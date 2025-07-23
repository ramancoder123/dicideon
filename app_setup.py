import streamlit as st
import sys
import os
import logging
from dotenv import load_dotenv

# --- Project Root Definition ---
# Define the project root once and use it for all path constructions.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# --- Constants ---
# Define the path to the logo. Assumes an 'assets' directory in the project root.
# You may need to create this directory and place your logo file inside it.
LOGO_PATH = os.path.join(PROJECT_ROOT, "assets", "logo.png")

def _setup_path():
    """Adds the project root to the Python path for consistent imports."""
    # This ensures that modules can be imported from the project root,
    # regardless of where the script is run from.
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

def _configure_page():
    """Sets the Streamlit page configuration."""
    st.set_page_config(
        page_title="Dicideon",
        page_icon="🎲", # A dice emoji as a placeholder
        layout="wide",
        initial_sidebar_state="auto",
    )

def _load_css(file_path="style.css"):
    """Loads and injects a custom CSS file if it exists."""
    full_css_path = os.path.join(PROJECT_ROOT, file_path)
    if os.path.exists(full_css_path):
        with open(full_css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        logging.info(f"Custom CSS file not found at '{full_css_path}'. Skipping.")

def _configure_logging():
    """Configures basic logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] - %(message)s",
    )

def initialize_app():
    """
    Performs all initial application setup tasks as described in main.py.
    """
    _setup_path()
    load_dotenv() # Loads variables from a .env file
    _configure_logging()
    _configure_page()
    _load_css() # Assumes style.css is in the root directory
    logging.info("Application initialized successfully.")