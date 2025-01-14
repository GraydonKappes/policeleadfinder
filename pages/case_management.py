import streamlit as st
from database import SessionLocal, Case, CaseStatus, Vehicle
from datetime import datetime

st.title("Case Management")

# Initialize database connection
db = SessionLocal()

try:
    # Get all cases
    cases = db.query(Case).join(Vehicle).order_by(Case.created_at.desc()).all()
    
    if not cases:
        st.info("No active cases found.")
    else:
        for case in cases:
            with st.expander(f"{case.vehicle.make} {case.vehicle.model} - {case.status.value}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"""
                    **Vehicle Details:**
                    - Owner: {case.vehicle.owner_name}
                    - Vehicle: {case.vehicle.year} {case.vehicle.make} {case.vehicle.model}
                    - Damage: {case.vehicle.damage}
                    - Priority: {case.priority.value}
                    """)
                
                with col2:
                    new_status = st.selectbox(
                        "Status",
                        options=[status for status in CaseStatus],
                        key=f"status_{case.id}",
                        index=[status for status in CaseStatus].index(case.status),
                        format_func=lambda x: x.value
                    )
                    
                    if new_status != case.status:
                        case.status = new_status
                        case.updated_at = datetime.utcnow()
                        db.commit()
                        st.rerun()
                
                # Notes section
                notes = st.text_area(
                    "Case Notes",
                    value=case.notes or "",
                    key=f"notes_{case.id}"
                )
                
                if notes != case.notes:
                    case.notes = notes
                    case.updated_at = datetime.utcnow()
                    db.commit()

finally:
    db.close() 