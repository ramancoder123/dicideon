import streamlit as st
from auth import auth_utils, session_manager, password_reset_utils
from utils import validator, request_handler, location_handler, exceptions
from admin import dashboard as admin_dashboard
import datetime
import streamlit.components.v1 as components
import logging
import os

# --- App Setup ---
# This single import and function call handles all initial configurations:
# path setup, page config, CSS, environment variables, and logging.
from app_setup import initialize_app, LOGO_PATH
initialize_app()

# The initialize_app function handles path setup, so we can import database after.
import database  # Import the new database module

def render_password_reset_page(token: str):
    """Displays the UI for resetting a password when a token is present."""
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH)
    try:
        email = password_reset_utils.verify_reset_token(token)
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
    except Exception as e:
        st.error("An unexpected error occurred during token verification. Please try again.")
        print(f"Password reset error: {e}")

def _render_otp_verification_form():
    """Renders the UI for OTP verification."""
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

    # The main verification action is handled within a form.
    with st.form("otp_verification_form"):
        otp_input = st.text_input("Enter 6-Digit OTP", max_chars=6)
        submitted_otp = st.form_submit_button("Verify & Complete Sign-Up", type="primary", use_container_width=True)
        
        if submitted_otp:
            # Strip whitespace from user input to prevent comparison errors
            clean_otp = otp_input.strip()
            if request_handler.verify_otp_and_finalize_request(st.session_state.otp_sent_for_email, clean_otp):
                # Set the state for the new success message screen
                st.session_state.signup_complete = True
                st.session_state.approval_eta = datetime.datetime.now() + datetime.timedelta(hours=4)
                st.session_state.signup_data = {} # Clear form data on success
                st.session_state.otp_sent_for_email = None
                st.session_state.otp_expires_at = None
                st.rerun()
            else:
                st.error("The OTP you entered is incorrect or has expired. Please try again.")

    # Secondary actions (Go Back, Resend) are handled outside the form using regular buttons.
    # This is a better practice than having multiple submit buttons in one form.
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Go Back & Edit Details", use_container_width=True):
            st.session_state.otp_sent_for_email = None
            st.session_state.otp_expires_at = None
            st.rerun()
    with col2:
        if st.button("Send OTP Again", use_container_width=True):
            try:
                new_expiration_time = request_handler.regenerate_and_resend_otp(st.session_state.otp_sent_for_email)
                if new_expiration_time:
                    st.session_state.otp_expires_at = new_expiration_time
                    st.success("A new OTP has been sent to your email.")
                    st.rerun()
                else:
                    st.error("Could not find your sign-up request. Please go back and start over.")
            except exceptions.EmailConfigurationError:
                st.error("Sorry, the email service is currently unavailable. Please try again later.")
            except exceptions.EmailSendingError:
                st.error("Failed to send new OTP. Please check your email address and try again.")
                
def _validate_signup_form(form_data: dict) -> list[str]:
    """
    Performs all validation for the signup form, sends security alerts,
    and returns a list of unique, sorted error messages.
    """
    errors = []
    
    # Extract data for validation
    email = form_data.get("email")
    user_id = form_data.get("user_id")
    contact_number = form_data.get("contact_number")
    password = form_data.get("password")
    confirm_password = form_data.get("confirm_password")
    selected_country_name = form_data.get("country")
    
    # 1. Uniqueness Checks (and security alerts)
    uniqueness_errors, notifications_to_send = validator.check_uniqueness(email, user_id, contact_number)
    errors.extend(uniqueness_errors)
    
    if notifications_to_send:
        for field, original_email in notifications_to_send.items():
            try:
                request_handler.send_security_alert_email(original_email, field)
            except Exception as e:
                logging.warning(f"Failed to send security alert for duplicate {field} to {original_email}: {e}")
                
    # 2. Required Field Checks
    required_fields = ["first_name", "last_name", "email", "contact_number", "organization_name", "user_id", "password", "confirm_password"]
    if not all(form_data.get(f) for f in required_fields):
        errors.append("Please fill out all required fields marked with *.")
    if form_data.get("gender") == "Select...":
        errors.append("Please select a gender.")
    if selected_country_name == "Select...":
        errors.append("Please select a country.")
        
    # 3. Format-specific validations
    country_iso2 = location_handler.get_country_iso2(selected_country_name)
    if country_iso2 and not validator.validate_phone_number(contact_number, country_iso2):
        errors.append("Please enter a valid contact number for the selected country.")
    elif not country_iso2 and selected_country_name != "Select...":
        errors.append(f"Could not find validation information for country: {selected_country_name}.")
        
    if not validator.validate_email(email):
        errors.append("Invalid email format.")
    if not validator.validate_password(password):
        errors.append("Password must be at least 8 characters long and contain a number.")
    if password != confirm_password:
        errors.append("Passwords do not match.")
        
    return sorted(list(set(errors)))

