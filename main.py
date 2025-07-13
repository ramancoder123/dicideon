import streamlit as st
from PIL import Image
from auth import auth_utils, session_manager, password_reset_utils
from utils import validator, request_handler, location_handler, exceptions
import datetime
import streamlit.components.v1 as components
import os
from dotenv import load_dotenv

# --- PAGE CONFIG ---
st.set_page_config(page_title="Dicideon", layout="wide")

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv() # This will load the .env file

# --- LOAD DATA AND HANDLE ERRORS ---
# This must be called after set_page_config() to display errors correctly.
location_error = location_handler.load_location_data()
if location_error:
    st.error(location_error)
    st.stop() # Stop the app if location data can't be loaded

# --- SESSION STATE INITIALIZATION ---
session_manager.init_session()
if 'otp_sent_for_email' not in st.session_state:
    st.session_state.otp_sent_for_email = None
if 'signup_data' not in st.session_state:
    st.session_state.signup_data = {}
if 'otp_expires_at' not in st.session_state:
    st.session_state.otp_expires_at = None


# --- DARK THEME CSS OVERRIDE ---
st.markdown("""
<style>
    /* --- Global Styles --- */
    body {
        background-color: #0e1117;
        color: white;
        overflow-y: auto; /* Scroll support for mobile keyboards */
    }

    html, body, #root {
        height: 100%;
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    *, *::before, *::after {
        box-sizing: inherit;
    }

    /* --- Main Layout Container --- */
    .block-container {
        padding: 20px !important; /* Padding for small screens */
        max-width: 100% !important;
        width: 100vw;
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        align-items: center; /* Keep horizontal centering */
        justify-content: flex-start; /* Align content to the top */
        padding-top: 3rem !important; /* Add space at the top for a navbar feel */
    }

    /* --- Form Wrapper/Card --- */
    /* Targets the main vertical block on the auth page */
    [data-testid="stAppViewContainer"] > .main .block-container > [data-testid="stVerticalBlock"] {
        width: 90%; /* Mobile first */
        max-width: 400px;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 20px; /* Vertical spacing */
    }

    /* --- Logo --- */
    [data-testid="stImage"] img {
        width: 80px; /* Mobile width */
        height: auto;
    }

    /* --- Headings --- */
    h2 {
        font-size: 1.5rem; /* Mobile font size */
        text-align: center;
        margin: 0;
    }
    h5 {
        font-size: 0.9rem; /* Mobile font size */
        text-align: center;
        color: #bbb;
        font-style: italic;
        margin: 0;
        margin-top: -10px; /* Pull subtitle closer to title */
    }

    /* --- Form Element Styling --- */
    .stTextInput input, .stDateInput input, .stSelectbox > div > div {
        height: 45px;
        padding: 0 12px;
        border-radius: 10px;
        background-color: #2a2c32;
        border: 1px solid #4a4c52;
        color: white;
    }
    .stButton > button {
        width: 100%;
        height: 45px;
        padding: 12px;
        border-radius: 10px;
        background-color: #6C63FF;
        color: white;
        border: none;
    }

    /* --- Tab Styling --- */
    .stTabs { width: 100%; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px; /* Keep the gap between tabs */
        justify-content: flex-start; /* Left-align the tabs */
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.9rem;
        padding: 10px 0;
    }
    .stTabs [aria-selected="true"] {
        border-bottom: 2px solid #6C63FF;
    }

    /* --- Desktop Styles --- */
    @media (min-width: 600px) {
        [data-testid="stImage"] img {
            width: 120px; /* Desktop width */
        }
        h2 {
            font-size: 2.2rem; /* Desktop font size */
        }
        h5 {
            font-size: 1.1rem; /* Desktop font size */
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 30px;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- LOGO PATH ---
_current_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(_current_dir, "data", "logo.png")

# --- MAIN APP ---
if st.session_state.authenticated:
    st.success(f"Welcome, {st.session_state.user}!")
    st.write("This is the main application page.")
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.rerun()

# --- AUTHENTICATION PAGE ---
else:
    # Check for a password reset token in the URL query parameters
    if 'token' in st.query_params:
        token = st.query_params['token']
        email = password_reset_utils.verify_reset_token(token)

        st.image(logo_path)
        if email:
            st.success(f"Token verified for {email}. Please set your new password.")
            with st.form("reset_password_form"):
                new_password = st.text_input("New Password", type="password")
                confirm_new_password = st.text_input("Confirm New Password", type="password")
                submitted_reset = st.form_submit_button("Reset Password", type="primary")

                if submitted_reset:
                    if not validator.validate_password(new_password):
                        st.error("Password must be at least 8 characters long and contain a number.")
                    elif new_password != confirm_new_password:
                        st.error("Passwords do not match.")
                    else:
                        if password_reset_utils.reset_password(token, new_password):
                            st.success("Your password has been reset successfully! You can now log in with your new password.")
                            st.info("Please remove the token from the URL before logging in.")
                        else:
                            st.error("Failed to reset password. The link may have expired.")
        else:
            st.error("Invalid or expired password reset link. Please request a new one.")

    else:
        # The layout is now controlled entirely by CSS for a responsive, centered look.
        
        # --- Header Section ---
        st.image(logo_path) # Width/height is now controlled by CSS
        st.markdown("## 👋 Welcome to **Dicideon**")
        st.markdown("##### _AI That Advises_")

        # --- Tab Navigation ---
        tab1, tab2 = st.tabs(["🔐 Sign In", "🆕 Sign Up"])

        with tab1:
            # Reconstructed the login form correctly inside the "Sign In" tab.
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", type="primary")
                if submitted:
                    if auth_utils.authenticate_user(email, password):
                        st.session_state.authenticated = True
                        st.session_state.user = email
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
            
            # --- Forgot Password Form (Moved outside the login form) ---
            with st.form("forgot_password_form"):
                st.markdown("###### Forgot Your Password?")
                forgot_email = st.text_input("Enter your email to get a reset link", key="forgot_email_input")
                submitted_forgot = st.form_submit_button("Send Reset Link")
                if submitted_forgot:
                    token = password_reset_utils.generate_reset_token(forgot_email)
                    if token:
                        try:
                            request_handler.send_password_reset_email(forgot_email, token)
                        except (exceptions.EmailConfigurationError, exceptions.EmailSendingError):
                            # Don't show a specific error here to prevent email enumeration,
                            # but the error will be logged to the console for the admin.
                            pass
                    # Show same message for security to prevent user enumeration
                    st.success("If an account with that email exists, a password reset link has been sent.")

        with tab2:
            # If an OTP has been sent, show the verification form
            if st.session_state.otp_sent_for_email and st.session_state.otp_expires_at:
                st.info(f"An OTP has been sent to {st.session_state.otp_sent_for_email}. Please enter it below to complete your registration.")
                
                # --- JavaScript Countdown Timer ---
                expiration_timestamp = st.session_state.otp_expires_at.timestamp()
                components.html(f"""
                    <div id="timer" style="font-weight: bold; text-align: center; margin-bottom: 1rem; color: white;"></div>
                    <script>
                        var expirationTimestamp = {expiration_timestamp};
                        var timerElement = document.getElementById("timer");
                        
                        function countdown() {{
                            var countDownDate = new Date(expirationTimestamp * 1000);
                            var x = setInterval(function() {{
                                var now = new Date();
                                var distance = countDownDate - now;

                                if (distance < 0) {{
                                    clearInterval(x);
                                    timerElement.innerHTML = "<p style='color: #FF4B4B; font-weight: bold;'>OTP has expired. Please go back and request a new one.</p>";
                                    return;
                                }}

                                var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                                var seconds = Math.floor((distance % (1000 * 60)) / 1000);

                                timerElement.innerHTML = "Time remaining: " + minutes.toString().padStart(2, '0') + ":" + seconds.toString().padStart(2, '0');
                            }}, 1000);
                        }}
                        countdown();
                    </script>
                """, height=50)

                with st.form("otp_verification_form"):
                    otp_input = st.text_input("Enter 6-Digit OTP", max_chars=6)

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        submitted_otp = st.form_submit_button("Verify & Complete Sign-Up", type="primary")
                    with col2:
                        go_back = st.form_submit_button("Go Back & Edit Details")
                    with col3:
                        resend_otp = st.form_submit_button("Send OTP Again")

                    if go_back:
                        st.session_state.otp_sent_for_email = None
                        st.session_state.otp_expires_at = None
                        st.rerun()

                    if resend_otp:
                        try:
                            new_expiration_time = request_handler.regenerate_and_resend_otp(st.session_state.otp_sent_for_email)
                            if new_expiration_time:
                                st.session_state.otp_expires_at = new_expiration_time
                                st.success("A new OTP has been sent to your email.")
                                st.rerun()
                            else:
                                st.error("Could not find your sign-up request. Please go back and start over.")
                                st.session_state.otp_sent_for_email = None
                                st.session_state.otp_expires_at = None
                                st.rerun()
                        except exceptions.EmailConfigurationError:
                            st.error("Sorry, the email service is currently unavailable. Please try again later.")
                        except exceptions.EmailSendingError:
                            st.error("Failed to send new OTP. Please check your email address and try again.")

                    if submitted_otp:
                        if request_handler.verify_otp_and_finalize_request(st.session_state.otp_sent_for_email, otp_input):
                            st.success("Thank you! Your access request has been submitted for approval.")
                            st.balloons()
                            st.session_state.signup_data = {} # Clear form data on success
                            st.session_state.otp_sent_for_email = None
                            st.session_state.otp_expires_at = None
                            st.rerun()
                        else:
                            st.error("The OTP you entered is incorrect. Please try again.")
                            # We no longer reset the state or rerun the app,
                            # allowing the user to make another attempt.
            # Otherwise, show the main sign-up form
            else:
                with st.form("signup_request_form", clear_on_submit=False):
                    st.markdown("**Personal Details**")
                    col1, col2 = st.columns(2, gap="medium")
                    with col1:
                        first_name = st.text_input("First Name*", value=st.session_state.signup_data.get("first_name", ""))
                        middle_name = st.text_input("Middle Name", value=st.session_state.signup_data.get("middle_name", ""))
                        dob = st.date_input("Date of Birth*", value=st.session_state.signup_data.get("dob", datetime.date.today()), min_value=datetime.date(1940, 1, 1), max_value=datetime.date.today())
                    with col2:
                        last_name = st.text_input("Last Name*", value=st.session_state.signup_data.get("last_name", ""))
                        email = st.text_input("Email*", value=st.session_state.signup_data.get("email", ""))
                        gender_options = ["Select...", "Male", "Female", "Other", "Prefer not to say"]
                        gender_index = gender_options.index(st.session_state.signup_data.get("gender", "Select...")) if st.session_state.signup_data.get("gender") in gender_options else 0
                        gender = st.selectbox("Gender*", options=gender_options, index=gender_index)

                    st.markdown("---")
                    st.markdown("**Location & Contact**")
                    countries = location_handler.get_countries()
                    states = location_handler.get_states(None)
                    cities = location_handler.get_cities(None)

                    col1, col2 = st.columns(2, gap="medium")
                    with col1:
                        country_index = (["Select..."] + countries).index(st.session_state.signup_data.get("country", "Select...")) if st.session_state.signup_data.get("country") in countries else 0
                        selected_country_name = st.selectbox("Country*", options=["Select..."] + countries, index=country_index)
                    with col2:
                        state_index = (["Select..."] + states).index(st.session_state.signup_data.get("state", "Select...")) if st.session_state.signup_data.get("state") in states else 0
                        selected_state_name = st.selectbox("State*", options=["Select..."] + states, index=state_index)

                    city_index = (["Select..."] + cities).index(st.session_state.signup_data.get("city", "Select...")) if st.session_state.signup_data.get("city") in cities else 0
                    selected_city_name = st.selectbox("City*", options=["Select..."] + cities, index=city_index)

                    col1, col2 = st.columns([1, 2], gap="medium")
                    with col1:
                        country_code_val = location_handler.get_country_code(selected_country_name)
                        country_code = st.text_input("Phone Code*", value=st.session_state.signup_data.get("country_code", country_code_val))
                    with col2:
                        contact_number = st.text_input("Contact Number*", value=st.session_state.signup_data.get("contact_number", ""))

                    st.markdown("---")
                    st.markdown("**Organization & Credentials**")
                    col1, col2 = st.columns(2, gap="medium")
                    with col1:
                        org_name = st.text_input("Organization Name*", value=st.session_state.signup_data.get("organization_name", ""))
                        password = st.text_input("Password*", type="password")
                    with col2:
                        user_id = st.text_input("User ID (Organization ID)*", value=st.session_state.signup_data.get("user_id", ""))
                        confirm_password = st.text_input("Confirm Password*", type="password")

                    submitted = st.form_submit_button("Send OTP", type="primary")
                    if submitted:
                        error_messages = []

                        # Uniqueness check now returns errors and notifications
                        uniqueness_errors, notifications_to_send = validator.check_uniqueness(email, user_id, contact_number)
                        error_messages.extend(uniqueness_errors)

                        # If duplicates were found, send security alerts to original users
                        if notifications_to_send:
                            for field, original_email in notifications_to_send.items():
                                try:
                                    request_handler.send_security_alert_email(original_email, field)
                                except Exception as e:
                                    print(f"Failed to send security alert for duplicate {field} to {original_email}: {e}")

                        if not all([first_name, last_name, email, contact_number, org_name, user_id, password, confirm_password]):
                            error_messages.append("Please fill out all required fields marked with *.")
                        if gender == "Select...": error_messages.append("Please select a gender.")
                        if selected_country_name == "Select...": error_messages.append("Please select a country.")
                        
                        country_iso2 = location_handler.get_country_iso2(selected_country_name)
                        if country_iso2 and not validator.validate_phone_number(contact_number, country_iso2):
                            error_messages.append("Please enter a valid contact number for the selected country.")
                        elif not country_iso2 and selected_country_name != "Select...":
                            error_messages.append(f"Could not find validation information for country: {selected_country_name}.")

                        if not validator.validate_email(email): error_messages.append("Invalid email format.")
                        if not validator.validate_password(password): error_messages.append("Password must be at least 8 characters long and contain a number.")
                        if password != confirm_password: error_messages.append("Passwords do not match.")

                        # Use a set to remove duplicate messages before displaying
                        unique_errors = sorted(list(set(error_messages)))
                        if unique_errors:
                            for msg in unique_errors:
                                st.error(msg)
                        else:
                            # Store form data in session state to pre-fill if OTP fails
                            st.session_state.signup_data = {
                                "first_name": first_name, "middle_name": middle_name, "last_name": last_name, "email": email, 
                                "dob": dob, "gender": gender, "country": selected_country_name, 
                                "state": selected_state_name, "city": selected_city_name,
                                "country_code": country_code, "contact_number": contact_number,
                                "organization_name": org_name, "user_id": user_id
                                # Password is intentionally not stored in session state
                            }
                            
                            # Prepare data for the request handler, adding password just for the request
                            request_data = st.session_state.signup_data.copy()
                            request_data['date_of_birth'] = request_data.pop('dob').strftime("%Y-%m-%d")
                            request_data['password'] = password

                            try:
                                expiration_time = request_handler.initiate_signup_and_send_otp(request_data)
                                st.session_state.otp_sent_for_email = email
                                st.session_state.otp_expires_at = expiration_time
                                st.rerun()
                            except exceptions.EmailConfigurationError:
                                st.error("Sorry, the email service is currently unavailable. Please try again later.")
                            except exceptions.EmailSendingError:
                                st.error("Failed to send OTP. Please check your email address and try again.")
