# management/commands/update_card_image_keys.py
from django.core.management.base import BaseCommand
from core.models import Card

class Command(BaseCommand):
   help = 'Updates card image keys to match S3 structure'

   def handle(self, *args, **options):
       cards = Card.objects.all()
       for card in cards:
           # Assuming image key format: card_images/SET/SET_NUMBER_EN.webp
           set_code = 'A1' if card.number <= 287 else 'P-A'
           number = str(card.number).zfill(3)
           card.image_key = f'card_images/{set_code}/{set_code}_{number}_EN.webp'
           card.save(update_fields=['image_key'])
           
           self.stdout.write(
               self.style.SUCCESS(f'Updated {card.title} - {card.image_key}')
           )