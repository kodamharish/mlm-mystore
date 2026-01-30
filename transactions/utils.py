
from django.conf import settings

from uuid import uuid4
from phonepe.sdk.pg.payments.v2.standard_checkout_client import StandardCheckoutClient
from phonepe.sdk.pg.payments.v2.models.request.standard_checkout_pay_request import StandardCheckoutPayRequest
from phonepe.sdk.pg.common.models.request.meta_info import MetaInfo
from phonepe.sdk.pg.env import Env

#pdf
from io import BytesIO
from datetime import datetime
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import os
from django.conf import settings



def get_phonepe_client():
    env_map = {
        "SANDBOX": Env.SANDBOX,
        "PRODUCTION": Env.PRODUCTION
    }
    return StandardCheckoutClient.get_instance(
        client_id=settings.PHONEPE_CLIENT_ID,
        client_secret=settings.PHONEPE_CLIENT_SECRET,
        client_version=settings.PHONEPE_CLIENT_VERSION,
        env=env_map.get(settings.PHONEPE_ENVIRONMENT, Env.SANDBOX),
        should_publish_events=False
    )


def initiate_payment(amount, redirect_url):
    client = get_phonepe_client()
    unique_order_id = str(uuid4())
    meta_info = MetaInfo(udf1="udf1", udf2="udf2", udf3="udf3")

    pay_request = StandardCheckoutPayRequest.build_request(
        merchant_order_id=unique_order_id,
        amount=amount,
        redirect_url=redirect_url,
        meta_info=meta_info
    )

    response = client.pay(pay_request)
    return {
        "order_id": unique_order_id,
        "merchant_order_id": unique_order_id,
        "redirect_url": response.redirect_url,
    }


# def check_payment_status(merchant_order_id):
#     client = get_phonepe_client()
#     response = client.get_order_status(merchant_order_id, details=False)
#     return response.state  # PENDING, COMPLETED, FAILED, etc.

def check_payment_status(merchant_order_id):
    client = get_phonepe_client()
    response = client.get_order_status(merchant_order_id, details=False)

    # Serialize the payment details
    payment_details = [
        {
            "payment_mode": getattr(detail, "payment_mode", None),
            "amount": getattr(detail, "amount", None),
            "transaction_id": getattr(detail, "transaction_id", None),
            "state": getattr(detail, "state", None),
            "error_code": getattr(detail, "error_code", None),
            "detailed_error_code": getattr(detail, "detailed_error_code", None),
            "instrument_type": getattr(detail, "instrumentType", None),
        }
        for detail in response.payment_details or []
    ]

    return {
        "merchant_order_id": merchant_order_id,
        "status": response.state,
        "payment_details": payment_details,
        "amount": response.amount,
        "order_id": response.order_id,
    }





#PDF 


