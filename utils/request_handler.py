import pandas as pd
import os
from datetime import datetime, timedelta
import random
import streamlit as st
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.hashing import hash_password
from utils.exceptions import EmailConfigurationError, EmailSendingError

# --- Logger Setup ---
logger = logging.getLogger(__name__)

# --- Robust Path Definition ---
_current_dir = os.path.dirname(os.path.abspath(__file__))
_data_dir = os.path.join(os.path.dirname(_current_dir), "data")
PENDING_REQUESTS_FILE = os.path.join(_data_dir, "pending_requests.csv")
TEMPLATES_DIR = os.path.join(_current_dir, "templates")
PENDING_REQUESTS_VALIDATION_FILE = os.path.join(_data_dir, "pending_requests_validation.csv")
USER_DATA_FILE = os.path.join(_data_dir, "user_data.csv")

ADMIN_EMAIL = "dicideonaccessmanage@gmail.com"

# Define columns as a constant to ensure consistency and reduce duplication.
_REQUEST_COLUMNS = [
    'request_timestamp', 'status', 'email', 'user_id', 'first_name',
    'middle_name', 'last_name', 'country_code', 'contact_number', 'date_of_birth', 
    'gender', 'organization_name', 'country', 'state', 'city', 
    'user_password', 'otp', 'otp_expires_at'
]

# Define columns for the final, approved user data file.
_USER_DATA_COLUMNS = [
    'email', 'user_id', 'first_name', 'middle_name', 'last_name', 
    'country_code', 'contact_number', 'date_of_birth', 'gender', 
    'organization_name', 'country', 'state', 'city', 'approval_timestamp'
]

def _create_csv_if_not_exists(file_path: str, columns: list):
    """Ensures a CSV file exists with the specified headers."""
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=columns)
        df.to_csv(file_path, index=False)

def _load_and_format_template(template_name: str, context: dict) -> str:
    """Loads an HTML template and replaces placeholders with context data."""
    template_path = os.path.join(TEMPLATES_DIR, template_name)
    try:
        with open(template_path, 'r') as f:
            template_str = f.read()
        for key, value in context.items():
            template_str = template_str.replace(f"{{{{{key}}}}}", str(value))
        return template_str
    except FileNotFoundError:
        logger.error(f"Email template not found at {template_path}")
        return f"<p>Error: Could not load email template '{template_name}'. Please contact support.</p>"

def _get_email_html(template_file: str, data: dict) -> str:
    """Prepares the context and formats a specific email template."""
    # Conditionally construct the full name to handle blank middle names gracefully.
    middle_name = data.get('middle_name')
    if middle_name and not pd.isna(middle_name):
        full_name = f"{data.get('first_name', '')} {middle_name} {data.get('last_name', '')}".strip()
    else:
        full_name = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
    
    context = {
        "email": data.get('email', 'N/A'),
        "full_name": full_name,
        "first_name": data.get('first_name', ''),
        "user_id": data.get('user_id', 'N/A'),
        "organization_name": data.get('organization_name', 'N/A'),
        "country_code": data.get('country_code', ''),
        "contact_number": data.get('contact_number', ''),
        "city": data.get('city', 'N/A'),
        "state": data.get('state', 'N/A'),
        "country": data.get('country', 'N/A'),
        "reset_link": data.get('reset_link', ''),
        "attempted_field": data.get('attempted_field', ''),
        "base_url": os.environ.get("BASE_URL", "http://localhost:8501"),
        "otp": data.get('otp', '')
    }
    return _load_and_format_template(template_file, context)

def send_password_reset_email(email: str, token: str):
    """Sends an email with a password reset link."""
    # The base URL must be configured for the deployment environment.
    base_url = os.environ.get("BASE_URL", "http://localhost:8501")
    reset_link = f"{base_url}?token={token}"
    html_body = _get_email_html("password_reset.html", {"reset_link": reset_link})
    _send_email(email, "Dicideon Password Reset", html_body)

def send_security_alert_email(recipient_email: str, attempted_field: str):
    """Sends a security alert notification to the original user."""
    subject = "Security Alert: Sign-Up Attempt on Your Dicideon Account"
    html_body = _get_email_html("security_alert.html", {"attempted_field": attempted_field})
    _send_email(recipient_email, subject, html_body)

def send_approval_email(recipient_email: str, first_name: str):
    """Sends an account approval notification to the user."""
    subject = "Your Dicideon Account Has Been Approved!"
    html_body = _get_email_html("approval.html", {"first_name": first_name})
    _send_email(recipient_email, subject, html_body)

def send_rejection_email(recipient_email: str, first_name: str):
    """Sends an account rejection notification to the user."""
    subject = "An Update on Your Dicideon Access Request"
    html_body = _get_email_html("rejection.html", {"first_name": first_name})
    _send_email(recipient_email, subject, html_body)

def send_corruption_notification_email(recipient_email: str, first_name: str):
    """Sends an email notifying the user of a corrupted request."""
    subject = "Action Required: Your Dicideon Sign-Up Request"
    html_body = _get_email_html("corrupted_request.html", {"first_name": first_name})
    _send_email(recipient_email, subject, html_body)

def send_otp_email(email: str, otp: str):
    """Sends an email with the sign-up OTP."""
    html_body = _get_email_html("otp.html", {"otp": otp})
    _send_email(email, "Your Dicideon Verification Code", html_body)

