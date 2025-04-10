from flask import Flask, request, send_file
from invoicemaker import generate_invoice
import io

app = Flask(__name__)

@app.route('/generate-invoice', methods=['POST'])
def generate_invoice_api():
    data = request.json

    # Call the generate_invoice function from invoicemaker
    pdf_buffer = generate_invoice(data)

    # Return the PDF as a response
    return send_file(
        io.BytesIO(pdf_buffer.getvalue()),
        mimetype='application/pdf',
        as_attachment=True,
        download_name='invoice.pdf'
    )

if __name__ == '__main__':
    app.run(debug=True)