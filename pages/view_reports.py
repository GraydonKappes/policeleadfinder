import streamlit as st
from database import SessionLocal
from db_operations import get_filtered_crashes, create_case_for_vehicle
from datetime import datetime, date, timedelta
from app import reset_session_state
from database import Vehicle, Case
from sqlalchemy.orm import Session

st.title("View Crash Reports")

# Calculate default dates (last 14 days)
end_date = date.today()
start_date = end_date - timedelta(days=14)

# Calculate default years (last 10 years)
current_year = datetime.now().year
default_min_year = current_year - 10

# Date range filter
st.subheader("Filter by Crash Date")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input(
        "Start Date", 
        value=start_date,
        min_value=date(2000,1,1),
        format="MM/DD/YYYY"
    )
with col2:
    end_date = st.date_input(
        "End Date",
        value=end_date,
        format="MM/DD/YYYY"
    )

# Year range filter
st.subheader("Filter by Vehicle Year")
col1, col2 = st.columns(2)
with col1:
    min_year = st.number_input("Min Year", min_value=1900, max_value=datetime.now().year, value=default_min_year)
with col2:
    max_year = st.number_input("Max Year", min_value=1900, max_value=datetime.now().year, value=current_year)

# Initialize database connection
db = SessionLocal()
try:
    # If filter button is clicked, use filtered results
    if st.button("Apply Filters"):
        reset_session_state()
        crashes = get_filtered_crashes(
            db, 
            year_range=(min_year, max_year),
            date_range=(start_date, end_date)
        )
    else:
        # Otherwise show crashes from last 14 days by default
        crashes = get_filtered_crashes(
            db,
            year_range=(default_min_year, current_year),
            date_range=(start_date, end_date)
        )
    
    if not crashes:
        st.info("No crash reports found matching the criteria.")
    else:
        for crash in crashes:
            with st.expander(f"Crash on {crash.crash_date} - {crash.filename}"):
                st.write("**Summary:**", crash.incident_summary)
                st.write("**Vehicles:**")
                for vehicle in crash.vehicles:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"""
                        Vehicle {vehicle.vehicle_number}:
                        - Owner: {vehicle.owner_name}
                        - Make: {vehicle.make}
                        - Model: {vehicle.model}
                        - Year: {vehicle.year}
                        - Damage: {vehicle.damage}
                        - Injuries: {vehicle.injuries}
                        """)
                    with col2:
                        if not hasattr(vehicle, 'case') or vehicle.case is None:
                            if st.button("Create Case", key=f"create_case_{vehicle.id}"):
                                try:
                                    case = create_case_for_vehicle(db, vehicle.id)
                                    st.success(f"Case created with {case.priority.value} priority!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error creating case: {str(e)}")
                        else:
                            st.info(f"Case exists - {vehicle.case.status.value}")
                            st.write(f"Priority: {vehicle.case.priority.value}")
finally:
    db.close() 