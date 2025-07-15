import streamlit as st
from admin import actions
import pandas as pd

# Define the columns to display and their desired order for a clean, consistent UI.
_DISPLAY_COLUMNS = [
    'request_timestamp', 'status', 'email', 'user_id', 'first_name', 'middle_name',
    'last_name', 'gender', 'date_of_birth', 'organization_name', 'country',
    'state', 'city', 'country_code', 'contact_number'
]

def render_dashboard():
    """Renders the admin dashboard for managing user requests."""
    st.title("Admin Dashboard: User Access Requests")

    all_requests = actions.get_pending_requests()

    if all_requests.empty:
        st.success("✅ No pending user requests at this time.")
        return

    # --- Data Integrity Check ---
    # Convert timestamp column to datetime, coercing errors to NaT (Not a Time)
    all_requests['request_timestamp'] = pd.to_datetime(all_requests['request_timestamp'], errors='coerce')
    corrupted_mask = all_requests['request_timestamp'].isna()

    if corrupted_mask.any():
        corrupted_requests = all_requests[corrupted_mask]
        st.error(f"🚨 Found {len(corrupted_requests)} corrupted request(s) with invalid dates that are blocking the dashboard.")
        st.markdown("This usually happens due to a manual error or data-entry issue. To fix this, the corrupted entries will be deleted and the affected users will be automatically emailed to sign up again.")
        
        if st.button("Clean Up Corrupted Requests", type="primary", help="This will delete the invalid entries and notify users."):
            with st.spinner("Processing..."):
                processed_count = 0
                # Use a set to avoid processing the same email multiple times
                for email in set(corrupted_requests['email'].unique()):
                    success, message = actions.handle_corrupted_request(email)
                    if success:
                        processed_count += 1
                    print(message) # Log message to console for debugging
                
                st.success(f"Cleanup complete. Processed and removed {processed_count} corrupted request(s).")
                # Rerun the app to show the clean dashboard state
                st.rerun()
        
        # Stop the rest of the dashboard from rendering until the data is clean
        st.stop()

    # --- Add Search and Filter UI (only appears if data is clean) ---
    st.markdown("### Search & Filter Requests")
    col1, col2 = st.columns([2, 1])
    search_term = col1.text_input(
        "Search by Name, Email, or User ID",
        placeholder="e.g., John Doe, example@email.com, user123"
    )

    with col2:
        date_range = st.date_input(
            "Filter by Request Date",
            value=(all_requests['request_timestamp'].min().date(), all_requests['request_timestamp'].max().date()),
            min_value=all_requests['request_timestamp'].min().date(),
            max_value=all_requests['request_timestamp'].max().date(),
            key="admin_date_filter"
        )
    
    st.markdown("---")

    # --- Apply Filters ---
    filtered_requests = all_requests.copy()

    if search_term:
        search_fields = (
            filtered_requests['first_name'].str.cat(filtered_requests['last_name'], sep=' ', na_rep='') + ' ' +
            filtered_requests['email'] + ' ' +
            filtered_requests['user_id']
        ).str.lower()
        filtered_requests = filtered_requests[search_fields.str.contains(search_term.lower(), na=False)]

    if len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        filtered_requests = filtered_requests[
            (filtered_requests['request_timestamp'].dt.date >= start_date.date()) &
            (filtered_requests['request_timestamp'].dt.date <= end_date.date())
        ]

    st.info(f"Showing {len(filtered_requests)} of {len(all_requests)} total pending request(s).")

    if filtered_requests.empty:
        st.warning("No requests match your current filters.")
        return

    for index, request in filtered_requests.iterrows():
        with st.container():
            # Use .get() for safer access in case a column is unexpectedly missing
            st.markdown(f"#### Request from: {request.get('first_name', '')} {request.get('last_name', '')} ({request.get('email', 'N/A')})")

            # Use an expander to keep the UI clean
            with st.expander("View Full Details"):
                # Explicitly select and display columns for robustness and a clean presentation.
                details_to_show = request.reindex(_DISPLAY_COLUMNS).dropna().rename(lambda x: x.replace('_', ' ').title())
                # Use st.dataframe for a better UI, as it's scrollable and more modern than st.table.
                st.dataframe(details_to_show)

            col1, col2, _ = st.columns([1, 1, 5]) # Layout for buttons

            if col1.button("Approve", key=f"approve_{request['email']}", type="primary"):
                success, message = actions.approve_request(request['email'])
                st.toast(message, icon="✅" if success else "❌")
                st.rerun()

            if col2.button("Reject", key=f"reject_{request['email']}"):
                success, message = actions.reject_request(request['email'])
                st.toast(message, icon="⚠️" if success else "❌")
                st.rerun()
            st.markdown("---")