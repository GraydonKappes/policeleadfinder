from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import uvicorn
import logging
from pdf_analyzer_service import PDFAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PDF Analyzer API",
    description="API for analyzing crash report PDFs using Claude AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize PDF Analyzer
pdf_analyzer = PDFAnalyzer()

# Pydantic models for request/response validation
class Vehicle(BaseModel):
    owner_name: str
    owner_address: str
    make: str
    model: str
    year: Optional[int]
    damage: str
    injuries: str
    insurance_company: Optional[str]
    insurance_policy_number: Optional[str]
    towing_company: Optional[str]

class AnalysisResponse(BaseModel):
    incident_summary: str
    crash_date: str
    vehicles: List[Dict]

@app.get("/health")
async def health_check():
    """Check if the service is healthy and Claude API is accessible"""
    try:
        success, message = pdf_analyzer.test_connection()
        if success:
            return {"status": "healthy", "claude_api": "connected"}
        return {"status": "degraded", "claude_api": "error", "message": message}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_pdf(file: UploadFile = File(...)):
    """Analyze a PDF crash report"""
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        # Read the uploaded file
        pdf_contents = await file.read()
        
        # Analyze the PDF
        result = pdf_analyzer.analyze_pdf(pdf_contents)
        
        return AnalysisResponse(
            incident_summary=result['incident_summary'],
            crash_date=result['crash_date'],
            vehicles=result['vehicles']
        )
    except Exception as e:
        logger.error(f"Error analyzing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/batch")
async def analyze_pdfs(files: List[UploadFile] = File(...)):
    """Analyze multiple PDF crash reports"""
    try:
        results = []
        for file in files:
            if not file.filename.endswith('.pdf'):
                raise HTTPException(
                    status_code=400, 
                    detail=f"File {file.filename} must be a PDF"
                )
            
            # Read and analyze each PDF
            pdf_contents = await file.read()
            result = pdf_analyzer.analyze_pdf(pdf_contents)
            results.append({
                "filename": file.filename,
                **result
            })
        
        return {"analyses": results}
    except Exception as e:
        logger.error(f"Error in batch analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api_service:app", host="0.0.0.0", port=8000, reload=True) 