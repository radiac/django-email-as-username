from django.conf import settings

# Whether or not to allow empty email addresses in the system
ALLOW_EMPTY = getattr(settings, 'EMAILUSERNAMES_ALLOW_EMPTY', False)

# The prefix used for generating unique usernames for users with an empty email
# Will be temporarily used on its own while saving a new user without email
EMPTY_PREFIX = getattr(settings, 'EMAILUSERNAMES_EMPTY_PREFIX', '-')
