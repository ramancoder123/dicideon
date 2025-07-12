import streamlit as st

def init_session():
    """Initialize all session state variables"""
    defaults = {
        "user": None,
        "authenticated": False,
        "theme": "Dark"
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value