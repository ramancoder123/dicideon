import pandas as pd
import os
from datetime import datetime, timedelta
import random
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.hashing import hash_password
from utils.exceptions import EmailConfigurationError, EmailSendingError

# --- Robust Path Definition ---
_current_dir = os.path.dirname(os.path.abspath(__file__))
_data_dir = os.path.join(os.path.dirname(_current_dir), "data")
PENDING_REQUESTS_FILE = os.path.join(_data_dir, "pending_requests.csv")
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

def _format_email_body(data):
    """Formats the sign-up data into a clean HTML email."""
    # Conditionally construct the full name to handle blank middle names gracefully.
    middle_name = data.get('middle_name')
    # pd.isna() is a robust way to check for pandas' NaN, which can occur with empty CSV fields.
    if middle_name and not pd.isna(middle_name):
        full_name = f"{data.get('first_name', '')} {middle_name} {data.get('last_name', '')}".strip()
    else:
        full_name = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; }}
            .container {{ padding: 20px; border: 1px solid #ddd; border-radius: 5px; max-width: 600px; }}
            h2 {{ color: #333; }}
            p {{ line-height: 1.6; }}
            strong {{ color: #555; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>New Dicideon Access Request</h2>
            <p>A new user has requested access. Please review their details below and update their status in the user management system.</p>
            <hr>
            <p><strong>Email:</strong> {data.get('email', 'N/A')}</p>
            <p><strong>Full Name:</strong> {full_name}</p>
            <p><strong>User ID:</strong> {data.get('user_id', 'N/A')}</p>
            <p><strong>Organization:</strong> {data.get('organization_name', 'N/A')}</p>
            <p><strong>Contact:</strong> {data.get('country_code', '')} {data.get('contact_number', '')}</p>
            <p><strong>Location:</strong> {data.get('city', 'N/A')}, {data.get('state', 'N/A')}, {data.get('country', 'N/A')}</p>
        </div>
    </body>
    </html>
    """
    return html

def _format_reset_email_body(reset_link):
    """Formats the password reset link into a clean HTML email."""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; }}
            .container {{ padding: 20px; border: 1px solid #ddd; border-radius: 5px; max-width: 600px; }}
            h2 {{ color: #333; }}
            p {{ line-height: 1.6; }}
            .button {{ background-color: #6C63FF; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Password Reset Request</h2>
            <p>You requested a password reset for your Dicideon account. Please click the button below to set a new password. This link is valid for one hour.</p>
            <p>If you did not request a password reset, you can safely ignore this email.</p>
            <br>
            <a href="{reset_link}" class="button" style="color: white;">Reset Password</a>
            <br><br>
            <p>If the button does not work, you can copy and paste this link into your browser:</p>
            <p><a href="{reset_link}">{reset_link}</a></p>
        </div>
    </body>
    </html>
    """
    return html

def _format_security_alert_email_body(attempted_field: str):
    """Formats a security alert email to notify a user of a sign-up attempt."""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; }}
            .container {{ padding: 20px; border: 1px solid #ddd; border-radius: 5px; max-width: 600px; }}
            h2 {{ color: #c0392b; }}
            p {{ line-height: 1.6; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Security Alert for Your Dicideon Account</h2>
            <p>We detected a recent attempt to create a new account using a <strong>{attempted_field}</strong> that is already associated with your email address.</p>
            <p>If this was you, please try logging in or use the 'Forgot Password' feature on the sign-in page. If this was not you, you can safely ignore this email. Your account remains secure.</p>
        </div>
    </body>
    </html>
    """
    return html

def _format_approval_email_body(first_name: str):
    """Formats the account approval email."""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; }}
            .container {{ padding: 20px; border: 1px solid #ddd; border-radius: 5px; max-width: 600px; }}
            h2 {{ color: #2ecc71; }}
            p {{ line-height: 1.6; }}
            .button {{ background-color: #6C63FF; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Welcome to Dicideon, {first_name}!</h2>
            <p>Your access request has been approved. You can now log in to your account using the credentials you provided during sign-up.</p>
            <br>
            <a href="http://localhost:8501" class="button" style="color: white;">Login Now</a>
        </div>
    </body>
    </html>
    """
    return html

def _format_rejection_email_body(first_name: str):
    """Formats the account rejection email."""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; }}
            .container {{ padding: 20px; border: 1px solid #ddd; border-radius: 5px; max-width: 600px; }}
            h2 {{ color: #e74c3c; }}
            p {{ line-height: 1.6; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Update on Your Dicideon Access Request</h2>
            <p>Hello {first_name},</p>
            <p>Thank you for your interest in Dicideon. After careful review, we are unable to approve your access request at this time. We appreciate your understanding.</p>
        </div>
    </body>
    </html>
    """
    return html

def send_password_reset_email(email: str, token: str):
    """Sends an email with a password reset link."""
    # In a real app, this base URL should come from a config file or environment variable.
    base_url = "http://localhost:8501"
    reset_link = f"{base_url}?token={token}"

    _send_email(email, "Dicideon Password Reset", _format_reset_email_body(reset_link))

def send_security_alert_email(recipient_email: str, attempted_field: str):
    """Sends a security alert notification to the original user."""
    subject = "Security Alert: Sign-Up Attempt on Your Dicideon Account"
    _send_email(recipient_email, subject, _format_security_alert_email_body(attempted_field))

def send_approval_email(recipient_email: str, first_name: str):
    """Sends an account approval notification to the user."""
    subject = "Your Dicideon Account Has Been Approved!"
    _send_email(recipient_email, subject, _format_approval_email_body(first_name))

def send_rejection_email(recipient_email: str, first_name: str):
    """Sends an account rejection notification to the user."""
    subject = "An Update on Your Dicideon Access Request"
    _send_email(recipient_email, subject, _format_rejection_email_body(first_name))

def _format_otp_email_body(otp):
    """Formats the OTP into a clean HTML email."""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; }}
            .container {{ padding: 20px; border: 1px solid #ddd; border-radius: 5px; max-width: 600px; }}
            h2 {{ color: #333; }}
            p {{ line-height: 1.6; }}
            .otp-code {{ font-size: 24px; font-weight: bold; color: #6C63FF; letter-spacing: 4px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Your Dicideon Verification Code</h2>
            <p>Thank you for signing up. Please use the following One-Time Password (OTP) to verify your email address. The code is valid for 10 minutes.</p>
            <p class="otp-code">{otp}</p>
            <p>If you did not request this, you can safely ignore this email.</p>
        </div>
    </body>
    </html>
    """
    return html

def send_otp_email(email: str, otp: str):
    """Sends an email with the sign-up OTP."""
    _send_email(email, "Your Dicideon Verification Code", _format_otp_email_body(otp))

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
    _send_email(ADMIN_EMAIL, f"New Dicideon Access Request from {email}", _format_email_body(record.to_dict()))
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
    except Exception as e:
        # This could be a network error, authentication error, etc.
        print(f"Email Error: {e}")
        raise EmailSendingError(f"An error occurred while trying to send the email.")