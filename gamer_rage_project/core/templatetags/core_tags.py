# core/templatetags/core_tags.py
from django import template
from django.db.models import Count

register = template.Library()

@register.inclusion_tag('card_display.html')
def render_card(card, show_add_button=False, deck=None):
    print(card, show_add_button, deck)
    return {
        'card': card,
        'show_add_button': show_add_button,
        'deck': deck
    }

@register.inclusion_tag('deck_display.html')
def render_deck(deck, show_full_reactions=False):
    # Get top 3 reactions here instead of in template
    top_reactions = deck.reactions.values('emoji').annotate(
        count=Count('emoji')
    ).order_by('-count')[:3]

    return {
        'deck': deck,
        'show_full_reactions': show_full_reactions,
        'top_reactions': top_reactions
    }