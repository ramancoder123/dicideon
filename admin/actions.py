import pandas as pd
import os
from datetime import datetime
from utils import request_handler
from auth import auth_utils

def get_pending_requests():
    """Loads all requests from the pending validation file."""
    if os.path.exists(request_handler.PENDING_REQUESTS_VALIDATION_FILE):
        try:
            # Use a dtype to prevent pandas from misinterpreting numeric columns
            return pd.read_csv(request_handler.PENDING_REQUESTS_VALIDATION_FILE, dtype={'contact_number': str})
        except pd.errors.EmptyDataError:
            return pd.DataFrame()
    return pd.DataFrame()

def _save_validation_requests(df):
    """Saves the updated dataframe to the validation file."""
    df.to_csv(request_handler.PENDING_REQUESTS_VALIDATION_FILE, index=False)

def _get_request_by_email(request_email: str) -> tuple[pd.DataFrame, pd.Series | None]:
    """Helper to fetch a request and its data by email from the validation file."""
    validation_df = get_pending_requests()
    request_data = validation_df[validation_df['email'] == request_email]
    if request_data.empty:
        return validation_df, None
    return validation_df, request_data.iloc[0].copy()

def approve_request(request_email: str):
    """Approves a user request, moving them to the main users file and saving their full profile."""
    validation_df, user_info = _get_request_by_email(request_email)
    if user_info is None:
        return False, "Request not found."
    
    try:
        # 1. Add the user with their pre-hashed password to the main users file for authentication
        auth_utils.add_approved_user(
            email=user_info['email'], username=user_info['user_id'],
            hashed_password=user_info['user_password']
        )
    except ValueError as e:
        return False, str(e) # Handle case where user might already exist
    
    # 2. Save the full, cleaned user profile to the main user data file
    _save_full_user_profile(user_info)

    # 3. Remove from pending validation and send approval email
    validation_df = validation_df[validation_df['email'] != request_email]
    _save_validation_requests(validation_df)
    request_handler.send_approval_email(user_info['email'], user_info['first_name'])
    
    return True, f"User {user_info['email']} approved and notified."

def _save_full_user_profile(user_info: pd.Series):
    """Reads, updates, and overwrites the user_data.csv file to ensure data integrity."""
    file_path = request_handler.USER_DATA_FILE
    columns = request_handler._USER_DATA_COLUMNS
    request_handler._create_csv_if_not_exists(file_path, columns)

    # Prepare the new record for the final user data file
    profile_data = user_info.to_frame().T
    profile_data['approval_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Read the existing data, append the new profile, and save, ensuring the header is always correct.
    # This is safer than using mode='a'.
    existing_data = pd.read_csv(file_path)
    updated_data = pd.concat([existing_data, profile_data], ignore_index=True)
    updated_data = updated_data.reindex(columns=columns) # Ensure column order is always correct
    updated_data.to_csv(file_path, index=False)

def reject_request(request_email: str):
    """Rejects a user request, removing them from the pending file."""
    validation_df, user_info = _get_request_by_email(request_email)
    if user_info is None:
        return False, "Request not found."

    # Remove from pending validation and send rejection email
    validation_df = validation_df[validation_df['email'] != request_email]
    _save_validation_requests(validation_df)
    request_handler.send_rejection_email(user_info['email'], user_info['first_name'])
    
    return True, f"User {user_info['email']} rejected and notified."

def handle_corrupted_request(request_email: str):
    """
    Deletes a corrupted request from the validation file and notifies the user.
    A "corrupted" request here is one that the dashboard identified as having an invalid format.
    """
    validation_df, request_data_series = _get_request_by_email(request_email)
    if request_data_series is None:
        return False, f"Corrupted request for {request_email} not found in validation file (might have been processed already)."
    
    # Get user's first name for the email before dropping the data
    first_name = request_data_series.get('first_name', 'there') # Fallback name

    # Remove ALL entries for this email to clean up potential duplicates
    validation_df = validation_df[validation_df['email'] != request_email]
    _save_validation_requests(validation_df)
    
    # Notify the user to sign up again
    request_handler.send_corruption_notification_email(request_email, first_name)
    return True, f"Removed corrupted request for {request_email} and notified the user."