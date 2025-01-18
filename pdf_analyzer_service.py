from anthropic import Anthropic
from PyPDF2 import PdfReader
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFAnalyzer:
    """Core service for analyzing PDF crash reports using Claude AI"""
    
    def __init__(self):
        """Initialize the PDF Analyzer service"""
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        self.anthropic = Anthropic(api_key=self.api_key)

    def extract_text_from_pdf(self, pdf_file) -> str:
        """Extract text content from PDF file"""
        try:
            pdf_reader = PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                try:
                    page_text = page.extract_text()
                    # Remove or replace problematic characters
                    text += ''.join(char if ord(char) < 128 else ' ' for char in page_text)
                    text += "\n"
                except Exception as e:
                    logger.error(f"Error processing page: {str(e)}")
                    continue
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise

    def analyze_with_claude(self, text: str) -> Optional[str]:
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
Insurance Company: [insurance company name]
Insurance Policy #: [policy number]
Towing Company: [name of towing company]

VEHICLE 2:
Owner Name: [full name]
Owner Address: [complete address]
Make: [make]
Model: [model]
Year: [year]
Damage: [damage details]
Injuries: [injury status]
Insurance Company: [insurance company name]
Insurance Policy #: [policy number]
Towing Company: [name of towing company]

If any information is missing, write "Not specified"."""
            
            message = self.anthropic.messages.create(
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
            return str(message.content)
        except Exception as e:
            logger.error(f"Error analyzing with Claude: {str(e)}")
            raise

    def parse_analysis_response(self, response: str) -> Dict:
        """Parse Claude's response into structured data"""
        try:
            # Split the response into sections
            sections = response.split('\n\n')
            
            # Extract summary
            summary = next((s.replace("INCIDENT SUMMARY:", "").strip() 
                          for s in sections if "INCIDENT SUMMARY:" in s), "Not specified")
            
            # Extract crash date
            crash_date = next((s.replace("CRASH DATE:", "").strip() 
                             for s in sections if "CRASH DATE:" in s), "Not specified")
            
            # Extract vehicle information
            vehicles = []
            current_vehicle = {}
            
            for section in sections:
                if "VEHICLE" in section:
                    if current_vehicle:
                        vehicles.append(current_vehicle)
                        current_vehicle = {}
                    
                    lines = section.split('\n')
                    for line in lines:
                        if ':' in line:
                            key, value = line.split(':', 1)
                            current_vehicle[key.strip()] = value.strip()
            
            if current_vehicle:
                vehicles.append(current_vehicle)
            
            return {
                'incident_summary': summary,
                'crash_date': crash_date,
                'vehicles': vehicles
            }
        except Exception as e:
            logger.error(f"Error parsing analysis response: {str(e)}")
            raise

    def analyze_pdf(self, pdf_file) -> Dict:
        """Complete PDF analysis pipeline"""
        try:
            # Extract text from PDF
            text = self.extract_text_from_pdf(pdf_file)
            
            # Analyze with Claude
            analysis = self.analyze_with_claude(text)
            if not analysis:
                raise ValueError("Failed to get analysis from Claude")
            
            # Parse response
            result = self.parse_analysis_response(analysis)
            
            return result
        except Exception as e:
            logger.error(f"Error in PDF analysis pipeline: {str(e)}")
            raise

    def test_connection(self) -> tuple[bool, str]:
        """Test connection to Claude API"""
        try:
            test_message = self.anthropic.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=100,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True, str(test_message.content)
        except Exception as e:
            return False, str(e) 