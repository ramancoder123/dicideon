import os
import sys
from datetime import datetime
from utils import request_handler
from auth import auth_utils

# --- Path Setup ---
_current_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_current_dir)
sys.path.append(_root_dir)
import database

def get_pending_requests():
    """
    Loads all requests with status 'pending_approval' from the database.
    Returns a list of dictionaries.
    """
    return database.get_all_pending_requests()

def approve_request(request_email: str):
    """Approves a user request, creating their user account and updating their status."""
    user_info = database.get_request_by_email(request_email)
    if user_info is None:
        return False, "Request not found."

    try:
        # 1. Add the user to the 'users' table for authentication.
        auth_utils.add_approved_user(
            email=user_info['email'], username=user_info['user_id'], hashed_password=user_info['user_password'], phone_code=user_info['country_code'], contact_number=user_info['contact_number'], country=user_info['country'],
            state=user_info['state'], city=user_info['city'], organization_name=user_info['organization_name'], gender=user_info['gender']
        )

        # 2. Update the request status to 'approved'
        database.update_request_status(request_email, 'approved')

        # 3. Send approval email
        request_handler.send_approval_email(user_info['email'], user_info['first_name'])

    except ValueError as e:
        return False, str(e) # Handle case where user might already exist
    except Exception as e:
        return False, f"An unexpected error occurred: {e}"

    return True, f"User {user_info['email']} approved and notified."

def reject_request(request_email: str):
    """Rejects a user request, updating their status in the database."""
    user_info = database.get_request_by_email(request_email)
    if user_info is None:
        return False, "Request not found."

    try:
        # Update status and send rejection email
        database.update_request_status(request_email, 'rejected')
        request_handler.send_rejection_email(user_info['email'], user_info['first_name'])
        return True, f"User {user_info['email']} rejected and notified."
    except Exception as e:
        return False, f"An unexpected error occurred during rejection: {e}"

def handle_corrupted_request(request_email: str):
    """
    Deletes a corrupted request from the validation file and notifies the user.
    A "corrupted" request here is one that the dashboard identified as having an invalid format.
    """
    # This function's logic will need to be re-evaluated.
    # With a database, data corruption is much less likely.
    # For now, we'll implement it as a deletion.
    request_data = database.get_request_by_email(request_email)
    if request_data is None:
        return False, f"Request for {request_email} not found (might have been processed already)."

    first_name = request_data.get('first_name', 'there')

    try:
        # A "corrupted" request will be treated as rejected.
        database.update_request_status(request_email, 'rejected')
        request_handler.send_corruption_notification_email(request_email, first_name)
        return True, f"Handled corrupted-state request for {request_email} and notified the user."
    except Exception as e:
        return False, f"An unexpected error occurred while handling corrupted request: {e}"