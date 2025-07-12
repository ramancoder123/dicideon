import streamlit as st

def show_signup_ui():
    """Signup form UI"""
    st.markdown("""
        <div class="auth-form">
            <h2 style="text-align: center;">Create Account</h2>
            <div style="margin-bottom: 1rem;">
                <label>Email</label>
                <input type="email" class="stTextInput" style="width: 100%;">
            </div>
            <div style="margin-bottom: 1rem;">
                <label>Username</label>
                <input type="text" class="stTextInput" style="width: 100%;">
            </div>
            <div style="margin-bottom: 1rem;">
                <label>Password</label>
                <input type="password" class="stTextInput" style="width: 100%;">
            </div>
            <div style="margin-bottom: 1rem;">
                <label>Confirm Password</label>
                <input type="password" class="stTextInput" style="width: 100%;">
            </div>
            <button class="stButton" style="width: 100%;">Sign Up</button>
            <p style="text-align: center; margin-top: 1rem;">
                Already have an account? <a href="#login" style="color: #4A90E2;">Sign in</a>
            </p>
        </div>
    """, unsafe_allow_html=True)