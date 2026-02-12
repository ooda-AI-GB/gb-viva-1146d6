import os
import uuid
import uvicorn
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Request, Form, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from xhtml2pdf import pisa
from starlette.middleware.sessions import SessionMiddleware

# --- Configuration ---
DATA_DIR = "data"
DB_PATH = os.path.join(DATA_DIR, "invoices.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Database Setup ---
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String, index=True)
    client_email = Column(String)
    description = Column(String)
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    filename = Column(String)
    status = Column(String, default="Draft") 

# Create Tables
Base.metadata.create_all(bind=engine)

# --- Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- FastAPI App ---
app = FastAPI(title="Invoice Generator")

# Add Session Middleware for flash messages (requires a secret key)
# In production, use a secure random secret key
app.add_middleware(SessionMiddleware, secret_key="super-secret-key-change-this-in-prod")

templates = Jinja2Templates(directory="templates")

# --- Helper Functions ---

def generate_pdf(invoice_data: Invoice, template_name: str = "invoice.html") -> str:
    """
    Generates a PDF from a Jinja2 template and saves it to disk.
    Returns the filename.
    """
    # Generate unique filename
    pdf_filename = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join(DATA_DIR, pdf_filename)
    
    # Render HTML
    template = templates.env.get_template(template_name)
    html_content = template.render(invoice=invoice_data)
    
    # Convert to PDF
    with open(file_path, "wb") as pdf_file:
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
    
    if pisa_status.err:
        logger.error(f"PDF generation failed for invoice {invoice_data.id}")
        raise RuntimeError("PDF generation failed")
        
    return pdf_filename

def send_email_simulation(invoice: Invoice):
    """
    Simulates sending an email.
    """
    logger.info(f"--- EMAIL SIMULATION ---")
    logger.info(f"To: {invoice.client_email}")
    logger.info(f"Subject: Invoice #{invoice.id} from My Company Inc.")
    logger.info(f"Body: Hello {invoice.client_name}, please find your invoice attached.")
    logger.info(f"Attachment: {invoice.filename}")
    logger.info(f"--- END EMAIL SIMULATION ---")

# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    # Retrieve invoices, ordered by newest first
    invoices = db.query(Invoice).order_by(Invoice.created_at.desc()).all()
    
    # Get flash message from session if it exists
    flash_message = request.session.pop("flash_message", None)
    
    return templates.TemplateResponse(
        "dashboard.html", 
        {"request": request, "invoices": invoices, "flash_message": flash_message}
    )

@app.post("/create")
async def create_invoice(
    request: Request,
    background_tasks: BackgroundTasks,
    client_name: str = Form(...),
    client_email: str = Form(...),
    description: str = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_db)
):
    # 1. Create DB Record
    new_invoice = Invoice(
        client_name=client_name,
        client_email=client_email,
        description=description,
        amount=amount,
        status="Processing", # Temporary status
        created_at=datetime.now()
    )
    db.add(new_invoice)
    db.commit()
    db.refresh(new_invoice)
    
    try:
        # 2. Generate PDF
        pdf_filename = generate_pdf(new_invoice)
        
        # Update record with filename and status
        new_invoice.filename = pdf_filename
        new_invoice.status = "Sent"
        db.commit()
        
        # 3. Simulate Email (logging)
        # We run this synchronously here for simplicity in this logic flow, 
        # or we could use background_tasks.add_task(send_email_simulation, new_invoice)
        # but the prompt implies immediate action/feedback.
        send_email_simulation(new_invoice)
        
        # Set flash message
        request.session["flash_message"] = f"Invoice successfully created and sent to {client_email}"
        
    except Exception as e:
        logger.error(f"Error processing invoice: {e}")
        new_invoice.status = "Error"
        db.commit()
        request.session["flash_message"] = "Error generating invoice. Please check logs."

    return RedirectResponse(url="/", status_code=303)

@app.get("/download/{invoice_id}")
async def download_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice or not invoice.filename:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    file_path = os.path.join(DATA_DIR, invoice.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF file missing")
        
    return FileResponse(
        file_path, 
        media_type="application/pdf", 
        filename=f"Invoice_{invoice_id}.pdf"
    )

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
