# core/templatetags/core_tags.py
from django import template
from django.db.models import Count
from allauth.socialaccount.models import SocialAccount
from django.urls import reverse
register = template.Library()

@register.inclusion_tag('card_display.html')
def render_card(card, show_add_button=False, deck=None):
    
    return {
        'card': card,
        'show_add_button': show_add_button,
        'deck': deck
    }

@register.inclusion_tag('deck_display.html')
def render_deck(deck, show_edit_button=False, show_full_reactions=False):
    # Get top 3 reactions here instead of in template
    top_reactions = deck.reactions.values('emoji').annotate(
        count=Count('emoji')
    ).order_by('-count')[:3]

    return {
        'deck': deck,
        'show_edit_button': show_edit_button,
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

@register.filter
def lookup(dictionary, key):
    return dictionary.get(key)

@register.simple_tag
def login_or_url(url_name, *args):
    """Returns login URL if user isn't authenticated, otherwise returns named URL"""
    if args:
        return reverse(url_name, args=args)
    return reverse(url_name)

@register.simple_tag(takes_context=True)
def get_redirect_url(context, url_name, *args):
    """Get URL with a next parameter for post-login redirect"""
    target_url = reverse(url_name, args=args)
    if not context['user'].is_authenticated:
        return f"/accounts/discord/login/?process=login&next={target_url}"
    return target_url