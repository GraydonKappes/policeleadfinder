import os
import streamlit as st
from anthropic import Anthropic
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import logging
import json

# Load environment variables
load_dotenv()

# Check if we're running on Streamlit Cloud
is_streamlit_cloud = os.environ.get('STREAMLIT_RUNTIME_ENV') == 'cloud'

# Get API key based on environment
api_key = None
if is_streamlit_cloud:
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception as e:
        st.error("No API key found in Streamlit secrets.")
        st.stop()
else:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        st.error("No API key found in .env file. Please add ANTHROPIC_API_KEY to your .env file.")
        st.stop()

# Initialize Anthropic client
anthropic = Anthropic(api_key=api_key)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_file):
    """Extract text content from uploaded PDF file"""
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        try:
            page_text = page.extract_text()
            # Remove or replace problematic characters
            text += ''.join(char if ord(char) < 128 else ' ' for char in page_text)
            text += "\n"
        except Exception as e:
            st.error(f"Error processing page: {str(e)}")
            continue
    return text

def analyze_with_claude(text):
    """Send text to Claude for analysis"""
    try:
        sanitized_text = ''.join(char if ord(char) < 128 else ' ' for char in text)
        
        system_prompt = """You are a specialized assistant analyzing automobile crash records.
        Analyze the provided crash report and return ONLY the following information in this EXACT format:

        INCIDENT SUMMARY:
        [2-3 sentence summary of the crash]

        CRASH DATE: [MM/DD/YYYY format - date only, no time]

        VEHICLE 1:
        Owner Name: [full name]
        Owner Address: [complete address]
        Make: [make]
        Model: [model]
        Year: [year]
        Damage: [damage details]
        Injuries: [injury status]

        VEHICLE 2:
        Owner Name: [full name]
        Owner Address: [complete address]
        Make: [make]
        Model: [model]
        Year: [year]
        Damage: [damage details]
        Injuries: [injury status]

        If any information is missing, write "Not specified"."""
        
        message = anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4096,
            temperature=0,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze this crash report and extract the requested information: \n\n{sanitized_text}"
                }
            ]
        )
        # Return the actual content from the message
        return str(message.content)
    except Exception as e:
        st.error(str(e))
        return None

def test_claude_connection():
    try:
        test_message = anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": "Hi"  # Simpler test message
                }
            ]
        )
        return True, test_message.content
    except Exception as e:
        return False, str(e)

def parse_claude_response(response):
    """Parse Claude's response into structured data"""
    try:
        # Split the response into sections
        sections = response.split("-------------------")
        
        # Parse incident summary
        summary = sections[1].replace("INCIDENT SUMMARY", "").strip()
        
        # Parse crash date
        try:
            crash_date = sections[0].split("CRASH DATE:")[1].split("VEHICLE")[0].strip()
            crash_date = clean_field_value(crash_date)
        except:
            crash_date = "Not specified"
        
        # Parse vehicle information
        vehicles_section = sections[3].replace("VEHICLE INFORMATION", "").strip()
        vehicles = []
        
        # Split by "Vehicle" and process each vehicle entry
        vehicle_entries = vehicles_section.split("Vehicle")[1:]  # Skip the first empty split
        
        for entry in vehicle_entries:
            lines = entry.strip().split('\n')
            vehicle = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    vehicle[key.strip()] = value.strip()
            
            vehicles.append(vehicle)
            
        return {
            'summary': summary,
            'crash_date': crash_date,
            'vehicles': vehicles
        }
    except Exception as e:
        logger.error(f"Error parsing Claude response: {str(e)}")
        return None

def clean_field_value(value):
    """Clean any field value by removing common artifacts"""
    if not isinstance(value, str):
        return value
        
    cleaned = value
    artifacts = [
        "', type='text]",
        ", type='text]",
        "type='text'",
        "type=text",
        "Owner",  # Remove standalone "Owner"
        "'",  # Add single quote by itself
        ",",  # Add comma by itself
        "[TextBlock(text='",
        "')",
        ")]",
        "\\n"
    ]
    
    for artifact in artifacts:
        cleaned = cleaned.replace(artifact, "")
    
    return cleaned.strip()

