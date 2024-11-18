from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class ColorTypes(models.TextChoices):
    GRASS = 'grass'
    FIRE = 'fire'
    WATER = 'water'
    LIGHTNING = 'lightning'
    FIGHTING = 'fighting'
    PSYCHIC = 'psychic'
    COLORLESS = 'colorless'
    DARKNESS = 'darkness'
    METAL = 'metal'
    DRAGON = 'dragon'
    FAIRY = 'fairy'

class CardTypes(models.TextChoices):
    ITEM = 'item'
    SUPPORTER = 'supporter'
    BASIC = 'basic'
    STAGE1 = 'stage_1'
    STAGE2 = 'stage_2'


class Card(models.Model):
    RARITY_ORDER = {
        '☆☆☆☆': 1,  # Adjust these values and names
        '☆☆☆': 2,   # to match your actual
        '☆☆': 3,     # rarity system
        '☆': 4,
        '◊◊◊◊': 5, 
        '◊◊◊': 6, 
        '◊◊': 7, 
        '◊': 8, 
        '': 9, 
    }
    card_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=45)
    hp = models.IntegerField()
    type = models.CharField(choices=CardTypes.choices, max_length=30)
    color = models.CharField(choices=ColorTypes.choices, max_length=30)
    number = models.IntegerField()
    rarity = models.CharField(max_length=30)
    pack = models.CharField(max_length=30)
    retreatCost = models.CharField(max_length=30)
    description = models.CharField(max_length=30)
    weakness_type = models.CharField(choices=ColorTypes.choices, max_length=30)
    weakness_dmg = models.IntegerField
    image_key = models.CharField(max_length=200)  # Store S3 key

    @property
    def image_url(self):
       return f'https://{settings.AWS_S3_CUSTOM_DOMAIN}/{self.image_key}'
    
    def __str__(self):
        return f"{self.title}"
    
class Energy(models.Model):
    name = models.CharField(max_length=50, unique=True)
    symbol = models.CharField(max_length=1)  # e.g., 'R' for Fire, 'W' for Water
    color_hex = models.CharField(max_length=7)  # e.g., '#FF0000' for Fire
    
    def __str__(self):
        return self.name

class EnergyCost(models.Model):
    energy = models.ForeignKey(Energy, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    ability = models.ForeignKey(
        'Ability',
        on_delete=models.CASCADE,
        related_name='energy_costs'
    )
    
    class Meta:
        unique_together = ['energy', 'ability']
    
    def __str__(self):
        return f"{self.quantity}{self.energy.symbol}"

class Ability(models.Model):
    class AbilityType(models.TextChoices):
        ATTACK = 'attack', 'Attack'
        ABILITY = 'ability', 'Ability'
        POKE_POWER = 'poke-power', 'Poké-Power'
        POKE_BODY = 'poke-body', 'Poké-Body'
    
    card = models.ForeignKey(
        Card,
        on_delete=models.CASCADE,
        related_name='abilities'
    )
    name = models.CharField(max_length=100)
    ability_type = models.CharField(
        max_length=20,
        choices=AbilityType.choices
    )
    description = models.TextField()
    damage = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="e.g., '20+', '150', 'None'"
    )
    
    class Meta:
        verbose_name_plural = 'abilities'
        ordering = ['card', 'ability_type']
        
    def __str__(self):
        return f"{self.name} ({self.get_ability_type_display()})"
    
    @property
    def formatted_energy_cost(self):
        costs = self.energy_costs.select_related('energy').order_by('energy__name')
        return ''.join(f"{cost.quantity}{cost.energy.symbol}" for cost in costs)
    
