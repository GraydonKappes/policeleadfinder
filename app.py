import os
import streamlit as st
from anthropic import Anthropic
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

api_key = st.secrets["ANTHROPIC_API_KEY"]
if not api_key:
    st.error("No API key found in Streamlit secrets.")
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
        # Sanitize text before sending to Claude
        sanitized_text = ''.join(char if ord(char) < 128 else ' ' for char in text)
        
        message = anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4096,
            temperature=0,
            system="You are a helpful assistant that analyzes documents and provides detailed summaries.",
            messages=[
                {
                    "role": "user",
                    "content": sanitized_text
                }
            ]
        )
        return message.content
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
            
            if st.button("Analyze with Claude"):
                if not text_content.strip():
                    st.error("No text could be extracted from the PDF.")
                    st.stop()
                    
                with st.spinner("Getting analysis from Claude..."):
                    analysis = analyze_with_claude(text_content)
                    if analysis:
                        st.write("### Analysis Results")
                        st.write(analysis)
                    else:
                        st.error("Failed to get analysis from Claude.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        logger.error(f"Error details: {str(e)}") 