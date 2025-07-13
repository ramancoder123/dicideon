from email_validator import validate_email as validate_email_lib, EmailNotValidError
import phonenumbers
import pandas as pd
import os
from auth import auth_utils
from utils import request_handler

def validate_email(email: str) -> bool:
    """
    Check if email is valid using a robust, industry-standard library.
    This is more reliable than a simple regular expression.
    """
    if not email:
        return False
    try:
        # The library checks for valid email format according to IETF standards.
        # We disable check_deliverability to avoid slow DNS lookups in the UI.
        validate_email_lib(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False

def validate_password(password: str) -> bool:
    """Check password requirements"""
    return len(password) >= 8 and any(c.isdigit() for c in password)

def validate_phone_number(phone_number: str, country_iso2: str) -> bool:
    """
    Validates a phone number against a specific country ISO code using the phonenumbers library.
    """
    if not phone_number or not country_iso2:
        return False
    try:
        parsed_number = phonenumbers.parse(phone_number, country_iso2)
        return phonenumbers.is_valid_number(parsed_number)
    except phonenumbers.phonenumberutil.NumberParseException:
        return False

def check_uniqueness(email: str, user_id: str, contact_number: str) -> tuple[list[str], dict[str, str]]:
    """
    Checks if email, user_id, or contact_number are already registered or pending.
    Returns a tuple: (list of error messages, dict of notifications to send {'field': 'original_email'}).
    """
    errors = []
    notifications = {}
    
    # 1. Load and prepare data sources
    try:
        users_df = auth_utils.load_users()
        # Standardize column name for comparison
        if 'username' in users_df.columns:
            users_df.rename(columns={'username': 'user_id'}, inplace=True)
    except FileNotFoundError:
        users_df = pd.DataFrame()

    try:
        if os.path.exists(request_handler.PENDING_REQUESTS_VALIDATION_FILE):
            validation_df = pd.read_csv(request_handler.PENDING_REQUESTS_VALIDATION_FILE)
            # Ensure contact_number is string for comparison
            if 'contact_number' in validation_df.columns:
                validation_df['contact_number'] = validation_df['contact_number'].astype(str)
        else:
            validation_df = pd.DataFrame()
    except (FileNotFoundError, pd.errors.EmptyDataError):
        validation_df = pd.DataFrame()

    # 2. Check for email uniqueness across both files
    is_email_duplicate = (not users_df.empty and 'email' in users_df.columns and email in users_df['email'].values) or \
                         (not validation_df.empty and 'email' in validation_df.columns and email in validation_df['email'].values)
    
    if is_email_duplicate:
        errors.append("This email address is already registered or pending approval.")
        # Add a notification to be sent to the original owner of the email.
        notifications['Email Address'] = email

    # 3. Check for user_id uniqueness
    if not users_df.empty and 'user_id' in users_df.columns and user_id in users_df['user_id'].values:
        original_email = users_df[users_df['user_id'] == user_id].iloc[0]['email']
        errors.append("This User ID is already registered or pending approval.")
        if original_email != email:
            notifications['User ID'] = original_email
    elif not validation_df.empty and 'user_id' in validation_df.columns and user_id in validation_df['user_id'].values:
        original_email = validation_df[validation_df['user_id'] == user_id].iloc[0]['email']
        errors.append("This User ID is already registered or pending approval.")
        if original_email != email:
            notifications['User ID'] = original_email

    # 4. Check for contact number uniqueness (only in validation file)
    if not validation_df.empty and 'contact_number' in validation_df.columns and contact_number in validation_df['contact_number'].values:
        original_email = validation_df[validation_df['contact_number'] == contact_number].iloc[0]['email']
        errors.append("This contact number is already registered or pending approval.")
        if original_email != email:
            notifications['Contact Number'] = original_email
        
    return list(set(errors)), notifications