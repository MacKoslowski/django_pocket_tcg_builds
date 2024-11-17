from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Card, Deck, DeckCard, ColorTypes, DeckReaction, DeckVote
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db.models import Count, Sum

def home(request):
    # Example data for demonstration
    #trending_decks = Deck.objects.annotate(
    #    upvote_count=Count('upvotes')
    #).order_by('-upvote_count')[:6]
    decks = Deck.objects.all()#\
    return render(request, 'home.html', {
        'trending_decks': decks
    })

def trending_decks(request):
    decks = Deck.objects.all()#\
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

#@login_required
def create_deck(request):
    if request.method == 'POST':
        # Create the deck first
        deck = Deck.objects.create(
            user_title=request.POST.get('title'),
            user_description=request.POST.get('description'),
            color_1=request.POST.get('primary_color'),
            color_2=request.POST.get('secondary_color') or None,
            creator=request.user
        )
        # Redirect to deck building page
        return redirect('core:build_deck', deck_id=deck.deck_id)
    
    return render(request, 'create_deck.html', {
        'color_types': ColorTypes.choices
    })

def build_deck(request, deck_id):
    deck = get_object_or_404(Deck, deck_id=deck_id, creator=request.user)
    return render(request, 'build_deck.html', {
        'deck': deck
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
#@login_required
def search_cards(request):
    query = request.GET.get('search', '')
    cards = Card.objects.filter(title__icontains=query)[:10]
    html = render_to_string(
        '_card_search_results.html', 
        {'cards': cards},
        request=request
    )
    return HttpResponse(html)

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


#@login_required
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

#@login_required
def remove_card_from_deck(request, deck_id, card_id):
    if request.method == 'POST':
        DeckCard.objects.filter(deck_id=deck_id, card_id=card_id).delete()
        deck = Deck.objects.get(deck_id=deck_id)
        return render(request, '_deck_card_list.html', {'deck': deck})
    

#@login_required
def toggle_deck_visibility(request, deck_id):
    if request.method == 'POST':
        deck = get_object_or_404(Deck, deck_id=deck_id, creator=request.user)
        deck.public = not deck.public
        deck.save()
        return HttpResponse(status=200)
    return HttpResponse(status=405)

#@login_required
def delete_deck(request, deck_id):
    if request.method == 'DELETE':
        deck = get_object_or_404(Deck, deck_id=deck_id, creator=request.user)
        deck.delete()
        return HttpResponse(status=200)
    return HttpResponse(status=405)

@login_required
def toggle_deck_vote(request, deck_id):
    if request.method == 'POST':
        deck = get_object_or_404(Deck, deck_id=deck_id)
        vote_value = int(request.POST.get('value'))  # 1 or -1
        
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
        
        return JsonResponse({
            'vote_sum': vote_sum,
            'user_vote': vote_value if (created or vote.value == vote_value) else 0
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def toggle_deck_reaction(request, deck_id):
    if request.method == 'POST':
        deck = get_object_or_404(Deck, deck_id=deck_id)
        emoji = request.POST.get('emoji')
        
        # Validate emoji
        if emoji not in dict(DeckReaction.EMOJI_CHOICES):
            return JsonResponse({'error': 'Invalid emoji'}, status=400)
        
        reaction, created = DeckReaction.objects.get_or_create(
            deck=deck,
            user=request.user,
            emoji=emoji
        )
        
        if not created:
            # Remove reaction if already exists
            reaction.delete()
        
        # Get updated counts
        reactions = DeckReaction.objects.filter(deck=deck).values('emoji').annotate(
            count=Count('id')
        )
        
        return JsonResponse({
            'reactions': list(reactions),
            'user_reacted': created
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def deck_detail(request, deck_id):
    deck = get_object_or_404(Deck, deck_id=deck_id)
    
    # Get vote info
    vote_sum = deck.votes.aggregate(total=Sum('value'))['total'] or 0
    user_vote = deck.votes.filter(user=request.user).values_list('value', flat=True).first()
    
    # Get reaction info
    reactions = deck.reactions.values('emoji').annotate(count=Count('id'))
    reaction_counts = {r['emoji']: r['count'] for r in reactions}
    user_reactions = {r.emoji: True for r in deck.reactions.filter(user=request.user)}
    
    return render(request, 'deck_detail.html', {
        'deck': deck,
        'vote_sum': vote_sum,
        'user_vote': user_vote,
        'reaction_counts': reaction_counts,
        'user_reactions': user_reactions,
        'reaction_choices': DeckReaction.EMOJI_CHOICES,
})