def generate_invoice_pdf_old(transaction, user, property_obj, doc_number, doc_type):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 40
    table_width = width - 2 * margin  # Fixed width for both tables

    # === Company Name at Top ===
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(width / 2, height - 50, "SHRIRAJ PROPERTY SOLUTIONS PRIVATE LIMITED")

    # === Header Section ===
    pdf.setFont("Helvetica", 9)
    
    # Address Left
    left_texts = [
        "50/4,",
        "Atal Chowk, Main Road Boria Khurd, ",
        "Near Durga Mandir,Raipur, ",
        "Chhattisgarh, 492017,",
        "India"
    ]
    for i, line in enumerate(left_texts):
        pdf.drawString(margin, height - 120 - i*12, line)
    
    # Logo in Center
    logo_path = os.path.join(settings.BASE_DIR, "static/images/logo.png")
    if os.path.exists(logo_path):
        logo_width = 90
        logo_height = 90
        pdf.drawImage(logo_path, (width - logo_width) / 2 - 30, height - 190, 
                     width=logo_width, height=logo_height, mask='auto')

    # GST Right
    right_texts = [
        "GSTN 22ABDCS6806R2ZV",
        "9074307248",
        "shrirajproperty00@gmail.com",
        "shrirajteam.com"
    ]
    for i, line in enumerate(right_texts):
        pdf.drawRightString(width - margin, height - 120 - i*12, line)

    # === TAX INVOICE ===
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawRightString(width - margin, height - 180, f"Tax {doc_type.title()}")

    # === Invoice Info Table ===
    pdf.setFont("Helvetica", 9)
    info_data = [
        ["REC / INV No", f"{doc_number}", "Name", f"{user.username}"],
        ["Invoice Date", f"{datetime.today().strftime('%d/%m/%Y')}", "Email", f"{user.email}"],
        ["Due Date", f"{datetime.today().strftime('%d/%m/%Y')}", "Phone", f"{user.phone_number}"],
    ]
    
    # Calculate column widths proportionally
    info_col_widths = [
        table_width * 0.20,  # Left label column (20%)
        table_width * 0.30,  # Left value column (30%)
        table_width * 0.15,  # Right label column (15%)
        table_width * 0.35   # Right value column (35%)
    ]
    
    info_table = Table(info_data, colWidths=info_col_widths)
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
    ]))
    info_table.wrapOn(pdf, width, height)
    info_table.drawOn(pdf, margin, height - 300)

    # === Property Table ===
    styles = getSampleStyleSheet()
    cell_style = styles["Normal"]
    cell_style.fontName = "Helvetica"
    cell_style.fontSize = 9
    cell_style.leading = 10
    cell_style.alignment = 1  # Center alignment

    # Create data with proper spacing for headers
    # === Property Table ===
    receipt_property_data = [
        ["S NO", "Property Title", "Property Value", "Balance Amount", "Booking Amount", "Total"],
        ["1", property_obj.property_title, f"{property_obj.total_property_value:.2f}",
         f"{transaction.remaining_amount:.2f}", f"{property_obj.booking_amount:.2f}",
         f"{property_obj.booking_amount:.2f}"]
    ]

    invoice_property_data = [
        ["S NO", "Property Title", "Property Value", "Balance", "Amount", "Total"],
        ["1", property_obj.property_title, f"{property_obj.total_property_value:.2f}",
         f"{transaction.remaining_amount:.2f}", f"{property_obj.property_value_without_booking_amount:.2f}",
         f"{property_obj.property_value_without_booking_amount:.2f}"]
    ]

    
    # Calculate column widths proportionally (same total width as info table)
    prop_col_widths = [
        table_width * 0.07,  # S NO (7%)
        table_width * 0.33,  # Property Title (33%)
        table_width * 0.15,  # Property Value (15%)
        table_width * 0.15,  # Remaining Amount (15%)
        table_width * 0.15,  # Amount (15%)
        table_width * 0.15   # Total (15%)
    ]


    if doc_type == 'receipt':
        prop_table = Table(receipt_property_data, colWidths=prop_col_widths)
    else:
        prop_table = Table(invoice_property_data, colWidths=prop_col_widths)

    
    #prop_table = Table(property_data, colWidths=prop_col_widths)
    prop_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEADING", (0, 0), (-1, -1), 10),
        ("WORDWRAP", (1, 1), (1, 1), True),  # Wrap property title
    ]))
    
    # Position property table with consistent spacing
    prop_table.wrapOn(pdf, width, height)
    prop_table.drawOn(pdf, margin, height - 360)  # 60px below info table

    # === Footer ===
    footer_y = height - 400  # 40px below property table
    pdf.setFont("Helvetica", 9)
    footer_lines = [
        "Thank you for Trusting Us! Your support inspires us to",
        "Consistently Deliver Quality and Innovation. We Look",
        "Forward to Serving You Again.",
        "",
        "Payment Options",
        "Bank Name - State Bank of India",
        "Account no - 1234",
        "IFSC Code - 1234",
        "Branch - Bangalore",
        "",
        "Terms & Conditions",
        "1. Payment must be made within the due date from the invoice date.",
        "2. Accepted payment methods include Bank Transfer, UPI, Demand Draft (DD), and Cheque",
        "3. Cash payments are not accepted.",
        "4. Prices are exclusive of applicable taxes.",
        "5. Orders cannot be canceled once they have been processed.",
        "6. Refund or exchange of goods will be done only for defective or damaged goods upon inspection by the company.",
        "7. Responsibility ceases regarding the weight of the goods once the box tape is Tampered.",
        "",
        "For any queries, please contact",
        "Email - shrirajproperty00@gmail.com",
        "Contact - 9074307248"
    ]
    for i, line in enumerate(footer_lines):
        pdf.drawString(margin, footer_y - (i * 12), line)

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    transaction.document_file.save(f"{doc_number}.pdf", ContentFile(buffer.read()))






