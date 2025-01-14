from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, extract
from datetime import datetime
from database import CrashReport, Vehicle, INJURY_STATUSES

def save_crash_report(db: Session, report_data: dict):
    # Check if report already exists
    existing_report = db.query(CrashReport).filter(
        CrashReport.filename == report_data["filename"],
        CrashReport.crash_date == datetime.strptime(report_data["crash_date"], "%m/%d/%Y").date()
    ).first()
    
    if existing_report:
        return existing_report  # Skip if already exists
    
    # Create crash report
    crash_report = CrashReport(
        filename=report_data["filename"],
        incident_summary=report_data["incident_summary"],
        crash_date=datetime.strptime(report_data["crash_date"], "%m/%d/%Y").date()
    )
    
    db.add(crash_report)
    db.flush()

    # Add vehicles
    for vehicle_data in [report_data.get("vehicle1"), report_data.get("vehicle2")]:
        if vehicle_data:
            # Ensure injury text matches enum exactly
            injury_text = vehicle_data.get("injuries", "Not specified")
            # Normalize the injury text to match enum values
            if injury_text not in INJURY_STATUSES:
                injury_text = 'Not specified'
            
            vehicle = Vehicle(
                crash_report_id=crash_report.id,
                vehicle_number=1 if vehicle_data == report_data.get("vehicle1") else 2,
                owner_name=vehicle_data["owner_name"],
                owner_address=vehicle_data["owner_address"],
                make=vehicle_data["make"],
                model=vehicle_data["model"],
                year=vehicle_data["year"],
                damage=vehicle_data["damage"],
                injuries=injury_text,
                insurance_company=vehicle_data.get("insurance_company"),
                insurance_policy_number=vehicle_data.get("insurance_policy_number"),
                towing_company=vehicle_data.get("towing_company")
            )
            db.add(vehicle)
    db.commit()
    return crash_report

def get_filtered_crashes(db: Session, year_range=None, date_range=None):
    query = db.query(CrashReport).distinct()
    
    if year_range:
        min_year, max_year = year_range
        query = query.join(Vehicle).filter(
            Vehicle.year.between(min_year, max_year)
        )
    
    if date_range:
        start_date, end_date = date_range
        query = query.filter(
            CrashReport.crash_date.between(start_date, end_date)
        )
    
    # Add ordering by crash_date in descending order
    query = query.order_by(CrashReport.crash_date.desc())
    
    return query.all() 