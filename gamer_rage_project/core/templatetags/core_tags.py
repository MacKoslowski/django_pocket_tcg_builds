# core/templatetags/core_tags.py
from django import template
from django.db.models import Count
from allauth.socialaccount.models import SocialAccount
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

@register.simple_tag
def get_discord_data(user):
    try:
        discord_account = SocialAccount.objects.filter(
            user=user, 
            provider='discord'
        ).first()
        if discord_account:
            return {
                'avatar': discord_account.extra_data.get('avatar'),
                'uid': discord_account.uid,
                'discriminator': discord_account.extra_data.get('discriminator'),
            }
    except:
        pass
    return None