def generate_invoice_pdf(transaction, user, property_obj, doc_number, payment_type):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 40
    table_width = width - 2 * margin

    # === Company Name ===
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(width / 2, height - 50,
                          "SHRIRAJ PROPERTY SOLUTIONS PRIVATE LIMITED")

    # === Address & Contact ===
    pdf.setFont("Helvetica", 9)
    left_texts = [
        "50/4,",
        "Atal Chowk, Main Road Boria Khurd,",
        "Near Durga Mandir, Raipur,",
        "Chhattisgarh, 492017,",
        "India",
    ]
    for i, line in enumerate(left_texts):
        pdf.drawString(margin, height - 120 - i * 12, line)

    logo_path = os.path.join(settings.BASE_DIR, "static/images/logo.png")
    if os.path.exists(logo_path):
        pdf.drawImage(logo_path, (width - 90) / 2 - 30, height - 190,
                      width=90, height=90, mask="auto")

    right_texts = [
        "GSTN 22ABDCS6806R2ZV",
        "9074307248",
        "shrirajproperty00@gmail.com",
        "shrirajteam.com",
    ]
    for i, line in enumerate(right_texts):
        pdf.drawRightString(width - margin, height - 120 - i * 12, line)

    # === Tax Invoice ===
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawRightString(width - margin, height - 180, "Tax Invoice")

    # === Invoice Info Table ===
    info_data = [
        ["Invoice No", doc_number, "Name", f"{user.first_name} {user.last_name}"],
        ["Invoice Date", datetime.today().strftime("%d/%m/%Y"), "Email", user.email],
        [ "Phone", user.phone_number],
    ]
    info_table = Table(
        info_data,
        colWidths=[table_width * 0.2, table_width * 0.3,
                   table_width * 0.15, table_width * 0.35],
    )
    info_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    info_table.wrapOn(pdf, width, height)
    info_table.drawOn(pdf, margin, height - 300)

    # === Property Table ===
    receipt_property_data = [
        ["S NO", "Property Title", "Property Value",
         "Balance Amount", "Booking Amount", "Total"],
        ["1", property_obj.property_title,
         f"{property_obj.total_property_value:.2f}",
         f"{transaction.remaining_amount:.2f}",
         f"{property_obj.booking_amount:.2f}",
         f"{property_obj.booking_amount:.2f}"]
    ]

    invoice_property_data = [
        ["S NO", "Property Title", "Property Value",
         "Balance", "Amount", "Total"],
        ["1", property_obj.property_title,
         f"{property_obj.total_property_value:.2f}",
         f"{transaction.remaining_amount:.2f}",
         f"{property_obj.property_value_without_booking_amount:.2f}",
         f"{property_obj.property_value_without_booking_amount:.2f}"]
    ]

    # Pick correct table based on payment_type
    if payment_type == "Booking-Amount":
        property_data = receipt_property_data
    else:  # Full-Amount
        property_data = invoice_property_data

    prop_table = Table(property_data, colWidths=[
        table_width * 0.07, table_width * 0.33,
        table_width * 0.15, table_width * 0.15,
        table_width * 0.15, table_width * 0.15,
    ])
    prop_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    prop_table.wrapOn(pdf, width, height)
    prop_table.drawOn(pdf, margin, height - 360)

    # === Footer ===
    footer_y = height - 400
    pdf.setFont("Helvetica", 9)
    footer_lines = [
        # "Thank you for Trusting Us! Your support inspires us to",
        # "Consistently Deliver Quality and Innovation. We Look",
        # "Forward to Serving You Again.",
        # "",
        # "Payment Options",
        # "Bank Name - State Bank of India",
        # "Account no - 1234",
        # "IFSC Code - 1234",
        # "Branch - Bangalore",
        # "",
        # "Terms & Conditions",
        # "1. Payment must be made within the due date from the invoice date.",
        # "2. Accepted payment methods include Bank Transfer, UPI, Demand Draft (DD), and Cheque",
        # "3. Cash payments are not accepted.",
        # "4. Prices are exclusive of applicable taxes.",
        # "5. Orders cannot be canceled once processed.",
        # "6. Refund/exchange only for defective goods upon inspection.",
        # "7. Responsibility ceases regarding the weight once box tape is tampered.",
        # "",
        "For any queries: shrirajproperty00@gmail.com | 9074307248",
    ]
    for i, line in enumerate(footer_lines):
        pdf.drawString(margin, footer_y - i * 12, line)

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    transaction.document_file.save(f"{doc_number}.pdf", ContentFile(buffer.read()))





