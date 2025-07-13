import pandas as pd
import os
import streamlit as st

# --- Robust Path Definition ---
# Get the absolute path of the directory containing this script (utils)
_current_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the absolute path to the data directory (one level up from utils)
_data_dir = os.path.join(os.path.dirname(_current_dir), "data")

COUNTRIES_FILE = os.path.join(_data_dir, "countries.csv")
STATES_FILE = os.path.join(_data_dir, "states.csv")
CITIES_FILE = os.path.join(_data_dir, "cities.csv")

# Use a global dictionary to act as a cache to avoid re-loading data.
# This also prevents the st.cache_data issue with calling st.error() during script startup.
_location_cache = {}

def load_location_data():
    """
    Loads and caches location data from separate files without linking them.
    This provides independent dropdowns for country, state, and city.
    Returns an error message string on failure, otherwise None.
    """
    if _location_cache:  # Data already loaded
        return None

    try:
        # 1. Load countries for dropdown and phone codes
        country_cols = ['name', 'phonecode', 'iso2']
        countries_df = pd.read_csv(COUNTRIES_FILE, usecols=country_cols, dtype={'phonecode': str, 'iso2': str})
        countries_df.dropna(subset=['name'], inplace=True)
        countries_df['name'] = countries_df['name'].str.strip()

        # 2. Load all states for a separate, unlinked dropdown
        state_cols = ['name']
        states_df = pd.read_csv(STATES_FILE, usecols=state_cols)
        states_df.dropna(subset=['name'], inplace=True)
        states_df['name'] = states_df['name'].str.strip()

        # 3. Load all cities for a separate, unlinked dropdown
        city_cols = ['name']
        cities_df = pd.read_csv(CITIES_FILE, usecols=city_cols)
        cities_df.dropna(subset=['name'], inplace=True)
        cities_df['name'] = cities_df['name'].str.strip()

        # 4. Pre-process for fast lookups
        _location_cache['countries_list'] = sorted(countries_df['name'].unique().tolist())
        _location_cache['states_list'] = sorted(states_df['name'].unique().tolist())
        _location_cache['cities_list'] = sorted(cities_df['name'].unique().tolist())
        _location_cache['phone_codes_dict'] = countries_df.set_index('name')['phonecode'].to_dict()
        _location_cache['iso2_dict'] = countries_df.set_index('name')['iso2'].to_dict()

        return None  # Success

    except FileNotFoundError as e:
        abs_path = os.path.abspath(e.filename)
        return f"Fatal Error: Location data file not found. The application is looking for '{os.path.basename(e.filename)}' at this exact location: {abs_path}. Please ensure the file exists and the name is correct."
    except KeyError as e:
        return f"Fatal Error: A required column {e} was not found. Please check your CSV files. `countries.csv` needs 'name', 'phonecode', and 'iso2'. `states.csv` needs 'name'. `cities.csv` needs 'name'."
    except Exception as e:
        return f"An unexpected error occurred while loading location data: {e}"

def get_countries():
    """Returns a sorted list of all country names."""
    return _location_cache.get('countries_list', [])

def get_country_code(country_name):
    """Returns the phone code for a given country name."""
    if country_name and country_name != "Select...":
        code = _location_cache.get('phone_codes_dict', {}).get(country_name)
        # Check for valid, non-null code to prevent errors with NaN values
        if pd.notna(code):
            code_str = ''.join(filter(str.isdigit, str(code)))
            return f"+{code_str}"
        return ""
    return ""

def get_country_iso2(country_name: str) -> str | None:
    """Returns the ISO2 code for a given country name."""
    if country_name and country_name != "Select...":
        return _location_cache.get('iso2_dict', {}).get(country_name)
    return None

def get_states(country_name):
    """Returns a sorted list of all state names, unlinked from the country."""
    # The country_name parameter is ignored, but kept for compatibility.
    return _location_cache.get('states_list', [])

def get_cities(state_name):
    """Returns a sorted list of all city names, unlinked from the state."""
    # The state_name parameter is ignored, but kept for compatibility.
    return _location_cache.get('cities_list', [])