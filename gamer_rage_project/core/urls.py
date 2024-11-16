from django.urls import path
from . import views
app_name = 'core'
urlpatterns = [
    path('', views.home, name='home'),
    path('decks/trending/', views.trending_decks, name='decks_trending'),
]