def generate_subscription_invoice_pdf_old(transaction, user, variant, doc_number, doc_type):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 40
    table_width = width - 2 * margin  # Fixed width for tables

    # === Company Name at Top ===
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(width / 2, height - 50, "SHRIRAJ PROPERTY SOLUTIONS PRIVATE LIMITED")

    # === Header Section ===
    pdf.setFont("Helvetica", 9)

    # Address Left
    left_texts = [
        "50/4,",
        "Atal Chowk, Main Road Boria Khurd, ",
        "Near Durga Mandir, Raipur, ",
        "Chhattisgarh, 492017,",
        "India"
    ]
    for i, line in enumerate(left_texts):
        pdf.drawString(margin, height - 120 - i*12, line)

    # Logo Center
    logo_path = os.path.join(settings.BASE_DIR, "static/images/logo.png")
    if os.path.exists(logo_path):
        logo_width = 100
        logo_height = 100
        pdf.drawImage(logo_path, (width - logo_width) / 2 - 30, height - 190,
                      width=logo_width, height=logo_height, mask='auto')

    # GST & Contact Right
    right_texts = [
        "GSTN 22ABDCS6806R2ZV",
        "9074307248",
        "shrirajproperty00@gmail.com",
        "shrirajteam.com"
    ]
    for i, line in enumerate(right_texts):
        pdf.drawRightString(width - margin, height - 120 - i*12, line)

    # === TAX INVOICE ===
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawRightString(width - margin, height - 180, f"Tax {doc_type.title()}")

    # === Invoice Info Table ===
    pdf.setFont("Helvetica", 9)
    info_data = [
        ["REC / INV No", f"{doc_number}", "Name", f"{user.username}"],
        ["Invoice Date", f"{datetime.today().strftime('%d/%m/%Y')}", "Email", f"{user.email}"],
        ["Due Date", f"{datetime.today().strftime('%d/%m/%Y')}", "Phone", f"{user.phone_number}"],
    ]

    info_col_widths = [
        table_width * 0.20,  # Left label
        table_width * 0.30,  # Left value
        table_width * 0.15,  # Right label
        table_width * 0.35   # Right value
    ]

    info_table = Table(info_data, colWidths=info_col_widths)
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
    ]))
    info_table.wrapOn(pdf, width, height)
    info_table.drawOn(pdf, margin, height - 300)

    # === Subscription Table ===
    styles = getSampleStyleSheet()
    cell_style = styles["Normal"]
    cell_style.fontName = "Helvetica"
    cell_style.fontSize = 9
    cell_style.leading = 10
    cell_style.alignment = 1  # Center align

    # Subscription details
    invoice_subscription_data = [
        ["S NO", "Plan Name",  "Duration", "Amount", "Total"],
        [
            "1",
            variant.plan_id.plan_name if variant.plan_id else "N/A",
            variant.duration_in_days,          # If you store duration
            f"{variant.price:.2f}",
            f"{variant.price:.2f}"
        ]
    ]

    sub_col_widths = [
        table_width * 0.07,  # S NO
        table_width * 0.28,  # Plan Name
        table_width * 0.20,  # Variant
        table_width * 0.15,  # Duration
        table_width * 0.15,  # Amount
        table_width * 0.15   # Total
    ]

    sub_table = Table(invoice_subscription_data, colWidths=sub_col_widths)
    sub_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEADING", (0, 0), (-1, -1), 10),
    ]))

    sub_table.wrapOn(pdf, width, height)
    sub_table.drawOn(pdf, margin, height - 360)

    # === Footer ===
    footer_y = height - 420
    pdf.setFont("Helvetica", 9)
    footer_lines = [
        "Thank you for Trusting Us! Your support inspires us to",
        "Consistently Deliver Quality and Innovation. We Look",
        "Forward to Serving You Again.",
        "",
        "Payment Options",
        "Bank Name - State Bank of India",
        "Account no - 1234",
        "IFSC Code - 1234",
        "Branch - Bangalore",
        "",
        "Terms & Conditions",
        "1. Payment must be made within the due date from the invoice date.",
        "2. Accepted payment methods include Bank Transfer, UPI, Demand Draft (DD), and Cheque",
        "3. Cash payments are not accepted.",
        "4. Prices are exclusive of applicable taxes.",
        "5. Orders cannot be canceled once they have been processed.",
        "6. Refund or exchange of goods will be done only for defective or damaged goods upon inspection by the company.",
        "7. Responsibility ceases regarding the goods once the box tape is tampered.",
        "",
        "For any queries, please contact",
        "Email - shrirajproperty00@gmail.com",
        "Contact - 9074307248"
    ]
    for i, line in enumerate(footer_lines):
        pdf.drawString(margin, footer_y - (i * 12), line)

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    transaction.document_file.save(f"{doc_number}.pdf", ContentFile(buffer.read()))


