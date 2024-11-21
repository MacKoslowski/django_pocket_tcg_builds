from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from functools import wraps
from django.db.models import Count

def rate_limit(key_prefix, limit=10, period=60):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            cache_key = f"rate_limit:{key_prefix}:{request.user.id}"
            count = cache.get(cache_key, 0)
            
            if count >= limit:
                raise PermissionDenied("Rate limit exceeded")
            
            cache.set(cache_key, count + 1, period)
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator