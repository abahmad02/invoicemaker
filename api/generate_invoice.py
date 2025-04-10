from invoicemaker import generate_invoice, send_email_with_attachment

def handler(request, context):
    if request.method != "POST":
        return {"statusCode": 405, "body": "Method not allowed"}

    data = request.json()
    to_email = data.get("to_email")

    if not to_email:
        return {"statusCode": 400, "body": "Missing to_email"}

    pdf_buffer = generate_invoice(data)
    send_email_with_attachment(
        subject="Your Solar Invoice",
        body="Please find your invoice attached.",
        to_email=to_email,
        pdf_buffer=pdf_buffer,
        filename="invoice.pdf"
    )

    return {"statusCode": 200, "body": "Invoice sent successfully!"}