def _handle_signup_submission(form_data: dict):
    """Orchestrates the validation and processing of the signup form."""
    # 1. Validate all form data
    error_messages = _validate_signup_form(form_data)
    if error_messages:
        for msg in error_messages:
            st.error(msg)
        return

    # 2. If validation passes, proceed with OTP process
    # Exclude passwords from session state for security
    st.session_state.signup_data = {k: v for k, v in form_data.items() if k not in ['password', 'confirm_password']}
    
    # Prepare data for the request handler, adding password back just for the request
    request_data = st.session_state.signup_data.copy()
    request_data['date_of_birth'] = request_data.pop('dob').strftime("%Y-%m-%d")
    request_data['password'] = form_data.get('password')

    try:
        expiration_time = request_handler.initiate_signup_and_send_otp(request_data)
        st.session_state.otp_sent_for_email = form_data.get('email')
        st.session_state.otp_expires_at = expiration_time
        st.rerun()
    except exceptions.EmailConfigurationError:
        st.error("Sorry, the email service is currently unavailable. Please try again later.")
    except exceptions.EmailSendingError:
        st.error("Failed to send OTP. Please check your email address and try again.")

def _render_signup_form():
    """Renders the main user registration form."""
    with st.form("signup_request_form", clear_on_submit=False):
        st.markdown("**Personal Details**")
        col1, col2 = st.columns(2, gap="medium")
        with col1:
            first_name = st.text_input("First Name*", value=st.session_state.signup_data.get("first_name", ""))
            middle_name = st.text_input("Middle Name", value=st.session_state.signup_data.get("middle_name", ""))
            dob = st.date_input("Date of Birth*", value=st.session_state.signup_data.get("dob", None), min_value=datetime.date(1940, 1, 1), max_value=datetime.date.today())
        with col2:
            last_name = st.text_input("Last Name*", value=st.session_state.signup_data.get("last_name", ""))
            email = st.text_input("Email*", value=st.session_state.signup_data.get("email", ""))
            gender_options = ["Select...", "Male", "Female", "Other", "Prefer not to say"]
            gender_index = gender_options.index(st.session_state.signup_data.get("gender", "Select...")) if st.session_state.signup_data.get("gender") in gender_options else 0
            gender = st.selectbox("Gender*", options=gender_options, index=gender_index)

        st.markdown("---")
        st.markdown("**Location & Contact**")
        # Get the master list of countries once. State and City lists will be generated dynamically.
        countries = location_handler.get_countries()

        # --- Country and State Selection ---
        col1, col2 = st.columns(2, gap="medium")
        with col1:
            country_index = (["Select..."] + countries).index(st.session_state.signup_data.get("country", "Select...")) if st.session_state.signup_data.get("country") in countries else 0
            selected_country_name = st.selectbox("Country*", options=["Select..."] + countries, index=country_index, key="country_select")

        # Dynamically get the list of states based on the selected country.
        states = location_handler.get_states(selected_country_name)
        with col2:
            # If the selected country changes, the old state might no longer be valid.
            # We check if the stored state is in the new list; if not, we reset it.
            current_state = st.session_state.signup_data.get("state", "Select...")
            if current_state not in states:
                current_state = "Select..."
            state_index = (["Select..."] + states).index(current_state)
            selected_state_name = st.selectbox("State*", options=["Select..."] + states, index=state_index, key="state_select")

        # Dynamically get the list of cities based on the selected state.
        cities = location_handler.get_cities(selected_state_name)
        
        # Similar to the state logic, we reset the city if the selected state changes.
        current_city = st.session_state.signup_data.get("city", "Select...")
        if current_city not in cities:
            current_city = "Select..."
        city_index = (["Select..."] + cities).index(current_city)
        selected_city_name = st.selectbox("City*", options=["Select..."] + cities, index=city_index, key="city_select")

        # --- Phone Code and Contact Number ---
        col1, col2 = st.columns([1, 2], gap="medium")
        with col1:
            # The phone code is now automatically derived from the selected country.
            # It is displayed in a disabled input field to prevent user modification.
            country_code_val = location_handler.get_country_code(selected_country_name)
            # We still assign it to a variable to pass it along with the form data.
            country_code = st.text_input("Phone Code*", value=country_code_val, disabled=True)
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
            # Collect all form data into a dictionary to pass to the handler
            form_data = {
                "first_name": first_name, "middle_name": middle_name, "last_name": last_name, "email": email, 
                "dob": dob, "gender": gender, "country": selected_country_name, 
                "state": selected_state_name, "city": selected_city_name,
                "country_code": country_code, "contact_number": contact_number,
                "organization_name": org_name, "user_id": user_id,
                "password": password, "confirm_password": confirm_password
            }
            _handle_signup_submission(form_data)

