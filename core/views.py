from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Card, Deck, DeckCard, ColorTypes, DeckReaction, DeckVote, Report
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from openai import OpenAI
from django.contrib import messages
from .permissions import deck_owner_required
from django.conf import settings
from django.core.paginator import Paginator
import json
from django.contrib.auth import logout
from .rate_limit import rate_limit
from datetime import date

@login_required
def account_settings(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # if action == 'update_name':
        #     new_name = request.POST.get('display_name')
        #     if new_name and not User.objects.filter(display_name=new_name).exists():
        #         request.user.display_name = new_name
        #         request.user.save()
        #         messages.success(request, 'Display name updated successfully!')
        #     else:
        #         messages.error(request, 'That name is already taken.')
                
        if action == 'delete_account':
            # Delete user content
            request.user.decks.all().delete()
            DeckVote.objects.filter(user_id=request.user.id).delete()
            # Delete user
            request.user.delete()
            logout(request)
            messages.success(request, 'Your account has been deleted.')
            return redirect('core:home')
            
    return render(request, 'account_settings.html')

def terms(request):
    return render(request, 'term_of_service.html', {
        'today': date.today()
    })

def privacy(request):
    return render(request, 'privacy_policy.html', {
        'today': date.today(),
        'using_analytics': False  # Change if using analytics
    })

def all_decks(request):
    # Regular request shows full page
    context = get_decks_context(request)  # Helper function for shared logic
    return render(request, 'all_decks.html', context)

def all_decks_results(request):
    # HTMX request only returns results partial
    context = get_decks_context(request)
    return render(request, '_all_deck_results.html', context)

def get_decks_context(request):
    # Shared logic for both views
    decks = Deck.objects.filter(public=True).select_related('creator')
    
    search_query = request.GET.get('search', '')
    card_search = request.GET.get('card', '')
    deck_type = request.GET.get('type', '')
    sort_by = request.GET.get('sort', '-created_at')

    if search_query:
        decks = decks.filter(
            Q(user_title__icontains=search_query) |
            Q(user_description__icontains=search_query)
        )

    if card_search:
        decks = decks.filter(cards__title__icontains=card_search).distinct()

    if deck_type:
        decks = decks.filter(Q(color_1=deck_type) | Q(color_2=deck_type))

    # Sorting
    if sort_by == 'votes':
        decks = decks.annotate(vote_count=Sum('votes__value')).order_by('-vote_count')
    elif sort_by == 'recent':
        decks = decks.order_by('-created_at')
    elif sort_by == 'popular':
        decks = decks.annotate(
            total_reactions=Count('reactions'),
            vote_count=Sum('votes__value')
        ).order_by('-total_reactions', '-vote_count')

    # Pagination
    paginator = Paginator(decks, 12)  # 12 decks per page
    page = request.GET.get('page')
    decks = paginator.get_page(page)

    return {
        'decks': decks,
        'search_query': search_query,
        'card_search': card_search,
        'deck_type': deck_type,
        'sort_by': sort_by,
        'color_types': ColorTypes.choices,
    }

def home(request):
    # Example data for demonstration
    #trending_decks = Deck.objects.annotate(
    #    upvote_count=Count('upvotes')
    #).order_by('-upvote_count')[:6]
    decks = Deck.objects.filter(public=1)
    return render(request, 'home.html', {
        'trending_decks': decks
    })

def trending_decks(request):
    decks = Deck.objects.filter(public=1)#\
        #.annotate(upvote_count=sum('upvotes'))\
        #.order_by('-upvote_count')[:6]
    
    return render(request, '_trending_decks.html', {
        'trending_decks': decks
    })

def deck_list(request):
    decks = Deck.objects.filter(
        creator=request.user
    ).order_by('-modified_at')  # Most recently modified first
    
    return render(request, 'deck_list.html', {
        'decks': decks
    })

@login_required
@deck_owner_required
def toggle_deck_public(request, deck_id):
    if request.method == 'POST':
        deck = get_object_or_404(Deck, deck_id=deck_id, creator=request.user)
        deck.public = not deck.public
        deck.save()
        return HttpResponse(status=200)
    return HttpResponse(status=405)


@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        # Delete user's content
        user.decks.all().delete()
        user.submitted_reports.all().delete()
        user.votes.all().delete()
        # Delete the user
        user.delete()
        logout(request)
        messages.success(request, 'Your account has been deleted.')
        return redirect('home')
    return render(request, 'account/delete_confirmation.html')

@login_required
@rate_limit('create_deck', limit=5, period=3600)  # 5 decks per hour
def create_deck(request):
   if request.method == 'POST':
       title = request.POST.get('title')
       description = request.POST.get('description')

        # Check content with OpenAI moderation
        #    try:
        #        input = f"title:{title}, description:{description}"
        #        print(input)
        #        client = OpenAI(api_key = settings.OPENAI_API_KEY)
        #        moderation = client.moderations.create(
        #            input=input
        #        )
        #        print(moderation.results[0])
        #        if moderation.results[0].flagged:
        #            return JsonResponse({
        #                'error': 'Content contains inappropriate language'
        #            }, status=400)

        #    except Exception as e:
        #        # Log the error but allow creation to continue
        #        print(f"Moderation API error: {str(e)}")

       deck = Deck.objects.create(
           user_title=title,
           user_description=description,
           color_1=request.POST.get('primary_color'),
           color_2=request.POST.get('secondary_color') or None,
           creator=request.user
       )
       return redirect('core:build_deck', deck_id=deck.deck_id)
  
   return render(request, 'create_deck.html', {
       'color_types': ColorTypes.choices
   })

@login_required
@deck_owner_required
def build_deck(request, deck_id):
    deck = get_object_or_404(Deck, deck_id=deck_id)
    
    cards_data = [{
        'card_id': card.card_id,
        'title': card.title,
        'type': card.type,
        'color': card.color,
        'hp': card.hp,
        'image_url': card.image_url
    } for card in Card.objects.all()]
    
    return render(request, 'edit_deck.html', {
        'deck': deck,
        'cards_json': json.dumps(cards_data)
    })

def update_secondary_color(request):
    """HTMX endpoint to update secondary color options"""
    primary_color = request.GET.get('primary_color')
    color_types = [
        (value, label) 
        for value, label in ColorTypes.choices 
        if value != primary_color
    ]
    
    return render(request, '_secondary_color_options.html', {
        'color_types': color_types
    })


def search_cards(request):
    query = request.GET.get('search', '')
    deck_id = request.GET.get('deck_id')  # This will be None if not provided
    
    cards = Card.objects.filter(title__icontains=query)[:10]
    
    # If deck_id is provided, get the deck
    deck = None
    if deck_id:
        try:
            deck = Deck.objects.get(deck_id=deck_id)
        except Deck.DoesNotExist:
            pass
    
    return render(request, '_card_search_results.html', {
        'cards': cards,
        'deck': deck  # Pass the deck object (or None) to the template
    })


@login_required
@deck_owner_required
def add_card_to_deck(request, deck_id):
    if request.method == 'POST':
        deck = Deck.objects.get(deck_id=deck_id)
        card_id = request.POST.get('card_id')
        quantity = int(request.POST.get('quantity', 1))
        
        deck_card, created = DeckCard.objects.get_or_create(
            deck=deck,
            card_id=card_id,
            defaults={'quantity': quantity}
        )
        if not created:
            deck_card.quantity += quantity
            deck_card.save()
            
        return render(request, '_deck_card_list.html', {'deck': deck})

@login_required
@deck_owner_required
def remove_card_from_deck(request, deck_id, card_id):
    if request.method == 'POST':
        DeckCard.objects.filter(deck_id=deck_id, card_id=card_id).delete()
        deck = Deck.objects.get(deck_id=deck_id)
        return render(request, '_deck_card_list.html', {'deck': deck})
    

@login_required
@deck_owner_required
def toggle_deck_visibility(request, deck_id):
    if request.method == 'POST':
        deck = get_object_or_404(Deck, deck_id=deck_id, creator=request.user)
        deck.public = not deck.public
        deck.save()
        return HttpResponse(status=200)
    return HttpResponse(status=405)

@login_required
@deck_owner_required
def delete_deck(request, deck_id):
    if request.method == 'DELETE':
        deck = get_object_or_404(Deck, deck_id=deck_id, creator=request.user)
        deck.delete()
        return HttpResponse(status=200)
    return HttpResponse(status=405)

@login_required
@rate_limit('vote', limit=30, period=60)  # 30 votes per minute
def toggle_deck_vote(request, deck_id):
    deck = get_object_or_404(Deck, deck_id=deck_id)
    if request.method == 'POST':
        vote_type = request.POST.get('vote_type')
        vote_value = 0
        if vote_type == 'up':
            vote_value = 1
        elif vote_type == 'down':
            vote_value = -1
        else:
            return HttpResponse(status=400)
        
        vote, created = DeckVote.objects.get_or_create(
            deck=deck,
            user=request.user,
            defaults={'value': vote_value}
        )
        
        if not created:
            if vote.value == vote_value:
                # Remove vote if clicking same button
                vote.delete()
            else:
                # Change vote if clicking different button
                vote.value = vote_value
                vote.save()
        
        # Get updated counts
        vote_sum = deck.votes.aggregate(total=Sum('value'))['total'] or 0
        user_reaction = DeckReaction.objects.filter(deck=deck,
            user=request.user).first()
            
        reactions = DeckReaction.objects.filter(deck=deck).values('emoji').annotate(
            count=Count('deck_id')
        )
        reaction_counts = {r['emoji']: r['count'] for r in reactions}
        return render(request, '_deck_vote.html', {
            'deck': deck,
            'vote_sum': vote_sum,
            'user_vote': vote_value if (created or vote.value == vote_value) else 0,
            'reactions': list(reactions),
            'user_reaction': user_reaction,
            'reaction_counts': reaction_counts,
            'reaction_choices': DeckReaction.EMOJI_CHOICES,
        })
    
    elif request.methd == 'GET':
        vote = DeckVote.objects.filter(deck=deck,
            user=request.user).first()
            
        vote_sum = deck.votes.aggregate(total=Sum('value'))['total'] or 0
        return render(request, '_deck_vote.html', {
            'deck': deck,
            'vote_sum': vote_sum,
            'user_vote': vote.value
        })

@login_required
@rate_limit('vote', limit=30, period=60)  # 30 votes per minute
def toggle_deck_reaction(request, deck_id):
    if request.method == 'POST':
        deck = get_object_or_404(Deck, deck_id=deck_id)
        emoji = request.POST.get('emoji')
        
        # Validate emoji
        if emoji not in dict(DeckReaction.EMOJI_CHOICES):
            return JsonResponse({'error': 'Invalid emoji'}, status=400)
        
        # Get existing reaction for this user/deck if any
        existing_reaction = DeckReaction.objects.filter(
            deck=deck,
            user=request.user
        ).first()

        if existing_reaction:
            if existing_reaction.emoji == emoji:
                # Remove if same emoji clicked
                existing_reaction.delete()
                user_reaction = None
            else:
                # Update to new emoji
                existing_reaction.emoji = emoji
                existing_reaction.save()
                user_reaction = existing_reaction
        else:
            # Create new reaction
            user_reaction = DeckReaction.objects.create(
                deck=deck,
                user=request.user,
                emoji=emoji
            )

        # Get updated counts
        reactions = DeckReaction.objects.filter(deck=deck).values('emoji').annotate(
            count=Count('deck_id')
        )
        reaction_counts = {r['emoji']: r['count'] for r in reactions}
        return render(request, '_deck_reactions.html', {
            'reactions': list(reactions),
            'user_reaction': user_reaction,
            'reaction_counts': reaction_counts,
            'reaction_choices': DeckReaction.EMOJI_CHOICES,
            'deck': deck
        })

    return HttpResponse(status=405)
    
    
def deck_detail(request, deck_id):
    deck = get_object_or_404(Deck, deck_id=deck_id)
    
    # Get all cards in deck with quantities
    deck_cards = deck.deckcards.select_related('card').all()
    
    # Get vote information
    vote_count = deck.votes.aggregate(total=Sum('value'))['total'] or 0
    user_vote = None
    user_reaction = None
    if request.user.is_authenticated:
        user_vote = deck.votes.filter(user=request.user).first()
        user_reaction = DeckReaction.objects.filter(deck=deck,
             user=request.user).first()
     # Get reaction info
    reactions = deck.reactions.values('emoji').annotate(count=Count('deck_id'))
    reaction_counts = {r['emoji']: r['count'] for r in reactions}
    
    
    context = {
        'deck': deck,
        'deck_cards': deck_cards,
        'vote_sum': vote_count,
        'user_vote': user_vote.value if user_vote else None,
        'reaction_counts': reaction_counts,
        'user_reactions': user_reaction,
        'reaction_choices': DeckReaction.EMOJI_CHOICES,
         'report_reasons': Report.ReportReason.choices,
    }
    
    return render(request, 'deck_detail.html', context)


@login_required
def report_deck(request, deck_id):
    if request.method == 'POST':
        deck = get_object_or_404(Deck, deck_id=deck_id)
        
        # Don't allow reporting your own deck
        #if deck.creator == request.user:
        #    return HttpResponse(status=403)
            
        # Check if user already reported this deck
        if Report.objects.filter(deck=deck, reporter=request.user, status=Report.ReportStatus.PENDING).exists():
            messages.warning(request, 'You have already reported this deck')
            return HttpResponse(status=400)
            
        Report.objects.create(
            deck=deck,
            reporter=request.user,
            reason=request.POST.get('reason'),
            details=request.POST.get('details')
        )
        deck.public = 0
        deck.save()
        
        messages.success(request, 'Thank you for your report. Our moderators will review it.')
        return HttpResponse(status=200)
        
    return HttpResponse(status=405)

def custom_permission_denied(request, exception):
    return render(request, '403.html', status=403)