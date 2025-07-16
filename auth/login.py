import streamlit as st

def show_login_ui():
    """Login form UI"""
    st.markdown("""
        <div class="auth-form">
            <h2 style="text-align: center;">Login</h2>
            <div style="margin-bottom: 1rem;">
                <label>Email</label>
                <input type="email" class="stTextInput" style="width: 100%;">
            </div>
            <div style="margin-bottom: 1rem;">
                <label>Password</label>
                <input type="password" class="stTextInput" style="width: 100%;">
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                <label><input type="checkbox"> Remember me</label>
                <a href="#forgot" style="color: #4A90E2;">Forgot password?</a>
            </div>
            <button class="stButton" style="width: 100%;">Login</button>
            <p style="text-align: center; margin-top: 1rem;">
                Don't have an account? <a href="#signup" style="color: #4A90E2;">Sign up</a>
            </p>
        </div>
    """, unsafe_allow_html=True)