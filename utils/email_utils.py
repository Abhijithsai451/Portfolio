import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

def send_contact_email(name: str, email: str, subject: str, message: str) -> bool:
    """
    Sends an email notification when someone uses the contact form.
    """
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    receiver_email = os.getenv("RECEIVER_EMAIL")

    if not all([smtp_server, smtp_user, smtp_password, receiver_email]):
        logger.error("Email configuration is missing in environment variables.")
        return False

    # Create the email content
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = receiver_email
    msg['Subject'] = f"Portfolio Contact: {subject}"

    body = f"""
    You have received a new message from your portfolio contact form:

    Name: {name}
    Email: {email}
    Subject: {subject}

    Message:
    {message}
    """
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to the server and send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure the connection
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        logger.info(f"Email sent successfully to {receiver_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
