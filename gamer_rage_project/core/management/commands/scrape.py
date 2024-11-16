# management/commands/scrape_cards.py
from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup
import time
from core.models import Card, ColorTypes, CardTypes, Ability
import re

class Command(BaseCommand):
    help = 'Scrapes Pokemon cards from limitlesstcg.com'

    def get_card_type(self, text):
        if 'Stage 2' in text:
            return CardTypes.STAGE2
        elif 'Stage 1' in text:
            return CardTypes.STAGE1
        elif 'Basic' in text:
            return CardTypes.BASIC
        elif 'Supporter' in text:
            return CardTypes.SUPPORTER
        elif 'Item' in text:
            return CardTypes.ITEM
        return CardTypes.BASIC

    def get_color_type(self, text):
        type_mapping = {
            'Grass': ColorTypes.GRASS,
            'Fire': ColorTypes.FIRE,
            'Water': ColorTypes.WATER,
            'Lightning': ColorTypes.LIGHTNING,
            'Fighting': ColorTypes.FIGHTING,
            'Psychic': ColorTypes.PSYCHIC,
            'Colorless': ColorTypes.COLORLESS,
            'Darkness': ColorTypes.DARKNESS,
            'Metal': ColorTypes.METAL,
            'Dragon': ColorTypes.DRAGON,
            'Fairy': ColorTypes.FAIRY,
        }
        return type_mapping.get(text, ColorTypes.COLORLESS)

    def extract_hp(self, hp_text):
        if hp_text:
            match = re.search(r'(\d+)\s*HP', hp_text)
            if match:
                return int(match.group(1))
        return 0

    def extract_retreat_cost(self, retreat_text):
        if retreat_text:
            match = re.search(r'Retreat:\s*(\d+)', retreat_text)
            if match:
                return int(match.group(1))
        return 0

    def extract_damage(self, attack_text):
        if attack_text:
            match = re.search(r'(\d+)(?:\+)?$', attack_text)
            if match:
                return match.group(0)
        return None

    def scrape_card(self, set_code, number):
        url = f"https://pocket.limitlesstcg.com/cards/{set_code}/{number}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            card_profile = soup.find('div', class_='card-profile')
            if not card_profile:
                return None

            card_text = card_profile.find('div', class_='card-text')
            if not card_text:
                return None

            # Basic card info
            title_section = card_text.find('p', class_='card-text-title')
            if not title_section:
                return None

            title = title_section.find('span', class_='card-text-name').text.strip()
            
            # Extract color and HP
            title_text = title_section.text.strip()
            color = None
            for type_name in ColorTypes.choices:
                if type_name[1].capitalize() in title_text:
                    color = type_name[0]
                    break

            hp = self.extract_hp(title_text)

            # Card type
            type_section = card_text.find('p', class_='card-text-type')
            card_type = self.get_card_type(type_section.text if type_section else '')

            # Weakness and retreat cost
            wrr_section = card_text.find('p', class_='card-text-wrr')
            weakness_type = None
            retreat_cost = 0
            
            if wrr_section:
                wrr_text = wrr_section.text.strip()
                for type_name in ColorTypes.choices:
                    if f"Weakness: {type_name[1].capitalize()}" in wrr_text:
                        weakness_type = type_name[0]
                        break
                retreat_cost = self.extract_retreat_cost(wrr_text)

            # Get pack info
            prints_section = soup.find('div', class_='card-prints')
            pack = prints_section.find('span', class_='text-lg').text.strip() if prints_section else ''
            
            # Get rarity
            rarity_cell = prints_section.find('td', string=lambda x: x and any(c in x for c in '◊★☆')) if prints_section else None
            rarity = rarity_cell.text.strip() if rarity_cell else ''

            # Create and save the card first
            card = Card.objects.create(
                title=title,
                color=color or ColorTypes.COLORLESS,
                hp=hp,
                type=card_type,
                number=number,
                rarity=rarity,
                pack=pack,
                retreatCost=str(retreat_cost),
                description='',
                weakness_type=weakness_type or ColorTypes.COLORLESS,
            )

            # Now handle abilities and attacks
            for ability_div in card_text.find_all(['div', 'card-text-attack', 'card-text-ability']):
                if 'card-text-ability' in ability_div.get('class', []):
                    # Handle Pokemon ability
                    ability_info = ability_div.find('p', class_='card-text-ability-info')
                    ability_effect = ability_div.find('p', class_='card-text-ability-effect')
                    
                    if ability_info:
                        name = ability_info.text.replace('Ability:', '').strip()
                        Ability.objects.create(
                            card=card,
                            name=name,
                            ability_type=Ability.AbilityType.ABILITY,
                            description=ability_effect.text.strip() if ability_effect else ''
                        )
                
                elif 'card-text-attack' in ability_div.get('class', []):
                    # Handle attack
                    attack_info = ability_div.find('p', class_='card-text-attack-info')
                    attack_effect = ability_div.find('p', class_='card-text-attack-effect')
                    
                    if attack_info:
                        attack_text = attack_info.text.strip()
                        name = attack_text.split('\n')[-1].strip()
                        damage = self.extract_damage(attack_text)
                        
                        Ability.objects.create(
                            card=card,
                            name=name,
                            ability_type=Ability.AbilityType.ATTACK,
                            description=attack_effect.text.strip() if attack_effect else '',
                            damage=damage
                        )

            return card

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error scraping card {set_code}/{number}: {str(e)}'))
            return None

    def handle(self, *args, **options):
        # Scrape A1 cards
        self.stdout.write('Scraping A1 cards...')
        for number in range(1, 287):
            card = self.scrape_card('A1', number)
            if card:
                self.stdout.write(self.style.SUCCESS(f'Successfully scraped A1/{number} - {card.title}'))
            time.sleep(1)

        # Scrape P-A cards
        self.stdout.write('Scraping P-A cards...')
        for number in range(1, 24):
            card = self.scrape_card('P-A', number)
            if card:
                self.stdout.write(self.style.SUCCESS(f'Successfully scraped P-A/{number} - {card.title}'))
            time.sleep(1)

        self.stdout.write(self.style.SUCCESS('Card scraping completed!'))