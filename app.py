import os
import streamlit as st
from anthropic import Anthropic
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import logging

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

        VEHICLE 1:
        Make: [make]
        Model: [model]
        Year: [year]
        Damage: [damage details]
        Injuries: [injury status]

        VEHICLE 2:
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
            'vehicles': vehicles
        }
    except Exception as e:
        logger.error(f"Error parsing Claude response: {str(e)}")
        return None

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

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    try:
        with st.spinner("Processing PDF..."):
            text_content = extract_text_from_pdf(uploaded_file)
            
            if st.button("🔍 Analyze Crash Report", use_container_width=True):
                if not text_content.strip():
                    st.error("No text could be extracted from the PDF.")
                    st.stop()
                
                with st.spinner("🔄 Analyzing crash report..."):
                    analysis = analyze_with_claude(text_content)
                    if analysis:
                        tab1, tab2 = st.tabs(["Summary View", "Detailed Report"])
                        
                        with tab1:
                            # Incident Summary Box
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
                                </style>
                            """, unsafe_allow_html=True)

                            # Extract summary and vehicle information
                            sections = analysis.split("VEHICLE")
                            summary = sections[0].replace("INCIDENT SUMMARY:", "").strip()
                            # Clean up the summary text
                            summary = summary.replace("[TextBlock(text='", "").replace("')", "").replace("\\n", " ").strip()

                            # Display Summary
                            st.subheader("📝 Incident Summary")
                            st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)
                            
                            # Display Vehicle Information
                            st.subheader("🚗 Vehicle Information")
                            col1, col2 = st.columns(2)
                            
                            # Vehicle 1
                            with col1:
                                vehicle1_info = sections[1].split("VEHICLE 2:")[0]
                                # Clean up vehicle 1 text
                                v1_clean = (vehicle1_info
                                            .replace("1:", "")
                                            .replace("\\n", " ")
                                            .replace("')", "")
                                            .replace("type='text'", "")
                                            .replace(", type='text']", "")
                                            .strip())
                                
                                # Format the cleaned text
                                formatted_v1 = (v1_clean
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
                                    # Clean up vehicle 2 text
                                    v2_clean = (vehicle2_info
                                               .replace("2:", "")
                                               .replace("\\n", " ")
                                               .replace("')", "")
                                               .replace("type='text'", "")
                                               .replace(", type='text']", "")
                                               .strip())
                                    
                                    # Format the cleaned text
                                    formatted_v2 = (v2_clean
                                                   .replace("Make:", "<br><b>Make:</b>")
                                                   .replace("Model:", "<br><b>Model:</b>")
                                                   .replace("Year:", "<br><b>Year:</b>")
                                                   .replace("Damage:", "<br><b>Damage:</b>")
                                                   .replace("Injuries:", "<br><b>Injuries:</b>"))
                                    
                                    st.markdown(f'<div class="vehicle-box">{formatted_v2}</div>', unsafe_allow_html=True)
                            
                            # Export button with some spacing
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.download_button(
                                label="📥 Export Analysis",
                                data=analysis,
                                file_name="crash_analysis.txt",
                                mime="text/plain",
                                use_container_width=True
                            )
                        
                        with tab2:
                            st.text_area("Raw PDF Content", text_content, height=300)
                    else:
                        st.error("Failed to analyze the crash report.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        logger.error(f"Error details: {str(e)}")