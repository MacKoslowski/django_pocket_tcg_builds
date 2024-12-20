from django.urls import path
from . import views
#def trigger_error(request):
#    division_by_zero = 1 / 0
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
     path('deck/<int:deck_id>/report/', views.report_deck, name='report_deck'),
     path('decks/all/', views.all_decks, name='all_decks'),
     path('decks/all/results/', views.all_decks_results, name='all_decks_results'),
     path('terms/', views.terms, name='terms'),
     path('privacy/', views.privacy, name='privacy'),
     path('account_settings/', views.account_settings, name='account_settings'),
     path("ads.txt", views.ads_txt_view, name="ads_txt"),
     #path('sentry-debug/', trigger_error),

]

