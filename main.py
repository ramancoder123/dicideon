import streamlit as st
from PIL import Image
from auth import auth_utils, session_manager, password_reset_utils
from utils import validator, request_handler, location_handler
import datetime
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Dicideon", layout="wide")

# --- LOAD DATA AND HANDLE ERRORS ---
# This must be called after set_page_config() to display errors correctly.
location_error = location_handler.load_location_data()
if location_error:
    st.error(location_error)
    st.stop() # Stop the app if location data can't be loaded

# --- SESSION STATE INITIALIZATION ---
session_manager.init_session()


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
        tab1, tab2 = st.tabs(["🔐 Sign In", " 🆕 Sign Up"])

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
                        request_handler.send_password_reset_email(forgot_email, token)
                    # Show same message for security to prevent user enumeration
                    st.success("If an account with that email exists, a password reset link has been sent.")

        with tab2:
            # Removed redundant headers for a cleaner UI.
            with st.form("signup_request_form", clear_on_submit=True):
                st.markdown("**Personal Details**")
                # A consistent two-column layout for a professional, indented look
                col1, col2 = st.columns(2, gap="medium")
                with col1:
                    first_name = st.text_input("First Name*")
                    middle_name = st.text_input("Middle Name")
                    dob = st.date_input("Date of Birth*", min_value=datetime.date(1940, 1, 1), max_value=datetime.date.today())
                with col2:
                    last_name = st.text_input("Last Name*")
                    email = st.text_input("Email*") # No longer takes up the full width
                    gender = st.selectbox("Gender*", ["Select...", "Male", "Female", "Other", "Prefer not to say"])

                st.markdown("---")
                st.markdown("**Location & Contact**")
                countries = location_handler.get_countries()
                states = location_handler.get_states(None) # Get the full list of states, unlinked
                cities = location_handler.get_cities(None) # Argument is ignored, get full list

                # New, cleaner layout for location and contact info
                col1, col2 = st.columns(2, gap="medium")
                with col1:
                    selected_country_name = st.selectbox("Country*", options=["Select..."] + countries)
                with col2:
                    selected_state_name = st.selectbox("State*", options=["Select..."] + states)

                selected_city_name = st.selectbox("City*", options=["Select..."] + cities)

                col1, col2 = st.columns([1, 2], gap="medium")
                with col1:
                    country_code_val = location_handler.get_country_code(selected_country_name)
                    country_code = st.text_input("Phone Code*", value=country_code_val)
                with col2:
                    contact_number = st.text_input("Contact Number*")

                st.markdown("---")
                st.markdown("**Organization & Credentials**")
                col1, col2 = st.columns(2, gap="medium")
                with col1:
                    org_name = st.text_input("Organization Name*")
                    password = st.text_input("Password*", type="password")
                with col2:
                    user_id = st.text_input("User ID (Organization ID)*")
                    confirm_password = st.text_input("Confirm Password*", type="password")

                # --- FORM SUBMISSION ---
                submitted = st.form_submit_button("Request Access", type="primary")
                if submitted:
                    # --- Validation ---
                    error_messages = []
                    if not all([first_name, last_name, email, contact_number, org_name, user_id, password, confirm_password]):
                        error_messages.append("Please fill out all required fields marked with *.")
                    if gender == "Select...":
                        error_messages.append("Please select a gender.")
                    if selected_country_name == "Select...":
                        error_messages.append("Please select a country.")
                    if states and selected_state_name == "Select...":
                        error_messages.append("Please select a state.")
                    if cities and selected_city_name == "Select...":
                        error_messages.append("Please select a city.")
                    if not validator.validate_email(email):
                        error_messages.append("Invalid email format.")
                    if not validator.validate_password(password):
                        error_messages.append("Password must be at least 8 characters long and contain a number.")
                    if password != confirm_password:
                        error_messages.append("Passwords do not match.")

                    if error_messages:
                        for msg in error_messages:
                            st.error(msg)
                    else:
                        # All checks passed, proceed with handling the request
                        form_data = {
                            "first_name": first_name, "middle_name": middle_name, "last_name": last_name,
                            "email": email, "date_of_birth": dob.strftime("%Y-%m-%d"), "gender": gender, "country": selected_country_name, 
                            "state": selected_state_name, "city": selected_city_name,
                            "country_code": country_code, "contact_number": contact_number,
                            "organization_name": org_name, "user_id": user_id, "password": password
                        }
                        request_handler.handle_signup_request(form_data)
                        st.success("Thank you! Your access request has been submitted for approval.")
                        st.balloons()
