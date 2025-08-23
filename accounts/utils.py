from rest_framework_simplejwt.tokens import RefreshToken,AccessToken
from datetime import timedelta

def generate_email_verification_token(user):
    """
    Generate a Refresh JWT token for email verification.
    Valid for 24 hours by default (configurable via SIMPLE_JWT).
    """
    token = AccessToken.for_user(user)
    token.set_exp(lifetime=timedelta(hours=24))
    token['email_verification'] = True    
    
    return str(token)