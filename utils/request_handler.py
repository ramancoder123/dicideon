import pandas as pd
import os
from datetime import datetime
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.hashing import hash_password

# --- Robust Path Definition ---
_current_dir = os.path.dirname(os.path.abspath(__file__))
_data_dir = os.path.join(os.path.dirname(_current_dir), "data")
PENDING_REQUESTS_FILE = os.path.join(_data_dir, "pending_requests.xlsx")

ADMIN_EMAIL = "dicideonaccessmanage@gmail.com"

def _create_pending_requests_file_if_not_exists():
    """Ensures the Excel file exists with the correct headers."""
    if not os.path.exists(PENDING_REQUESTS_FILE):
        df = pd.DataFrame(columns=[
            'request_timestamp', 'status', 'email', 'user_id', 'first_name',
            'middle_name', 'last_name', 'country_code', 'contact_number',
            'date_of_birth', 'gender', 'organization_name', 'country',
            'state', 'city', 'user_password'
        ])
        df.to_excel(PENDING_REQUESTS_FILE, index=False)

def _format_email_body(data):
    """Formats the sign-up data into a clean HTML email."""
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
            <p><strong>Email:</strong> {data['email']}</p>
            <p><strong>Full Name:</strong> {data['first_name']} {data['middle_name']} {data['last_name']}</p>
            <p><strong>User ID:</strong> {data['user_id']}</p>
            <p><strong>Organization:</strong> {data['organization_name']}</p>
            <p><strong>Contact:</strong> {data['country_code']} {data['contact_number']}</p>
            <p><strong>Location:</strong> {data['city']}, {data['state']}, {data['country']}</p>
        </div>
    </body>
    /html>
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

def send_password_reset_email(email: str, token: str):
    """Sends an email with a password reset link."""
    # In a real app, this base URL should come from a config file or environment variable.
    base_url = "http://localhost:8501"
    reset_link = f"{base_url}?token={token}"
    
    _send_email(email, "Dicideon Password Reset", _format_reset_email_body(reset_link))

def handle_signup_request(form_data):
    """Saves the request to Excel and sends a notification email."""
    _create_pending_requests_file_if_not_exists()

    # 1. Prepare data and save to Excel
    request_data = form_data.copy()
    request_data['request_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    request_data['status'] = 'pending'
    request_data['user_password'] = hash_password(request_data.pop('password')) # Hash password for security

    df = pd.read_excel(PENDING_REQUESTS_FILE)
    new_request_df = pd.DataFrame([request_data])
    updated_df = pd.concat([df, new_request_df], ignore_index=True)
    updated_df.to_excel(PENDING_REQUESTS_FILE, index=False)

    # 2. Send notification email to admin
    _send_email(ADMIN_EMAIL, f"New Dicideon Access Request from {form_data['email']}", _format_email_body(form_data))

def _send_email(recipient_email, subject, html_body):
    """A generic function to send an HTML email."""
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")

    if not sender_email or not sender_password:
        st.warning("Email credentials not configured. Skipping email notification.")
        return False

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
        return True
    except Exception as e:
        st.error(f"Failed to send notification email: {e}")
        print(f"Email Error: {e}")
        return False