def clean_display_text(text):
    """Clean text for display purposes"""
    return (text
            .replace("', type='text]", "")
            .replace(", type='text]", "")
            .replace("[TextBlock(text='", "")
            .replace("type='text'", "")
            .replace("'", "")  # Add single quote removal
            .replace(",", "")  # Add comma removal
            .replace("')", "")
            .replace(")]", "")
            .replace("\\n", " ")
            .strip())

def format_analysis_for_json(analysis_list):
    """Convert analyses into structured JSON format"""
    formatted_data = []
    for filename, analysis in analysis_list:
        sections = analysis.split("VEHICLE")
        
        # Clean summary text
        summary = sections[0].split("CRASH DATE:")[0].replace("INCIDENT SUMMARY:", "").strip()
        summary = clean_field_value(summary)
        
        # Extract crash date
        try:
            crash_date = sections[0].split("CRASH DATE:")[1].split("VEHICLE")[0].strip()
            crash_date = clean_field_value(crash_date)
        except:
            crash_date = "Not specified"
        
        # Process Vehicle 1
        vehicle1_info = sections[1].split("VEHICLE 2:")[0] if len(sections) > 1 else ""
        vehicle1 = {}
        
        # Extract and clean each field for Vehicle 1
        field_mappings = {
            "Make:": "make",
            "Model:": "model",
            "Year:": "year",
            "Damage:": "damage",
            "Injuries:": "injuries",
            "Owner Name:": "owner_name",
            "Owner Address:": "owner_address"
        }
        
        for field_label, field_key in field_mappings.items():
            if field_label in vehicle1_info:
                next_field = next((f for f in field_mappings.keys() if f in vehicle1_info.split(field_label)[1]), None)
                value = vehicle1_info.split(field_label)[1].split(next_field)[0].strip() if next_field else vehicle1_info.split(field_label)[1].strip()
                
                # Clean the value
                cleaned_value = clean_field_value(value)
                
                # Convert year to integer if possible
                if field_key == "year":
                    try:
                        vehicle1[field_key] = int(cleaned_value)
                    except ValueError:
                        vehicle1[field_key] = cleaned_value
                else:
                    vehicle1[field_key] = cleaned_value
        
        # Process Vehicle 2 using the same logic
        vehicle2 = {}
        if len(sections) > 2:
            vehicle2_info = sections[2]
            
            for field_label, field_key in field_mappings.items():
                if field_label in vehicle2_info:
                    next_field = next((f for f in field_mappings.keys() if f in vehicle2_info.split(field_label)[1]), None)
                    value = vehicle2_info.split(field_label)[1].split(next_field)[0].strip() if next_field else vehicle2_info.split(field_label)[1].strip()
                    
                    # Clean the value
                    cleaned_value = clean_field_value(value)
                    
                    # Convert year to integer if possible
                    if field_key == "year":
                        try:
                            vehicle2[field_key] = int(cleaned_value)
                        except ValueError:
                            vehicle2[field_key] = cleaned_value
                    else:
                        vehicle2[field_key] = cleaned_value
        
        report_data = {
            "filename": filename,
            "incident_summary": summary,
            "crash_date": crash_date,
            "vehicle1": vehicle1,
            "vehicle2": vehicle2 if vehicle2 else None
        }
        formatted_data.append(report_data)
    
    return formatted_data

# Streamlit UI
st.title("PDF Analysis with Claude AI")
st.write("Upload a PDF file to get an AI-powered analysis")

if st.button("Test Claude Connection"):
    success, message = test_claude_connection()
    if success:
        st.success(f"Claude says: {message}")
    else:
        st.error(f"Failed to connect to Claude: {message}")

st.divider()  # Add a visual separator between the test button and file uploader

uploaded_files = st.file_uploader("Choose PDF files", type="pdf", accept_multiple_files=True)