def generate_subscription_invoice_pdf(transaction, user, variant, doc_number):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 40
    table_width = width - 2 * margin  # Fixed width for tables

    # === Company Name at Top ===
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(width / 2, height - 50, "SHRIRAJ PROPERTY SOLUTIONS PRIVATE LIMITED")

    # === Header Section ===
    pdf.setFont("Helvetica", 9)

    # Address Left
    left_texts = [
        "50/4,",
        "Atal Chowk, Main Road Boria Khurd, ",
        "Near Durga Mandir, Raipur, ",
        "Chhattisgarh, 492017,",
        "India"
    ]
    for i, line in enumerate(left_texts):
        pdf.drawString(margin, height - 120 - i*12, line)

    # Logo Center
    logo_path = os.path.join(settings.BASE_DIR, "static/images/logo.png")
    if os.path.exists(logo_path):
        logo_width = 100
        logo_height = 100
        pdf.drawImage(logo_path, (width - logo_width) / 2 - 30, height - 190,
                      width=logo_width, height=logo_height, mask='auto')

    # GST & Contact Right
    right_texts = [
        "GSTN 22ABDCS6806R2ZV",
        "9074307248",
        "shrirajproperty00@gmail.com",
        "shrirajteam.com"
    ]
    for i, line in enumerate(right_texts):
        pdf.drawRightString(width - margin, height - 120 - i*12, line)

    # === TAX INVOICE ===
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawRightString(width - margin, height - 180, f"Tax Invoice")

    # === Invoice Info Table ===
    pdf.setFont("Helvetica", 9)
    info_data = [
        ["Invoice No", f"{doc_number}", "Name", f"{user.first_name} {user.last_name}"],
        ["Invoice Date", f"{datetime.today().strftime('%d/%m/%Y')}", "Email", f"{user.email}"],
        ["Phone", f"{user.phone_number}"],
    ]

    info_col_widths = [
        table_width * 0.20,  # Left label
        table_width * 0.30,  # Left value
        table_width * 0.15,  # Right label
        table_width * 0.35   # Right value
    ]

    info_table = Table(info_data, colWidths=info_col_widths)
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
    ]))
    info_table.wrapOn(pdf, width, height)
    info_table.drawOn(pdf, margin, height - 300)

    # === Subscription Table ===
    styles = getSampleStyleSheet()
    cell_style = styles["Normal"]
    cell_style.fontName = "Helvetica"
    cell_style.fontSize = 9
    cell_style.leading = 10
    cell_style.alignment = 1  # Center align

    # Subscription details
    invoice_subscription_data = [
        ["S NO", "Plan Name",  "Duration (Days)", "Amount", "Total"],
        [
            "1",
            variant.plan_id.plan_name if variant.plan_id else "N/A",
            variant.duration_in_days,          # If you store duration
            f"{variant.price:.2f}",
            f"{variant.price:.2f}"
        ]
    ]

    sub_col_widths = [
        table_width * 0.07,  # S NO
        table_width * 0.28,  # Plan Name
        table_width * 0.20,  # Variant
        table_width * 0.15,  # Duration
        table_width * 0.15,  # Amount
        table_width * 0.15   # Total
    ]

    sub_table = Table(invoice_subscription_data, colWidths=sub_col_widths)
    sub_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEADING", (0, 0), (-1, -1), 10),
    ]))

    sub_table.wrapOn(pdf, width, height)
    sub_table.drawOn(pdf, margin, height - 360)

    # === Footer ===
    footer_y = height - 420
    pdf.setFont("Helvetica", 9)
    footer_lines = [
        # "Thank you for Trusting Us! Your support inspires us to",
        # "Consistently Deliver Quality and Innovation. We Look",
        # "Forward to Serving You Again.",
        # "",
        # "Payment Options",
        # "Bank Name - State Bank of India",
        # "Account no - 1234",
        # "IFSC Code - 1234",
        # "Branch - Bangalore",
        # "",
        # "Terms & Conditions",
        # "1. Payment must be made within the due date from the invoice date.",
        # "2. Accepted payment methods include Bank Transfer, UPI, Demand Draft (DD), and Cheque",
        # "3. Cash payments are not accepted.",
        # "4. Prices are exclusive of applicable taxes.",
        # "5. Orders cannot be canceled once they have been processed.",
        # "6. Refund or exchange of goods will be done only for defective or damaged goods upon inspection by the company.",
        # "7. Responsibility ceases regarding the goods once the box tape is tampered.",
        # "",
        "For any queries, please contact",
        "Email - shrirajproperty00@gmail.com",
        "Contact - 9074307248"
    ]
    for i, line in enumerate(footer_lines):
        pdf.drawString(margin, footer_y - (i * 12), line)

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    transaction.document_file.save(f"{doc_number}.pdf", ContentFile(buffer.read()))




