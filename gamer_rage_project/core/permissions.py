# permissions.py
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Deck

def deck_owner_required(view_func):
   @wraps(view_func)
   def wrapper(request, deck_id, *args, **kwargs):
       deck = get_object_or_404(Deck, deck_id=deck_id)
       if deck.creator != request.user:
           raise PermissionDenied("You must be the deck owner to perform this action.")
       return view_func(request, deck_id, *args, **kwargs)
   return wrapper