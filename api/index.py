from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from invoicemaker import generate_invoice, send_email_with_attachment
import json

app = FastAPI()

@app.post("/")
async def send_invoice(request: Request):
    try:
        data = await request.json()
        to_email = data.get("to_email")
        if not to_email:
            return JSONResponse(status_code=400, content={"error": "Missing 'to_email'"})
        
        pdf_buffer = generate_invoice(data)
        send_email_with_attachment(
            subject="Your Solar Invoice",
            body=f"Dear {data['customer_name']}, please find your invoice attached.",
            to_email=to_email,
            pdf_buffer=pdf_buffer,
            filename="invoice.pdf"
        )
        return {"message": "Invoice sent successfully"}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