def generate_product_invoice_pdf_old(transaction, order, user):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 40
    table_width = width - 2 * margin

    # ================= COMPANY NAME =================
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(
        width / 2,
        height - 50,
        "SHRIRAJ PROPERTY SOLUTIONS PRIVATE LIMITED"
    )

    # ================= HEADER =================
    pdf.setFont("Helvetica", 9)

    # Address (Left)
    left_texts = [
        "50/4,",
        "Atal Chowk, Main Road Boria Khurd,",
        "Near Durga Mandir, Raipur,",
        "Chhattisgarh, 492017,",
        "India"
    ]
    for i, line in enumerate(left_texts):
        pdf.drawString(margin, height - 120 - i * 12, line)

    # Logo (Center)
    logo_path = os.path.join(settings.BASE_DIR, "static/images/logo.png")
    if os.path.exists(logo_path):
        pdf.drawImage(
            logo_path,
            (width - 100) / 2 - 30,
            height - 190,
            width=100,
            height=100,
            mask="auto"
        )

    # GST & Contact (Right)
    right_texts = [
        "GSTN 22ABDCS6806R2ZV",
        "9074307248",
        "shrirajproperty00@gmail.com",
        "shrirajteam.com"
    ]
    for i, line in enumerate(right_texts):
        pdf.drawRightString(width - margin, height - 120 - i * 12, line)

    # ================= TAX INVOICE =================
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawRightString(width - margin, height - 180, "Tax Invoice")

    # ================= INVOICE INFO =================
    pdf.setFont("Helvetica", 9)
    info_data = [
        ["Invoice No", transaction.document_number, "Name", f"{user.first_name} {user.last_name}"],
        ["Invoice Date", datetime.today().strftime('%d/%m/%Y'), "Email", user.email],
        ["Phone", user.phone_number, "", ""],
    ]

    info_table = Table(
        info_data,
        colWidths=[
            table_width * 0.20,
            table_width * 0.30,
            table_width * 0.15,
            table_width * 0.35,
        ]
    )

    info_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))

    info_table.wrapOn(pdf, width, height)
    info_table.drawOn(pdf, margin, height - 300)

    # ================= PRODUCT TABLE =================
    product_table_data = [
        ["S No", "Product Name", "Qty", "Price", "Total"]
    ]

    for idx, item in enumerate(order.items.all(), start=1):
        product_table_data.append([
            str(idx),
            item.product.product_name,
            str(item.quantity),
            f"{item.price:.2f}",
            f"{item.price * item.quantity:.2f}",
        ])

    product_table = Table(
        product_table_data,
        colWidths=[
            table_width * 0.08,
            table_width * 0.42,
            table_width * 0.10,
            table_width * 0.20,
            table_width * 0.20,
        ]
    )

    product_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (2, 1), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))

    product_table.wrapOn(pdf, width, height)
    product_table.drawOn(pdf, margin, height - 380)

    # ================= TOTAL =================
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawRightString(
        width - margin,
        height - 380 - (len(product_table_data) * 20),
        f"Grand Total: {order.total_amount:.2f}"
    )

    # ================= FOOTER =================
    footer_y = height - 500
    pdf.setFont("Helvetica", 9)
    footer_lines = [
        "For any queries, please contact",
        "Email - shrirajproperty00@gmail.com",
        "Contact - 9074307248",
    ]

    for i, line in enumerate(footer_lines):
        pdf.drawString(margin, footer_y - i * 12, line)

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    transaction.document_file.save(
        f"{transaction.document_number}.pdf",
        ContentFile(buffer.read())
    )




def generate_variant_invoice_pdf_new1(transaction, order, user):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 40
    table_width = width - 2 * margin

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(width / 2, height - 50, "SHRIRAJ PROPERTY SOLUTIONS PRIVATE LIMITED")

    pdf.setFont("Helvetica", 9)

    # CUSTOMER + INVOICE INFO
    info_data = [
        ["Invoice No", transaction.document_number, "Name", user.username],
        ["Invoice Date", datetime.today().strftime('%d/%m/%Y'), "Email", user.email],
        ["Phone", user.phone_number or "", "", ""],
    ]

    info_table = Table(
        info_data,
        colWidths=[table_width * .20, table_width * .30, table_width * .15, table_width * .35]
    )
    info_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    info_table.wrapOn(pdf, width, height)
    info_table.drawOn(pdf, margin, height - 160)

    # PRODUCT TABLE (VARIANTS)
    product_data = [["S No", "Product", "Variant", "Qty", "Price", "Total"]]

    for idx, item in enumerate(order.items.all(), 1):
        product = item.variant.product if item.variant else None
        product_data.append([
            str(idx),
            product.product_name if product else "",
            item.variant.name if item.variant else "-",
            str(item.quantity),
            f"{item.price:.2f}",
            f"{item.price * item.quantity:.2f}"
        ])

    product_table = Table(product_data, colWidths=[
        table_width * .08,
        table_width * .32,
        table_width * .20,
        table_width * .10,
        table_width * .15,
        table_width * .15,
    ])

    product_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (3, 1), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    product_table.wrapOn(pdf, width, height)
    product_table.drawOn(pdf, margin, height - 350)

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawRightString(width - margin, height - 360 - (len(product_data) * 20),
                        f"Grand Total: {order.total_amount:.2f}")

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    transaction.document_file.save(
        f"{transaction.document_number}.pdf",
        ContentFile(buffer.read())
    )



def format_variant_attributes(attrs):
    if not attrs:
        return "-"

    # if stored as dict: {"Color": "Red", "Size": "XL"}
    if isinstance(attrs, dict):
        return " / ".join(f"{k}: {v}" for k, v in attrs.items())

    # if stored as list: [{"Color": "Red"}, {"Size": "XL"}]
    if isinstance(attrs, list):
        kv_pairs = []
        for d in attrs:
            if isinstance(d, dict):
                kv_pairs.extend(f"{k}: {v}" for k, v in d.items())
        if kv_pairs:
            return " / ".join(kv_pairs)

    # fallback for unexpected formats
    return str(attrs)


