from django.shortcuts import render
from django.contrib.auth.decorators import login_required

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