if uploaded_files:
    try:
        all_analyses = []
        
        for uploaded_file in uploaded_files:
            with st.spinner(f"Processing {uploaded_file.name}..."):
                text_content = extract_text_from_pdf(uploaded_file)
                
                if not text_content.strip():
                    st.error(f"No text could be extracted from {uploaded_file.name}")
                    continue
                
                with st.spinner(f"🔄 Analyzing {uploaded_file.name}..."):
                    analysis = analyze_with_claude(text_content)
                    if analysis:
                        all_analyses.append((uploaded_file.name, analysis))
                    else:
                        st.error(f"Failed to analyze {uploaded_file.name}")

        if all_analyses:
            # Add styling
            st.markdown("""
                <style>
                .summary-box {
                    background-color: #f0f2f6;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 10px 0;
                }
                .vehicle-box {
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 10px 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .report-separator {
                    margin: 40px 0;
                    border-top: 2px solid #e0e0e0;
                }
                </style>
            """, unsafe_allow_html=True)

            # Process each analysis
            for idx, (filename, analysis) in enumerate(all_analyses):
                if idx > 0:
                    st.markdown('<div class="report-separator"></div>', unsafe_allow_html=True)
                
                st.subheader(f"📄 Report: {filename}")
                
                # Extract summary and crash date
                sections = analysis.split("VEHICLE")
                summary_section = sections[0]
                summary = summary_section.split("CRASH DATE:")[0].replace("INCIDENT SUMMARY:", "").strip()
                summary = summary.replace("[TextBlock(text='", "").replace("')", "").replace("\\n", " ").strip()

                try:
                    crash_date = summary_section.split("CRASH DATE:")[1].strip()
                    crash_date = clean_display_text(crash_date)
                except:
                    crash_date = "Not specified"

                # Display Summary
                st.subheader("📝 Incident Summary")
                st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)

                # Display Crash Date
                st.subheader("📅 Crash Date")
                st.markdown(f'<div class="summary-box">{crash_date}</div>', unsafe_allow_html=True)
                
                # Display Vehicle Information
                st.subheader("🚗 Vehicle Information")
                col1, col2 = st.columns(2)
                
                # Vehicle 1
                with col1:
                    vehicle1_info = sections[1].split("VEHICLE 2:")[0]
                    v1_clean = (vehicle1_info
                                .replace("1:", "")
                                .replace("\\n", " ")
                                .replace("')", "")
                                .replace("type='text'", "")
                                .replace(", type='text']", "")
                                .strip())
                    
                    formatted_v1 = (v1_clean
                                   .replace("Owner Name:", "<br><b>Owner Name:</b>")
                                   .replace("Owner Address:", "<br><b>Owner Address:</b>")
                                   .replace("Make:", "<br><b>Make:</b>")
                                   .replace("Model:", "<br><b>Model:</b>")
                                   .replace("Year:", "<br><b>Year:</b>")
                                   .replace("Damage:", "<br><b>Damage:</b>")
                                   .replace("Injuries:", "<br><b>Injuries:</b>"))
                    
                    st.markdown(f'<div class="vehicle-box">{formatted_v1}</div>', unsafe_allow_html=True)
                
                # Vehicle 2
                with col2:
                    if len(sections) > 2:
                        vehicle2_info = sections[2]
                        v2_clean = clean_display_text(vehicle2_info.replace("2:", ""))
                        
                        formatted_v2 = (v2_clean
                                       .replace("Owner Name:", "<br><b>Owner Name:</b>")
                                       .replace("Owner Address:", "<br><b>Owner Address:</b>")
                                       .replace("Make:", "<br><b>Make:</b>")
                                       .replace("Model:", "<br><b>Model:</b>")
                                       .replace("Year:", "<br><b>Year:</b>")
                                       .replace("Damage:", "<br><b>Damage:</b>")
                                       .replace("Injuries:", "<br><b>Injuries:</b>"))
                        
                        st.markdown(f'<div class="vehicle-box">{formatted_v2}</div>', unsafe_allow_html=True)

            # Export all analyses as JSON
            st.markdown("<br>", unsafe_allow_html=True)
            json_data = format_analysis_for_json(all_analyses)
            json_string = json.dumps(json_data, indent=2)  # Added indent=2 for pretty printing
            
            st.download_button(
                label="📥 Export All Analyses (JSON)",
                data=json_string,
                file_name="crash_analyses.json",
                mime="application/json",
                use_container_width=True
            )
                    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        logger.error(f"Error details: {str(e)}")