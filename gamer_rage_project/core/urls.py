from django.urls import path
from . import views
app_name = 'core'
urlpatterns = [
    path('', views.home, name='home'),
    path('decks/trending/', views.trending_decks, name='decks_trending'),
    path('deck/create/', views.create_deck, name='create_deck'),
    path('deck/search/', views.search_cards, name='search_cards'),
    path('deck/<int:deck_id>/toggle-vis/', views.toggle_deck_visibility, name='toggle_deck_visibility'),
    path('deck/<int:deck_id>/delete_deck/', views.delete_deck, name='delete_deck'),
    path('deck/<int:deck_id>/add-card/', views.add_card_to_deck, name='add_card_to_deck'),
    path('deck/<int:deck_id>/vote/', views.toggle_deck_vote, name='toggle_deck_vote'),
    path('deck/<int:deck_id>/react/', views.toggle_deck_reaction, name='toggle_deck_reaction'),
    path('deck/<int:deck_id>/', views.deck_detail, name='deck_detail'),
    path('deck/update_second_color/', views.update_secondary_color, name='update_secondary_color'),
    path('<int:deck_id>/remove-card/<int:card_id>/', 
         views.remove_card_from_deck, 
         name='remove_card_from_deck'),
    path('deck/<int:deck_id>/build/', 
         views.build_deck, 
         name='build_deck'),
    path('deck_list/', 
         views.deck_list, 
         name='deck_list'),
     path('deck/<int:deck_id>/toggle-public/', views.toggle_deck_public, name='toggle_deck_public'),
          # ... existing urls ...
    
]
