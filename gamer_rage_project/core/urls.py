from django.urls import path
from . import views
app_name = 'core'
urlpatterns = [
    path('', views.home, name='home'),
    path('decks/trending/', views.trending_decks, name='decks_trending'),
    path('deck/create/', views.create_deck, name='create_deck'),
    path('deck/search/', views.search_cards, name='search_cards'),
    path('deck/<int:deck_id>/add-card/', views.add_card_to_deck, name='add_card_to_deck'),
    path('deck/<int:deck_id>/add-card/', views.add_card_to_deck, name='add_card_to_deck'),
     path('<int:deck_id>/remove-card/<int:card_id>/', 
         views.remove_card_from_deck, 
         name='remove_card_from_deck'),
    path('update-secondary-color/', 
         views.update_secondary_color, 
         name='update_secondary_color'),
]
