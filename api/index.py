from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from invoicemaker import generate_invoice, send_email_with_attachment
import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/")
async def send_invoice(request: Request):
    try:
        logger.debug("Request received")
        
        data = await request.json()
        logger.debug(f"Request data: {data}")
        
        to_email = data.get("to_email")
        if not to_email:
            logger.error("Missing to_email")
            return JSONResponse(status_code=400, content={"error": "Missing 'to_email'"})
        
        logger.debug("Generating invoice...")
        pdf_buffer = generate_invoice(data)
        logger.debug("Invoice generated successfully")
        
        logger.debug("Sending email...")
        send_email_with_attachment(
            subject="Your Solar Invoice",
            body=f"Dear {data['customer_name']}, please find your invoice attached.",
            to_email=to_email,
            pdf_buffer=pdf_buffer,
            filename="invoice.pdf"
        )
        logger.debug("Email sent successfully")
        
        return {"message": "Invoice sent successfully"}

    except Exception as e:
        logger.error(f"Error in endpoint: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})