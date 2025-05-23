# Import the required modules
import fpdf  # For creating pdf files
import PyPDF2
import datetime  # For getting the current date
import fitz 
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import tempfile
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import math
import io
import logging

def merge_pdfs(pdf_list, output_filename):
    merged_pdf = PyPDF2.PdfWriter()

    for pdf in pdf_list:
        with open(pdf, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in range(reader.numPages):
                merged_pdf.add_page(reader.getPage(page))

    with open(output_filename, 'wb') as f:
        merged_pdf.write(f)

def add_pdf_to_middle(existing_pdf, pdf_to_add, page_number, output_filename):
    merged_pdf = PyPDF2.PdfWriter()

    with open(existing_pdf, 'rb') as f1, open(pdf_to_add, 'rb') as f2:
        existing_reader = PyPDF2.PdfReader(f1)
        pdf_to_add_reader = PyPDF2.PdfReader(f2)

        for page in range(len(existing_reader.pages)):
            if page == page_number:
                for add_page in range(len(pdf_to_add_reader.pages)):
                    merged_pdf.add_page(pdf_to_add_reader.pages[add_page])
            merged_pdf.add_page(existing_reader.pages[page])

    with open(output_filename, 'wb') as f:
        merged_pdf.write(f)


    with open(output_filename, 'wb') as f:
        merged_pdf.write(f)


import fitz  # Import the PyMuPDF library

def replace_text(input_pdf, output_pdf, replacements, zoom_factor=3.0):
    try:
        # Open input PDF
        if isinstance(input_pdf, str):
            doc = fitz.open(input_pdf)
        else:
            input_pdf.seek(0)
            doc = fitz.open(stream=input_pdf.read(), filetype="pdf")
        
        # Perform text replacements
        for page in doc:
            for placeholder, replacement in replacements.items():
                text_instances = page.search_for(placeholder)
                for inst in text_instances:
                    rect = fitz.Rect(inst[0], inst[1], inst[2], inst[3])
                    page.add_redact_annot(rect)
                    page.apply_redactions()
                    page.insert_text(
                        rect.bl + (0, 2),  # Slightly below original position
                        replacement,
                        fontsize=11,
                        fontname="helv",
                        color=(0, 0, 0)
                    )
        
        # Save to output
        if isinstance(output_pdf, str):
            doc.save(output_pdf)
        else:
            doc.save(output_pdf, garbage=4, deflate=True)
        
        doc.close()
        
    except Exception as e:
        logging.error(f"Error in replace_text: {str(e)}", exc_info=True)
        raise
    
def send_email_with_attachment(subject, body, to_email, pdf_buffer, filename="invoice.pdf"):
    try:
        logging.debug(f"Preparing to send email to {to_email}")
        
        # Validate PDF buffer
        if not pdf_buffer:
            raise ValueError("PDF buffer is empty")
            
        pdf_buffer.seek(0)
        content = pdf_buffer.read()
        if not content:
            raise ValueError("PDF buffer contains no data")
            
        logging.debug(f"PDF content size: {len(content)} bytes")
        from_email = os.getenv("EMAIL_USERNAME")
        from_password = os.getenv("EMAIL_PASSWORD")

        if from_email is None or from_password is None:
            raise ValueError("EMAIL_USERNAME and EMAIL_PASSWORD environment variables must be set")

        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Read the BytesIO buffer and attach it as bytes
        pdf_buffer.seek(0)  # Ensure the buffer is at the beginning
        part = MIMEApplication(pdf_buffer.read(), Name=filename)
        part['Content-Disposition'] = f'attachment; filename="{filename}"'
        msg.attach(part)

        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(from_email, from_password)
            server.sendmail(from_email, to_email, msg.as_string())
            server.quit()
        except Exception as e:
            raise Exception(f"Failed to send email: {str(e)}")
    except Exception as e:
        logging.error(f"Error in send_email_with_attachment: {str(e)}", exc_info=True)
        raise
    

def generate_invoice(data):
    try:
        # Extract data from the input 
        logging.debug("Starting invoice generation...")
        system_size = data['system_size']
        panel_amount = data['panel_amount']
        panel_power = data['panel_power']
        price_of_inverter = data['price_of_inverter']
        brand_of_inverter = data['brand_of_inverter']
        price_of_panels = data['price_of_panels']
        netmetering_costs = data['netmetering_costs']
        installation_costs = data['installation_costs']
        cabling_costs = data['cabling_costs']
        structure_costs = data['structure_costs']
        electrical_and_mechanical_costs = data['electrical_and_mechanical_costs']
        total_cost = data['total_cost']
        customer_name = data['customer_name']
        customer_address = data['customer_address']
        customer_contact = data['customer_contact']

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            temp_path = tmp_file.name
        
        pdf = fpdf.FPDF(format=(260, 420))
        pdf.add_page()
        pdf.set_font("Arial", size=20)
        pdf.set_text_color(0, 0, 0)
        advance_payment = float(total_cost) * 0.9

        # Add the header section
        pdf.cell(240, 10, txt="Energy Cove Solar System Invoice", ln=1, align="C")
        pdf.set_font("Arial", size=12)
        pdf.cell(120, 10, txt=f"Customer Name: {customer_name}", ln=0, align="L")
        pdf.cell(120, 10, txt=f"Quotation Date: {datetime.date.today()}", ln=1, align="R")
        pdf.cell(120, 10, txt=f"Customer Address: {customer_address}", ln=0, align="L")
        pdf.cell(120, 10, txt=f"Present Date: {datetime.date.today()}", ln=1, align="R")
        pdf.cell(120, 10, txt=f"Customer Contact: {customer_contact}", ln=1, align="L")

        # Add the system size and type section
        pdf.set_fill_color(255, 255, 0)
        pdf.set_font("Arial", size=18)  
        
        pdf.cell(240, 10, txt=f"{system_size} kW | Solar System", ln=1, align="C",border=1, fill=True)

        # Add the description table
        pdf.set_fill_color(255, 255, 255)
        pdf.set_font("Arial", size=12)
        pdf.cell(15, 10, txt="S.No", border=1, ln=0, align="C", fill=True)
        pdf.cell(190, 10, txt="Description", border=1, ln=0, align="C", fill=True)
        pdf.cell(15, 10, txt="QTY", border=1, ln=0, align="C", fill=True)
        pdf.cell(20, 10, txt="Price", border=1, ln=1, align="C", fill=True)

        pdf.cell(15, 30, txt="1", border=1, ln=0, align="C", fill=True)
        pdf.set_fill_color(255, 255, 0)
        pdf.set_font("Arial", size=16)
        pdf.cell(190, 20, txt="PV Panels", border=1, ln=0, align="C", fill=True)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_font("Arial", size=12)
        pdf.cell(15, 20, txt=f"{panel_amount}", border="L, R,T", ln=0, align="C", fill=True)
        pdf.cell(20, 20, txt=f"{price_of_panels}", border="L,R,T", ln=1, align="R", fill=True)  
        pdf.cell(15, 10, txt="", border=0)  # Empty cell to create space
        pdf.cell(95, 10, txt=f"Brand: ", border=1, ln=0, align="L", fill=True)
        pdf.cell(95, 10, txt=f"Power Rating: {panel_power}", border=1, ln=0, align="L", fill=True)
        pdf.cell(15, 10, txt="", border="L,R,B")  # Empty cell to create space
        pdf.cell(20, 10, txt="", border="L,R,B", ln=1)  # Empty cell to create space


        pdf.cell(15, 40, txt="2", border=1, ln=0, align="C", fill=True)
        pdf.set_fill_color(255, 255, 0)
        pdf.set_font("Arial", size=16)
        pdf.cell(190, 20, txt="Inverter & Accessories", border=1, ln=0, align="C", fill=True)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_font("Arial", size=12)
        pdf.cell(15, 20, txt=f"", border="L, R, T", ln=0, align="C", fill=True)
        pdf.cell(20, 20, txt=f"", border="L,R, T", ln=1, align="R", fill=True)  
        pdf.cell(15, 10, txt="", border=0)  # Empty cell to create space
        pdf.cell(63.3, 10, txt=f"Brand: {brand_of_inverter}", border=1, ln=0, align="L", fill=True)
        pdf.cell(63.3, 10, txt=f"Power Rating: {system_size}kW", border=1, ln=0, align="L", fill=True)
        pdf.cell(63.4, 10, txt=f"Model: On-Grid", border=1, ln=0, align="L", fill=True)
        pdf.cell(15, 10, txt="1", border="L,R", align="C")  # Empty cell to create space
        pdf.cell(20, 10, txt=f"{int(float(price_of_inverter))}", border="L,R", ln=1, align="R")  # Empty cell to create space
        pdf.cell(15, 10, txt="", border=0)  # Empty cell to create space
        pdf.cell(190, 10, txt=f"Monitoring Device Included/ 5 Years warranty / System Produces 1200 Units per month", border=1, ln=0, align="L", fill=True)
        pdf.cell(15, 10, txt=f"", border="L, R,B", ln=0, align="C", fill=True)
        pdf.cell(20, 10, txt=f"", border="L,R,B", ln=1, align="R", fill=True)  

        pdf.cell(15, 40, txt="3", border=1, ln=0, align="C", fill=True)
        pdf.set_fill_color(255, 255, 0)
        pdf.set_font("Arial", size=14)
        pdf.cell(190, 10, txt="DC Cable & Earthing", border=1, ln=0, align="C", fill=True)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_font("Arial", size=12)
        pdf.cell(15, 10, txt=f"", border="L, R,T", ln=0, align="C", fill=True)
        pdf.cell(20, 10, txt=f"", border="L,R,T", ln=1, align="R", fill=True)  
        pdf.cell(15, 10, txt="", border=0)  # Empty cell to create space
        pdf.cell(95, 10, txt="DC Cable: 1000 VDC, 4mm as required by design & PVC Conduits", border=1, ln=0, align="L", fill=True)
        pdf.cell(95, 10, txt="Protection Box with Circuit Breakers, Fuses", border=1, ln=0, align="L", fill=True)
        pdf.cell(15, 10, txt="1", border="L,R", ln=0, align="C", fill=True)
        pdf.cell(20, 10, txt=f"{cabling_costs}", border="L,R", ln=1, align="R", fill=True)
        pdf.cell(15, 10, txt="", border=0)  # Empty cell to create space
        pdf.set_fill_color(255, 255, 0)
        pdf.set_font("Arial", size=14)
        pdf.cell(190, 10, txt="AC Cable", border=1, ln=0, align="C", fill=True)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_font("Arial", size=12)
        pdf.cell(15, 10, txt=f"", border="L, R", ln=0, align="C", fill=True)
        pdf.cell(20, 10, txt=f"", border="L,R", ln=1, align="R", fill=True)  
        pdf.cell(15, 10, txt="", border=0)  # Empty cell to create space
        pdf.cell(190, 10, txt="AC Cable: 0.415kV as per required design (10 Meter from Inverter to Main DB )", border=1, ln=0, align="L", fill=True)
        pdf.cell(15, 10, txt="", border="L,R,B", ln=0, align="C", fill=True)
        pdf.cell(20, 10, txt=f"", border="L,R,B", ln=1, align="R", fill=True)

        pdf.cell(15, 30, txt="4", border=1, ln=0, align="C", fill=True)
        pdf.set_fill_color(255, 255, 0)
        pdf.set_font("Arial", size=16)
        pdf.cell(190, 20, txt="PV Panels Structure", border=1, ln=0, align="C", fill=True)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_font("Arial", size=12)
        pdf.cell(15, 20, txt=f"1", border="L, R,T", ln=0, align="C", fill=True)
        pdf.cell(20, 20, txt=f"{int(float(structure_costs))}", border="L,R,T", ln=1, align="R", fill=True)  
        pdf.cell(15, 10, txt="", border=0)  # Empty cell to create space
        pdf.cell(190, 10, txt=f"Customized frames with steel pipes & Chanels 14 guage and painting for 18 panels", border=1, ln=0, align="L", fill=True)
        pdf.cell(15, 10, txt="", border="L,R,B")  # Empty cell to create space
        pdf.cell(20, 10, txt="", border="L,R,B", ln=1)  # Empty cell to create space

        pdf.cell(15, 50, txt="5", border=1, ln=0, align="C", fill=True)
        pdf.set_fill_color(255, 255, 0)
        pdf.set_font("Arial", size=16)
        pdf.cell(190, 20, txt="Balance of System / Installation & Commissioning", border=1, ln=0, align="C", fill=True)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_font("Arial", size=12)
        pdf.cell(15, 20, txt=f"", border="L, R,T", ln=0, align="C", fill=True)
        pdf.cell(20, 20, txt=f"", border="L,R,T", ln=1, align="R", fill=True)  
        pdf.cell(15, 10, txt="", border=0)  # Empty cell to create space
        pdf.cell(190, 10, txt=f"AC/DC Cable Trau, Flexible Pipes, Conduits, Rawal Bolts, Cable Ties, Lugs & other accessories", border=1, ln=0, align="L", fill=True)
        pdf.cell(15, 10, txt="1", border="L,R", align="C")  # Empty cell to create space
        pdf.cell(20, 10, txt=f"{int(float(installation_costs))}", border="L,R", ln=1, align="R")  # Empty cell to create space
        pdf.cell(15, 10, txt="", border=0)  # Empty cell to create space
        pdf.cell(190, 10, txt=f"Transportation Cost", border=1, ln=0, align="L", fill=True)
        pdf.cell(15, 10, txt="", border="L,R")  # Empty cell to create space
        pdf.cell(20, 10, txt="", border="L,R", ln=1)  # Empty cell to create space
        pdf.cell(15, 10, txt="", border=0)  # Empty cell to create space
        pdf.cell(190, 10, txt=f"Earthing system AC/DC", border=1, ln=0, align="L", fill=True)
        pdf.cell(15, 10, txt="", border="L,R,B")  # Empty cell to create space
        pdf.cell(20, 10, txt="", border="L,R,B", ln=1)  # Empty cell to create space

        pdf.cell(15, 30, txt="6", border=1, ln=0, align="C", fill=True)
        pdf.set_fill_color(255, 255, 0)
        pdf.set_font("Arial", size=16)
        pdf.cell(190, 20, txt="Installation & Commissioning ", border=1, ln=0, align="C", fill=True)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_font("Arial", size=12)
        pdf.cell(15, 20, txt=f"1", border="L, R,T", ln=0, align="C", fill=True)
        pdf.cell(20, 20, txt=f"{int(float(electrical_and_mechanical_costs))}", border="L,R,T", ln=1, align="R", fill=True)  
        pdf.cell(15, 10, txt="", border=0)  # Empty cell to create space
        pdf.cell(190, 10, txt=f"Electrical & Mechanical work", border=1, ln=0, align="L", fill=True)
        pdf.cell(15, 10, txt="", border="L,R,B")  # Empty cell to create space
        pdf.cell(20, 10, txt="", border="L,R,B", ln=1)  # Empty cell to create space
        # Add the netmetering section
        pdf.cell(15, 40, txt="7", border=1, ln=0, align="C", fill=True)
        pdf.set_fill_color(255, 255, 0)
        pdf.set_font("Arial", size=16)
        pdf.cell(190, 20, txt="Netmetering", border=1, ln=0, align="C", fill=True)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_font("Arial", size=12)
        pdf.cell(15, 20, txt=f"", border="L, R,T", ln=0, align="C", fill=True)
        pdf.cell(20, 20, txt=f"", border="L,R,T", ln=1, align="R", fill=True)  
        pdf.cell(15, 10, txt="", border=0)  # Empty cell to create space
        pdf.cell(95, 10, txt=f"Preparation of file - Dealing with MEPCO", border=1, ln=0, align="L", fill=True)
        pdf.cell(95, 10, txt=f"2 Reverse meters supply", border=1, ln=0, align="L", fill=True)
        pdf.cell(15, 10, txt="1", border="L,R" , align="C")  # Empty cell to create space
        pdf.cell(20, 10, txt=f"{int(float(netmetering_costs))}", border="L,R", ln=1, align="R")  # Empty cell to create space
        pdf.cell(15, 10, txt="", border=0)  # Empty cell to create space
        pdf.cell(190, 10, txt=f"Load extension / Main wire from green meters to Main DB of house in the scope of client", border=1, ln=0, align="L", fill=True)
        pdf.cell(15, 10, txt="", border="L,R,B")  # Empty cell to create space
        pdf.cell(20, 10, txt="", border="L,R,B", ln=1)  # Empty cell to create space
        # Add the total system cost section
        pdf.set_fill_color(0, 128, 0)
        pdf.set_font("Arial", size=15)
        pdf.cell(205, 20, txt=f"Total System Cost:",border=1, ln=0, align="C", fill=True)
        pdf.cell(35, 20, txt=f"{int(total_cost)}", border=1, ln=1, align="C", fill=True)
        pdf.cell(205, 20, txt=f"90% Advance Payment and 10% after testing commissioning:", border=1, ln=0, align="C", fill=True)
        pdf.cell(35, 20, txt=f"{int(advance_payment)}", border=1, ln=1, align="C", fill=True)

        pdf.output(temp_path)
        
        # Step 2: Define text replacements
        replacements = {
            "[NAME]": data['customer_name'],
            "[System Power]": str(data['system_size']),
            "[System Type]": "Solar System"
            # Add other template placeholders as needed
        }
        
        # Step 3: Perform text replacement
        output_buffer = io.BytesIO()
        replace_text(temp_path, output_buffer, replacements)
        
        # Clean up
        os.unlink(temp_path)
        
        output_buffer.seek(0)
        return output_buffer

    except Exception as e:
        logging.error(f"Error in generate_invoice: {str(e)}", exc_info=True)
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise

