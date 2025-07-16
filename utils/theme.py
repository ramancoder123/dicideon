import streamlit as st

def apply_theme():
    """Apply theme colors to all components"""
    st.markdown(f"""
        <style>
            .stTextInput input, .stTextInput label {{
                color: {'#FAFAFA' if st.session_state.theme == 'Dark' else '#31333F'} !important;
            }}
            .stButton>button {{
                background-color: {'#4A90E2' if st.session_state.theme == 'Dark' else '#1E88E5'};
                color: white !important;
            }}
        </style>
    """, unsafe_allow_html=True)

def toggle_theme():
    """Switch between dark/light mode"""
    st.session_state.theme = 'Light' if st.session_state.theme == 'Dark' else 'Dark'
    apply_theme()