def generate_invoice_pdf_new2(transaction, order, user):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 40
    table_width = width - 2 * margin

    # HEADER
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(width/2, height-40, "ORDER INVOICE")

    pdf.setFont("Helvetica", 9)
    pdf.drawString(margin, height-70, f"Invoice No: {transaction.document_number}")
    pdf.drawString(margin, height-85, f"Invoice Date: {datetime.today().strftime('%d/%m/%Y')}")

    # BUYER DETAILS
    pdf.drawString(margin, height-110, f"First Name: {user.first_name}")
    pdf.drawString(margin, height-125, f"Last Name: {user.last_name}")
    pdf.drawString(margin, height-140, f"Email: {user.email}")
    pdf.drawString(margin, height-155, f"Phone: {getattr(user,'phone_number','')}")

    # TABLE
    table_data = [["Item", "Details", "Qty", "Price", "Total"]]

    for item in order.items.all():
        if item.variant:
            product = item.variant.product
            attrs = format_variant_attributes(item.variant.attributes)
            title = f"{product.product_name} ({attrs})"
        else:
            p = item.property_item
            title = f"{p.property_title}"

        table_data.append([
            "Product" if item.variant else "Property",
            title,
            str(item.quantity),
            f"{item.price:.2f}",
            f"{item.price * item.quantity:.2f}"
        ])

    table = Table(table_data, colWidths=[
        table_width * .15, table_width * .40,
        table_width * .10, table_width * .15, table_width * .20
    ])

    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ALIGN", (2,1), (-1,-1), "CENTER"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
    ]))

    table.wrapOn(pdf, width, height)
    table.drawOn(pdf, margin, height-300)

    # TOTAL
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawRightString(width-margin, height-320-(len(table_data)*15),
                        f"Grand Total: {order.total_amount:.2f}")

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    transaction.document_file.save(
        f"{transaction.document_number}.pdf",
        ContentFile(buffer.read())
    )






def generate_product_invoice_pdf_new3(transaction, order, user):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 40
    table_width = width - 2 * margin

    # ================= COMPANY NAME =================
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(
        width / 2,
        height - 50,
        "SHRIRAJ PROPERTY SOLUTIONS PRIVATE LIMITED"
    )

    # ================= HEADER =================
    pdf.setFont("Helvetica", 9)

    # Address (Left)
    left_texts = [
        "50/4,",
        "Atal Chowk, Main Road Boria Khurd,",
        "Near Durga Mandir, Raipur,",
        "Chhattisgarh, 492017,",
        "India"
    ]
    for i, line in enumerate(left_texts):
        pdf.drawString(margin, height - 120 - i * 12, line)

    # Logo (Center)
    logo_path = os.path.join(settings.BASE_DIR, "static/images/logo.png")
    if os.path.exists(logo_path):
        pdf.drawImage(
            logo_path,
            (width - 100) / 2 - 30,
            height - 190,
            width=100,
            height=100,
            mask="auto"
        )

    # GST & Contact (Right)
    right_texts = [
        "GSTN 22ABDCS6806R2ZV",
        "9074307248",
        "shrirajproperty00@gmail.com",
        "shrirajteam.com"
    ]
    for i, line in enumerate(right_texts):
        pdf.drawRightString(width - margin, height - 120 - i * 12, line)

    # ================= TAX INVOICE =================
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawRightString(width - margin, height - 180, "Tax Invoice")

    # ================= INVOICE INFO =================
    pdf.setFont("Helvetica", 9)
    info_data = [
        ["Invoice No", transaction.document_number, "Name", f"{user.first_name} {user.last_name}"],
        ["Invoice Date", datetime.today().strftime('%d/%m/%Y'), "Email", user.email],
        ["Phone", getattr(user, "phone_number", ""), "", ""],
    ]

    info_table = Table(
        info_data,
        colWidths=[
            table_width * 0.20,
            table_width * 0.30,
            table_width * 0.15,
            table_width * 0.35,
        ]
    )

    info_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))

    info_table.wrapOn(pdf, width, height)
    info_table.drawOn(pdf, margin, height - 300)

    # ================= PRODUCT TABLE =================
    product_table_data = [
        ["S No", "Item", "Qty", "Price", "Total"]
    ]

    for idx, item in enumerate(order.items.all(), start=1):

        if item.variant:
            product = item.variant.product
            attrs = format_variant_attributes(item.variant.attributes)
            item_name = f"{product.product_name} ({attrs})"
        else:
            p = item.property_item
            item_name = f"{p.property_title}"

        product_table_data.append([
            str(idx),
            item_name,
            str(item.quantity),
            f"{item.price:.2f}",
            f"{(item.price * item.quantity):.2f}"
        ])

    product_table = Table(
        product_table_data,
        colWidths=[
            table_width * 0.08,
            table_width * 0.42,
            table_width * 0.10,
            table_width * 0.20,
            table_width * 0.20,
        ]
    )

    product_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (2, 1), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))

    product_table.wrapOn(pdf, width, height)
    product_table.drawOn(pdf, margin, height - 380)

    # ================= TOTAL =================
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawRightString(
        width - margin,
        height - 380 - (len(product_table_data) * 20),
        f"Grand Total: {order.total_amount:.2f}"
    )

    # ================= FOOTER =================
    footer_y = height - 500
    pdf.setFont("Helvetica", 9)
    footer_lines = [
        "For any queries, please contact",
        "Email - shrirajproperty00@gmail.com",
        "Contact - 9074307248",
    ]

    for i, line in enumerate(footer_lines):
        pdf.drawString(margin, footer_y - i * 12, line)

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    transaction.document_file.save(
        f"{transaction.document_number}.pdf",
        ContentFile(buffer.read())
    )





