import streamlit as st
from database import SessionLocal
from db_operations import get_filtered_crashes
from datetime import datetime, date

st.title("View Crash Reports")

# Date range filter
st.subheader("Filter by Crash Date")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", min_value=date(2000,1,1))
with col2:
    end_date = st.date_input("End Date")

# Year range filter
st.subheader("Filter by Vehicle Year")
col1, col2 = st.columns(2)
with col1:
    min_year = st.number_input("Min Year", min_value=1900, max_value=datetime.now().year)
with col2:
    max_year = st.number_input("Max Year", min_value=1900, max_value=datetime.now().year, value=datetime.now().year)

if st.button("Apply Filters"):
    db = SessionLocal()
    try:
        crashes = get_filtered_crashes(
            db, 
            year_range=(min_year, max_year),
            date_range=(start_date, end_date)
        )
        
        for crash in crashes:
            with st.expander(f"Crash on {crash.crash_date} - {crash.filename}"):
                st.write("**Summary:**", crash.incident_summary)
                st.write("**Vehicles:**")
                for vehicle in crash.vehicles:
                    st.write(f"""
                    Vehicle {vehicle.vehicle_number}:
                    - Owner: {vehicle.owner_name}
                    - Make: {vehicle.make}
                    - Model: {vehicle.model}
                    - Year: {vehicle.year}
                    - Damage: {vehicle.damage}
                    - Injuries: {vehicle.injuries}
                    """)
    finally:
        db.close() 