import os
import streamlit as st
from anthropic import Anthropic
from PyPDF2 import PdfReader
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Anthropic client
anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

def extract_text_from_pdf(pdf_file):
    """Extract text content from uploaded PDF file"""
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        try:
            page_text = page.extract_text()
            # Use UTF-8 encoding instead of ASCII
            page_text = page_text.encode('utf-8', errors='replace').decode('utf-8')
            text += page_text + "\n"
        except Exception as e:
            st.error(f"Error processing page: {str(e)}")
            continue
    return text

def analyze_with_claude(text):
    """Send text to Claude for analysis"""
    try:
        # Use UTF-8 encoding instead of ASCII
        cleaned_text = text.encode('utf-8', errors='replace').decode('utf-8')
        message = anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4096,
            temperature=0,
            system="You are a helpful assistant that analyzes documents and provides detailed summaries.",
            messages=[
                {
                    "role": "user",
                    "content": f"Please analyze this document and provide a detailed summary with key points:\n\n{cleaned_text}"
                }
            ]
        )
        return message.content
    except Exception as e:
        st.error(f"Error analyzing document: {str(e)}")
        return None

# Streamlit UI
st.title("PDF Analysis with Claude AI")
st.write("Upload a PDF file to get an AI-powered analysis")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    with st.spinner("Processing PDF..."):
        # Extract text from PDF
        text_content = extract_text_from_pdf(uploaded_file)
        
        # Get analysis from Claude
        if st.button("Analyze with Claude"):
            with st.spinner("Getting analysis from Claude..."):
                analysis = analyze_with_claude(text_content)
                st.write("### Analysis Results")
                st.write(analysis) 