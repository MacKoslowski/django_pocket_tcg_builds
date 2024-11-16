from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Card, Deck, DeckCard, ColorTypes
from django.template.loader import render_to_string

def home(request):
    # Example data for demonstration
    #trending_decks = Deck.objects.annotate(
    #    upvote_count=Count('upvotes')
    #).order_by('-upvote_count')[:6]
    
    return render(request, 'home.html', {
        'trending_decks': []
    })

def trending_decks(request):
    format = request.GET.get('format', 'standard')
    #decks = Deck.objects.filter(format=format)\
    #    .annotate(upvote_count=Count('upvotes'))\
    #    .order_by('-upvote_count')[:6]
    
    #return render(request, 'decks/_trending_decks.html', {
    #    'trending_decks': decks
    #})

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

#@login_required
def add_card_to_deck(request, deck_id):
    if request.method == 'POST':
        deck = Deck.objects.get(id=deck_id)
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
        deck = Deck.objects.get(id=deck_id)
        return render(request, '_deck_card_list.html', {'deck': deck})