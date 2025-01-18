import requests
import os
from pathlib import Path
import logging
import time
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API base URL
BASE_URL = "http://localhost:8000"
MAX_RETRIES = 5
RETRY_DELAY = 2  # seconds

def wait_for_service():
    """Wait for the API service to be ready"""
    for i in range(MAX_RETRIES):
        try:
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                logger.info("Service is ready!")
                return True
        except requests.exceptions.ConnectionError:
            logger.info(f"Service not ready, attempt {i+1}/{MAX_RETRIES}...")
            time.sleep(RETRY_DELAY)
    return False

def test_health():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        logger.info(f"Health check response: {response.json()}")
        assert response.status_code == 200
        return True
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return False

def test_pdf_analysis(pdf_path):
    """Test PDF analysis endpoint"""
    try:
        # Ensure file exists
        if not Path(pdf_path).exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return False
        
        # Prepare file for upload
        with open(pdf_path, 'rb') as f:
            files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
            
            # Send request
            response = requests.post(
                f"{BASE_URL}/analyze",
                files=files
            )
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            logger.info("Analysis successful!")
            logger.info(f"Incident Summary: {result['incident_summary']}")
            logger.info(f"Crash Date: {result['crash_date']}")
            logger.info(f"Number of vehicles: {len(result['vehicles'])}")
            return True
        else:
            logger.error(f"Analysis failed: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error testing PDF analysis: {str(e)}")
        return False

def test_batch_analysis(pdf_directory):
    """Test batch PDF analysis endpoint"""
    try:
        # Get all PDFs in directory
        pdf_files = list(Path(pdf_directory).glob("*.pdf"))
        if not pdf_files:
            logger.error(f"No PDF files found in {pdf_directory}")
            return False
        
        # Prepare files for upload
        files = []
        try:
            files = [
                ('files', (pdf.name, open(pdf, 'rb'), 'application/pdf'))
                for pdf in pdf_files
            ]
            
            # Send request
            response = requests.post(
                f"{BASE_URL}/analyze/batch",
                files=files
            )
            
            # Check response
            if response.status_code == 200:
                results = response.json()
                logger.info("Batch analysis successful!")
                logger.info(f"Processed {len(results['analyses'])} files")
                for analysis in results['analyses']:
                    logger.info(f"File: {analysis['filename']}")
                    logger.info(f"Incident Summary: {analysis['incident_summary']}")
                return True
            else:
                logger.error(f"Batch analysis failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing batch analysis: {str(e)}")
            return False
        finally:
            # Always close files
            for _, file_tuple in files:
                try:
                    file_tuple[1].close()
                except:
                    pass
            
    except Exception as e:
        logger.error(f"Error in batch analysis: {str(e)}")
        return False

if __name__ == "__main__":
    # Wait for service to be ready
    logger.info("Waiting for service to be ready...")
    if not wait_for_service():
        logger.error("Service failed to start! Exiting...")
        sys.exit(1)
    
    # Test health endpoint
    logger.info("Testing health endpoint...")
    if not test_health():
        logger.error("Health check failed! Stopping tests.")
        sys.exit(1)
    
    # Test single PDF analysis
    pdf_path = input("Enter path to test PDF file: ")
    logger.info("Testing single PDF analysis...")
    if not test_pdf_analysis(pdf_path):
        logger.error("Single PDF analysis failed!")
    
    # Test batch analysis
    pdf_dir = input("Enter directory containing PDF files: ")
    logger.info("Testing batch PDF analysis...")
    if not test_batch_analysis(pdf_dir):
        logger.error("Batch PDF analysis failed!") 