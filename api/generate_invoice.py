import json
from invoicemaker import generate_invoice, send_email_with_attachment

def handler(request, context):
    try:
        if request.method != "POST":
            return {
                "statusCode": 405,
                "body": json.dumps({"error": "Method not allowed"})
            }

        data = request.json()
        to_email = data.get("to_email")
        if not to_email:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'to_email'"})
            }

        pdf_buffer = generate_invoice(data)

        send_email_with_attachment(
            subject="Your Solar Invoice",
            body=f"Dear {data['customer_name']}, please find your invoice attached.",
            to_email=to_email,
            pdf_buffer=pdf_buffer,
            filename="invoice.pdf"
        )

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Invoice sent successfully."})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

handler = handler  # Required by Vercel
