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
    # ManyToMany relationship with Card through DeckCard
    cards = models.ManyToManyField(Card, through='DeckCard')
    
    def __str__(self):
        return self.user_title
    
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
        return f"{self.quantity}x {self.card.name} in {self.deck.title}"

    def clean(self):
        from django.core.exceptions import ValidationError
        # Enforce Pokemon TCG rules
        if self.quantity > 4 and self.card.card_type != 'Energy':
            raise ValidationError('You can only have 4 of the same card in a deck')

class Vote(models.Model):
    class Votes(models.TextChoices):
        UPVOTE = 'upvote', _('Update')
        DOWNVOTE = 'downvote', _('Downvote')
        
    vote_id = models.AutoField(primary_key=True)
    deck_id = models.IntegerField()
    user_id = models.IntegerField()
    vote_type = models.CharField(choices=Votes.choices, max_length=30)
    patch_id = models.IntegerField
    created_at = models.DateTimeField(auto_now_add=True)  # Set once when created

class Reaction(models.Model):
    react_id = models.AutoField(primary_key=True)
    deck_id = models.IntegerField()
    user_id = models.IntegerField()
    emoji = models.CharField(max_length=5)
    patch_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)  # Set once when created

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