class Deck(models.Model):
    deck_id = models.AutoField(primary_key=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='decks'
    )
    user_title = models.CharField(max_length=30)
    user_description = models.CharField(max_length=200)
    color_1 = models.CharField(max_length=30,  choices=ColorTypes.choices)
    color_2 = models.CharField(max_length=30,  choices=ColorTypes.choices) 
    created_at = models.DateTimeField(auto_now_add=True)  # Set once when created
    public = models.BooleanField(default=False)
    modified_at = models.DateTimeField(auto_now=True)     # Updates on every save
    flagged = models.BooleanField(default=False)
    cover_card = models.ForeignKey(
        Card,
        on_delete=models.SET_NULL,  # If the card is deleted, don't delete the deck
        null=True,  # Allow deck to exist without cover card
        blank=True,  # Allow form submission without cover card
        related_name='cover_for_decks'  # Access decks where this card is the cover
    )
    # ManyToMany relationship with Card through DeckCard
    cards = models.ManyToManyField(Card, through='DeckCard')
    
    def __str__(self):
        return self.user_title
    
    def set_highest_rarity_cover(self):
        """Set the cover card to the highest rarity card in the deck"""
        highest_rarity_card = (
            self.deckcards.select_related('card')
            .exclude(card__type__in=['item', 'supporter'])  # Optionally exclude trainer cards
            .annotate(
                rarity_order=models.Case(
                    *[
                        models.When(card__rarity=rarity, then=models.Value(order))
                        for rarity, order in Card.RARITY_ORDER.items()
                    ],
                    default=models.Value(999),
                    output_field=models.IntegerField(),
                )
            )
            .order_by('rarity_order')  # Lower number = higher rarity
            .first()
        )

        if highest_rarity_card:
            self.cover_card = highest_rarity_card.card
            self.save(update_fields=['cover_card'])

    def save(self, *args, **kwargs):
        # First save to ensure we have an ID
        super().save(*args, **kwargs)
        
        # If no cover card is set, set it automatically
        if not self.cover_card:
            self.set_highest_rarity_cover()
        
    @property
    def card_count(self):
        return self.deckcards.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0

class DeckCard(models.Model):
    relation_id = models.AutoField(primary_key=True)
    deck = models.ForeignKey(
        Deck,
        on_delete=models.CASCADE,
        related_name='deckcards'
    )
    card = models.ForeignKey(
        Card,
        on_delete=models.CASCADE,
        related_name='deckcards'
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('deck', 'card')  # Prevent duplicate cards in deck
        
    def __str__(self):
        return f"{self.quantity}x {self.card.title} in {self.deck.user_title}"

    def clean(self):
        from django.core.exceptions import ValidationError
        # Enforce Pokemon TCG rules
        if self.quantity > 4 and self.card.card_type != 'Energy':
            raise ValidationError('You can only have 4 of the same card in a deck')
        
    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        # If this is a new card and it's rarer than the current cover,
        # update the deck's cover card
        if is_new and not self.deck.cover_card:
            self.deck.set_highest_rarity_cover()

# core/models.py
class DeckVote(models.Model):
    deck = models.ForeignKey(Deck, related_name='votes', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    value = models.SmallIntegerField(choices=[(-1, 'Downvote'), (1, 'Upvote')])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['deck', 'user']  # One vote per user per deck

class DeckReaction(models.Model):
    EMOJI_CHOICES = [
        ('⚡', 'Lightning'),
        ('🔥', 'Fire'),
        ('🌿', 'Leaf'),
        ('💧', 'Water'),
        ('⭐', 'Star'),
        ('✨', 'Sparkles'),
        ('💪', 'Strong'),
        ('🎯', 'Target'),
        ('❤️', 'Heart'),
        ('💔', 'Broken Heart'),
        ('🎲', 'Dice'),
        ('✅', 'Check Mark'),
        ('❌', 'Cross Mark'),
        ('🗑️', 'Trash'),
        ('👁️', 'Eye'),
        ('💫', 'Dizzy'),
        ('🛡️', 'Shield'),
        ('⚠️', 'Warning'),
    ]
    react_id = models.AutoField(primary_key=True)
    deck = models.ForeignKey(Deck, related_name='reactions', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=5, choices=EMOJI_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)  # Set once when created
    class Meta:
        unique_together = ['deck', 'user', 'emoji']  # One of each emoji per user per deck

class Patch(models.Model):
    patch_id = models.AutoField(primary_key=True)
    version = models.CharField(max_length=30)

class Report(models.Model):
    class ReportStatus(models.TextChoices):
        PENDING = 'pending', _('Pending Review')
        APPROVED = 'approved', _('Action Taken')
        REJECTED = 'rejected', _('No Action Needed')

    class ReportReason(models.TextChoices):
        INAPPROPRIATE = 'inappropriate', _('Inappropriate Content')
        OFFENSIVE = 'offensive', _('Offensive Language')
        SPAM = 'spam', _('Spam')
        OTHER = 'other', _('Other')

    # Core fields
    deck = models.ForeignKey(
        'Deck',
        on_delete=models.RESTRICT,
        related_name='reports'
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='submitted_reports'
    )
    reason = models.CharField(
        max_length=40,
        choices=ReportReason.choices,
        default=ReportReason.INAPPROPRIATE
    )
    details = models.TextField(
        help_text="Please provide specific details about the issue"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20,
        choices=ReportStatus.choices,
        default=ReportStatus.PENDING
    )
    

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report #{self.id} - {self.deck.title} ({self.status})"

    @property
    def is_pending(self):
        return self.status == self.ReportStatus.PENDING