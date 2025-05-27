import logging
from django.contrib.auth.models import User
from django.db.models import Value, CharField
from django.db.models.functions import Concat

logger = logging.getLogger(__name__)

def get_all_users():
    """
    Retrieves all users from Django auth_user table with ID and combined name.
    
    Returns:
        tuple: (users_list, error_message)
            - users_list: List of user objects with id and name fields or None if error
            - error_message: Error message or None if successful
    """
    try:
        users = User.objects.annotate(
            name=Concat('first_name', Value(' '), 'last_name', output_field=CharField())
        ).values('id', 'name').order_by('name')
        return users, None
    except Exception as e:
        logger.error(f"Error retrieving users: {e}")
        return None, str(e)