def initiate_signup_and_send_otp(form_data):
    """
    Saves the initial request with an OTP, sets status to 'awaiting_otp',
    and sends the OTP email. Returns the expiration datetime on success.
    """
    _create_csv_if_not_exists(PENDING_REQUESTS_FILE, _REQUEST_COLUMNS)
    
    # 1. Generate OTP and expiration
    otp = str(random.randint(100000, 999999))
    otp_expires_at = datetime.now() + timedelta(minutes=10)

    # 2. Prepare data for saving
    request_data = form_data.copy()
    request_data['request_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    request_data['status'] = 'awaiting_otp'
    request_data['user_password'] = hash_password(request_data.pop('password'))
    request_data['otp'] = otp
    request_data['otp_expires_at'] = otp_expires_at.strftime("%Y-%m-%d %H:%M:%S")

    # 3. Save to CSV, overwriting any previous attempt from the same email
    df = pd.read_csv(PENDING_REQUESTS_FILE)
    df = df[df['email'] != request_data['email']]
    new_request_df = pd.DataFrame([request_data])
    updated_df = pd.concat([df, new_request_df], ignore_index=True)
    
    # Enforce a clean schema to prevent saving junk columns like 'dob' or 'date_of_borth'
    updated_df = updated_df.reindex(columns=_REQUEST_COLUMNS)
    updated_df.to_csv(PENDING_REQUESTS_FILE, index=False)

    # 4. Send OTP email to the user
    send_otp_email(request_data['email'], otp)
    return otp_expires_at

def regenerate_and_resend_otp(email: str) -> datetime | None:
    """
    Finds an existing request, generates a new OTP, updates the record,
    and resends the email. Returns the new expiration time on success.
    """
    if not os.path.exists(PENDING_REQUESTS_FILE): return None
    
    df = pd.read_csv(PENDING_REQUESTS_FILE)
    request_row_series = df[(df['email'] == email) & (df['status'] == 'awaiting_otp')]
    
    if request_row_series.empty: return None
    
    request_index = request_row_series.index[0]
    
    # Generate new OTP and expiration
    new_otp = str(random.randint(100000, 999999))
    new_expires_at = datetime.now() + timedelta(minutes=10)
    
    # Update the DataFrame
    df.loc[request_index, 'otp'] = new_otp
    df.loc[request_index, 'otp_expires_at'] = new_expires_at.strftime("%Y-%m-%d %H:%M:%S")
    
    # Save the updated DataFrame and resend the email
    df.to_csv(PENDING_REQUESTS_FILE, index=False)
    send_otp_email(email, new_otp)
    return new_expires_at

def verify_otp_and_finalize_request(email: str, otp: str) -> bool:
    """
    Verifies the OTP. If correct, moves the request from the pending file
    to the validation file and notifies the admin.
    """
    if not os.path.exists(PENDING_REQUESTS_FILE): return False

    df = pd.read_csv(PENDING_REQUESTS_FILE)
    request_row = df[(df['email'] == email) & (df['status'] == 'awaiting_otp')]

    if request_row.empty: return False

    record = request_row.iloc[0].copy() # Use .copy() to avoid SettingWithCopyWarning
    expires_at = datetime.strptime(record['otp_expires_at'], "%Y-%m-%d %H:%M:%S")
    
    if str(record['otp']) != otp or datetime.now() > expires_at:
        return False

    # OTP is valid, so move the record from the temp file to the final validation file.
    # 1. Remove the record from the temporary pending file.
    request_index = request_row.index[0]
    df = df.drop(request_index)
    df.to_csv(PENDING_REQUESTS_FILE, index=False)

    # 2. Prepare the record for the final validation file.
    record['status'] = 'pending'
    record['otp'] = '' # Clear sensitive data.
    record['otp_expires_at'] = '' # Clear sensitive data.

    # 3. Add the verified record to the final validation file.
    _create_csv_if_not_exists(PENDING_REQUESTS_VALIDATION_FILE, _REQUEST_COLUMNS)
    validation_df = pd.read_csv(PENDING_REQUESTS_VALIDATION_FILE)
    updated_validation_df = pd.concat([validation_df, record.to_frame().T], ignore_index=True)
    # Reindex to ensure only the correct columns are saved, in the correct order.
    updated_validation_df = updated_validation_df.reindex(columns=_REQUEST_COLUMNS)
    updated_validation_df.to_csv(PENDING_REQUESTS_VALIDATION_FILE, index=False)

    # 4. Notify the admin about the newly verified request.
    html_body = _get_email_html("admin_notification.html", record.to_dict())
    _send_email(ADMIN_EMAIL, f"New Dicideon Access Request from {email}", html_body)
    return True

def _send_email(recipient_email, subject, html_body):
    """
    A generic function to send an HTML email.
    Raises EmailConfigurationError or EmailSendingError on failure.
    """
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")

    if not sender_email or not sender_password:
        # This is a server configuration issue, not a user error.
        logger.critical("Email service is not configured. SENDER_EMAIL or SENDER_PASSWORD secrets are missing.")
        raise EmailConfigurationError("Email service is not configured on the server.")

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        logger.info(f"Successfully sent email to {recipient_email} with subject: '{subject}'")
    except Exception as e:
        # Include the original exception message for better debugging.
        error_message = f"Failed to send email to {recipient_email} with subject '{subject}'. Error: {e}"
        logger.error(error_message)
        raise EmailSendingError(error_message)