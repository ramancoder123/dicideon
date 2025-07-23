import pandas as pd
import os
import streamlit as st
import logging

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
    Loads and caches location data from CSV files. It establishes relationships
    between countries, states, and cities to support cascading dropdowns.
    Returns an error message string on failure, otherwise None.
    """
    if _location_cache:  # Data already loaded
      return None

    try:
        # 1. Load countries for dropdown and phone codes
        country_cols = ['name', 'phonecode', 'iso2']
        countries_df = pd.read_csv(COUNTRIES_FILE, usecols=country_cols, dtype={'phonecode': str, 'iso2': str})
        countries_df.dropna(subset=['name', 'iso2'], inplace=True)
        # Normalize country names to handle inconsistencies (e.g., 'india' vs 'India')
        # Also standardize iso2 codes to uppercase for reliable joins.
        countries_df['name'] = countries_df['name'].str.strip().str.title()
        countries_df['iso2'] = countries_df['iso2'].str.strip().str.upper()
        logging.info(f"LOCATION_HANDLER: Loaded {len(countries_df)} countries from countries.csv.")

        # 2. Load states, using the 'country_code' column for linking.
        state_cols = ['name', 'country_code']
        states_df = pd.read_csv(STATES_FILE, usecols=state_cols, dtype=str)
        states_df.dropna(subset=['name', 'country_code'], inplace=True)
        logging.info(f"LOCATION_HANDLER: Loaded {len(states_df)} total state entries from states.csv.")
        # Normalize state names and country codes for the join.
        states_df['name'] = states_df['name'].str.strip().str.title()
        states_df['country_code'] = states_df['country_code'].str.strip().str.upper()

        # --- Data Linking: Join states to countries on their codes ---
        # This is the most reliable way to link the two datasets.
        # An 'inner' join automatically filters out states with no matching country code.
        merged_states_df = pd.merge(
            states_df,
            countries_df[['name', 'iso2']],
            left_on='country_code',
            right_on='iso2',
            how='inner'
        )
        # Rename columns for clarity after the merge.
        merged_states_df.rename(columns={'name_x': 'state_name', 'name_y': 'country_name'}, inplace=True)
        logging.info(f"LOCATION_HANDLER: Successfully linked {len(merged_states_df)} states to countries using their codes.")
        if len(merged_states_df) == 0 and len(states_df) > 0:
            logging.error("LOCATION_HANDLER: CRITICAL - No states could be linked. Check that 'country_code' in states.csv matches 'iso2' in countries.csv.")

        # 3. Load and link cities
        city_cols = ['name', 'state_name']
        cities_df = pd.read_csv(CITIES_FILE, usecols=city_cols, dtype=str)
        cities_df.dropna(subset=['name', 'state_name'], inplace=True)
        logging.info(f"LOCATION_HANDLER: Loaded {len(cities_df)} total city entries from cities.csv.")
        cities_df['name'] = cities_df['name'].str.strip().str.title()
        cities_df['state_name'] = cities_df['state_name'].str.strip().str.title()

        # --- Data Cleaning & Linking for Cities ---
        # This step makes the app resilient to data mismatches.
        # It filters cities to only those that belong to a state we successfully linked.
        valid_states = set(merged_states_df['state_name'])
        original_city_count = len(cities_df)
        
        # Keep only cities whose state_name is in our list of valid, linked states.
        cities_df = cities_df[cities_df['state_name'].isin(valid_states)]
        
        if len(cities_df) < original_city_count:
            logging.warning(f"LOCATION_HANDLER: Discarded {original_city_count - len(cities_df)} cities because their state name in 'cities.csv' did not match any valid state from 'states.csv'. This is not a fatal error.")

        # 4. Pre-process for fast lookups
        _location_cache['countries_list'] = sorted(countries_df['name'].unique().tolist())
        _location_cache['phone_codes_dict'] = countries_df.set_index('name')['phonecode'].to_dict()
        _location_cache['iso2_dict'] = countries_df.set_index('name')['iso2'].to_dict()

        # Create the final mappings for the dropdowns from our merged data.
        states_by_country_dict = merged_states_df.groupby('country_name')['state_name'].apply(list).to_dict()
        _location_cache['states_by_country'] = states_by_country_dict
        _location_cache['cities_by_state'] = cities_df.groupby('state_name')['name'].apply(list).to_dict()

        if not states_by_country_dict:
            logging.error("LOCATION_HANDLER: CRITICAL - The 'states_by_country' mapping is EMPTY. The dropdown will not work.")
        else:
            logging.info(f"LOCATION_HANDLER: Successfully created state mapping for {len(states_by_country_dict)} countries.")

        return None  # Success

    except FileNotFoundError as e:
        abs_path = os.path.abspath(e.filename)
        return f"Fatal Error: Location data file not found. The application is looking for '{os.path.basename(e.filename)}' at this exact location: {abs_path}. Please ensure the file exists and the name is correct."
    except KeyError as e:
        return f"Fatal Error: A required column {e} was not found. Please check your CSV files. `countries.csv` needs 'name', 'phonecode', 'iso2'. `states.csv` needs 'name' and 'country_code'. `cities.csv` needs 'name' and 'state_name'."
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

def get_states(country_name: str | None) -> list[str]:
    """
    Returns a list of states filtered by country name.
    If no country_name is provided or it's the default 'Select...', returns an empty list.
    """
    if not country_name or country_name == "Select...":
        return []  # No states if no country selected.
    return sorted(_location_cache.get('states_by_country', {}).get(country_name, []))

def get_cities(state_name: str | None) -> list[str]:
    """
    Returns a list of cities filtered by state name.
    If no state_name is provided or it's the default 'Select...', returns an empty list.
    """
    if not state_name or state_name == "Select...":
        return []  # No cities if no state selected
    return sorted(_location_cache.get('cities_by_state', {}).get(state_name, []))

# ------------------- STREAMLIT UI CODE -------------------
def main():
    st.title("Location Selector")
    
    # Initialize session state for selections
    if 'country' not in st.session_state:
        st.session_state.country = "Select..."
    if 'state' not in st.session_state:
        st.session_state.state = "Select..."
    if 'city' not in st.session_state:
        st.session_state.city = "Select..."
    
    # Load location data with error handling
    error_msg = load_location_data()
    if error_msg:
        st.error(error_msg)
        st.stop()
    
    # Country selection
    countries = get_countries()
    st.session_state.country = st.selectbox(
        "Select Country", 
        ["Select..."] + countries,
        index=0 if st.session_state.country == "Select..." else countries.index(st.session_state.country)+1
    )
    
    # Reset state/city when country changes
    if st.session_state.country == "Select...":
        st.session_state.state = "Select..."
        st.session_state.city = "Select..."
    
    # State selection (only show if country is selected)
    if st.session_state.country and st.session_state.country != "Select...":
        states = get_states(st.session_state.country)
        st.session_state.state = st.selectbox(
            "Select State", 
            ["Select..."] + states,
            index=0 if st.session_state.state == "Select..." else states.index(st.session_state.state)+1
        )
        
        # Reset city when state changes
        if st.session_state.state == "Select...":
            st.session_state.city = "Select..."
    
    # City selection (only show if state is selected)
    if st.session_state.state and st.session_state.state != "Select...":
        cities = get_cities(st.session_state.state)
        st.session_state.city = st.selectbox(
            "Select City", 
            ["Select..."] + cities,
            index=0 if st.session_state.city == "Select..." else cities.index(st.session_state.city)+1
        )
    
    # Display selections
    if st.session_state.country != "Select...":
        st.subheader("Your Selections:")
        st.write(f"Country: {st.session_state.country}")
        
        if st.session_state.state != "Select...":
            st.write(f"State: {st.session_state.state}")
            
            if st.session_state.city != "Select...":
                st.write(f"City: {st.session_state.city}")
        
        # Show country phone code
        phone_code = get_country_code(st.session_state.country)
        if phone_code:
            st.write(f"Country Phone Code: {phone_code}")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    main()