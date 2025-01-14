from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, extract
from datetime import datetime
from database import CrashReport, Vehicle, INJURY_STATUSES, CasePriority, Case, CaseStatus

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

def calculate_case_priority(vehicle_damage: str, vehicle_year: int) -> CasePriority:
    current_year = datetime.now().year
    
    # Check if vehicle is less than 10 years old
    is_recent = (vehicle_year and (current_year - vehicle_year) <= 10)
    
    # Check for severe damage keywords
    severe_keywords = ['severe', 'major', 'totaled', 'extensive', 'heavy', 'significant']
    has_severe_damage = any(keyword in vehicle_damage.lower() for keyword in severe_keywords)
    
    if is_recent and has_severe_damage:
        return CasePriority.HIGH
    elif is_recent or has_severe_damage:
        return CasePriority.MEDIUM
    else:
        return CasePriority.LOW 

def create_case_for_vehicle(db: Session, vehicle_id: int) -> Case:
    try:
        # Check if case already exists
        existing_case = db.query(Case).filter(Case.vehicle_id == vehicle_id).first()
        if existing_case:
            return existing_case
        
        # Get vehicle details
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            raise ValueError("Vehicle not found")
        
        # Calculate priority
        priority = calculate_case_priority(vehicle.damage, vehicle.year)
        
        # Create new case
        case = Case(
            vehicle_id=vehicle_id,
            status=CaseStatus.NEW,
            priority=priority,
            notes=f"Initial case created for {vehicle.make} {vehicle.model} ({vehicle.year})"
        )
        
        db.add(case)
        db.commit()
        db.refresh(case)
        return case
        
    except Exception as e:
        db.rollback()
        raise e 