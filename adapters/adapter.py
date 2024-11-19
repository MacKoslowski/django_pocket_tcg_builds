from allauth.account.adapter import DefaultAccountAdapter
from django.shortcuts import redirect
#from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class CustomAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False # No email/password signups allowed
    def get_signup_url(self, request):
        return redirect('account_login')
