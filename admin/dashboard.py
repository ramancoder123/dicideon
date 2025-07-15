import streamlit as st
from admin import actions

# Define the columns to display and their desired order for a clean, consistent UI.
_DISPLAY_COLUMNS = [
    'request_timestamp', 'status', 'email', 'user_id', 'first_name', 'middle_name',
    'last_name', 'gender', 'date_of_birth', 'organization_name', 'country',
    'state', 'city', 'country_code', 'contact_number'
]

def render_dashboard():
    """Renders the admin dashboard for managing user requests."""
    st.title("Admin Dashboard: User Access Requests")

    pending_requests = actions.get_pending_requests()

    if pending_requests.empty:
        st.success("✅ No pending user requests at this time.")
        return

    st.info(f"You have {len(pending_requests)} pending request(s).")
    st.markdown("---")

    for index, request in pending_requests.iterrows():
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