from io import BytesIO
from datetime import datetime
import os

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from django.conf import settings
from django.core.files.base import ContentFile


def generate_product_invoice_pdf(transaction, order, user):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 40
    table_width = width - 2 * margin

    # =================================================
    # PARAGRAPH STYLE (FOR AUTO WRAPPING ITEM COLUMN)
    # =================================================
    styles = getSampleStyleSheet()
    item_style = styles["Normal"]
    item_style.fontName = "Helvetica"
    item_style.fontSize = 9
    item_style.leading = 12
    item_style.wordWrap = "CJK"

    # ================= COMPANY NAME =================
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(
        width / 2,
        height - 50,
        "SHRIRAJ PROPERTY SOLUTIONS PRIVATE LIMITED"
    )

    # ================= HEADER =================
    pdf.setFont("Helvetica", 9)

    # Address (Left)
    left_texts = [
        "50/4,",
        "Atal Chowk, Main Road Boria Khurd,",
        "Near Durga Mandir, Raipur,",
        "Chhattisgarh, 492017,",
        "India"
    ]
    for i, line in enumerate(left_texts):
        pdf.drawString(margin, height - 120 - i * 12, line)

    # Logo (Center)
    logo_path = os.path.join(settings.BASE_DIR, "static/images/logo.png")
    if os.path.exists(logo_path):
        pdf.drawImage(
            logo_path,
            (width - 100) / 2 - 30,
            height - 190,
            width=100,
            height=100,
            mask="auto"
        )

    # GST & Contact (Right)
    right_texts = [
        "GSTN 22ABDCS6806R2ZV",
        "9074307248",
        "shrirajproperty00@gmail.com",
        "shrirajteam.com"
    ]
    for i, line in enumerate(right_texts):
        pdf.drawRightString(width - margin, height - 120 - i * 12, line)

    # ================= TAX INVOICE =================
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawRightString(width - margin, height - 180, "Tax Invoice")

    # ================= INVOICE INFO =================
    pdf.setFont("Helvetica", 9)
    info_data = [
        ["Invoice No", transaction.document_number, "Name", f"{user.first_name} {user.last_name}"],
        ["Invoice Date", datetime.today().strftime('%d/%m/%Y'), "Email", user.email],
        ["Phone", getattr(user, "phone_number", ""), "", ""],
    ]

    info_table = Table(
        info_data,
        colWidths=[
            table_width * 0.20,
            table_width * 0.30,
            table_width * 0.15,
            table_width * 0.35,
        ]
    )

    info_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))

    info_table.wrapOn(pdf, width, height)
    info_table.drawOn(pdf, margin, height - 300)

    # ================= PRODUCT TABLE =================
    product_table_data = [
        ["S No", "Item", "Qty", "Price", "Total"]
    ]

    for idx, item in enumerate(order.items.all(), start=1):

        # ---------- ITEM NAME (AUTO WRAP) ----------
        if item.variant:
            product = item.variant.product
            attrs = format_variant_attributes(item.variant.attributes)

            item_name = Paragraph(
                f"<b>{product.product_name}</b><br/>{attrs}",
                item_style
            )
        else:
            p = item.property_item
            item_name = Paragraph(
                f"<b>{p.property_title}</b>",
                item_style
            )

        product_table_data.append([
            str(idx),
            item_name,
            str(item.quantity),
            f"{item.price:.2f}",
            f"{(item.price * item.quantity):.2f}"
        ])

    product_table = Table(
        product_table_data,
        colWidths=[
            table_width * 0.08,
            table_width * 0.42,
            table_width * 0.10,
            table_width * 0.20,
            table_width * 0.20,
        ]
    )

    product_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (2, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))

    product_table.wrapOn(pdf, width, height)
    product_table.drawOn(pdf, margin, height - 380)

    # ================= TOTAL =================
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawRightString(
        width - margin,
        height - 380 - (len(product_table_data) * 20),
        f"Grand Total: {order.total_amount:.2f}"
    )

    # ================= FOOTER =================
    footer_y = height - 500
    pdf.setFont("Helvetica", 9)
    footer_lines = [
        "For any queries, please contact",
        "Email - shrirajproperty00@gmail.com",
        "Contact - 9074307248",
    ]

    for i, line in enumerate(footer_lines):
        pdf.drawString(margin, footer_y - i * 12, line)

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    transaction.document_file.save(
        f"{transaction.document_number}.pdf",
        ContentFile(buffer.read())
    )