def _render_login_form():
    """Renders the user login form."""
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

def _render_forgot_password_form():
    """Renders the form for initiating a password reset."""
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

def _render_signup_confirmation_page():
    """Displays the final confirmation message after a successful sign-up request."""
    eta_time = st.session_state.approval_eta.strftime("%I:%M %p on %B %d, %Y")
    st.success("Your request has been mailed for approval.")
    st.info(f"Kindly wait for a response. Your request will be reviewed by approximately **{eta_time}**.")
    st.balloons()
    if st.button("← Back to Login", use_container_width=True):
        # Reset all signup-related state to ensure a clean slate for the next user.
        st.session_state.signup_complete = False
        st.session_state.approval_eta = None
        st.session_state.signup_data = {}
        st.session_state.otp_sent_for_email = None
        st.session_state.otp_expires_at = None
        st.rerun()

def render_authentication_page():
    """Displays the main authentication page with Sign In and Sign Up tabs."""
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH) # Width/height is now controlled by CSS
    st.markdown("## 👋 Welcome to **Dicideon**")
    st.markdown("##### _AI That Advises_")

    # --- Tab Navigation ---
    tab1, tab2 = st.tabs(["🔐 Sign In", "🆕 Sign Up"])

    with tab1:
        _render_login_form()
        _render_forgot_password_form()

    with tab2:
        # The logic is now routed to the appropriate rendering function based on session state.
        # 1. If sign-up is fully complete, show the final confirmation message.
        if st.session_state.get('signup_complete', False):
            _render_signup_confirmation_page()
        # 2. If an OTP has been sent, show the verification form.
        elif st.session_state.get('otp_sent_for_email') and st.session_state.get('otp_expires_at'):
            _render_otp_verification_form()
        # 3. Otherwise, show the main sign-up form.
        else:
            _render_signup_form()

def _initialize_session_state():
    """Initializes all required keys in Streamlit's session state for a clean startup."""
    session_manager.init_session() # This handles 'authenticated' and 'user'
    
    # Define keys and their default values to ensure they exist
    default_session_keys = {
        "otp_sent_for_email": None,
        "signup_data": {},
        "otp_expires_at": None,
        "signup_complete": False,
        "approval_eta": None
    }
    
    for key, value in default_session_keys.items():
        if key not in st.session_state:
            st.session_state[key] = value

def main():
    database.init_db()  # Create database and tables if they don't exist

    # --- LOAD DATA AND HANDLE ERRORS ---
    location_error = location_handler.load_location_data()
    if location_error:
        st.error(location_error)
        st.stop() # Stop the app if location data can't be loaded

    _initialize_session_state()

    # --- MAIN APP ROUTING ---
    if st.session_state.authenticated:
        # Place logout button in a consistent sidebar location
        st.sidebar.success(f"Logged in as {st.session_state.user}")
        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()

        # Route to the appropriate view based on user role
        if st.session_state.user == request_handler.ADMIN_EMAIL:
            admin_dashboard.render_dashboard()
        else:
            st.title("Welcome to Dicideon")
            st.write("This is the main application page for regular users.")
    else:
        # Check for a password reset token in the URL query parameters to decide which page to render.
        query_params = st.query_params.to_dict()
        if 'token' in query_params:
            render_password_reset_page(query_params['token'])
        else:
            render_authentication_page()

if __name__ == "__main__":
    main()