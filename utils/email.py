import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

def send_bulk_emails(recipients, subject, body_html):
    """
    recipients: List of email addresses.
    subject: Email subject.
    body_html: HTML content of the email.
    """
    sender = Config.SMTP_USER if Config.SMTP_USER else "noreply@aimarketplace.local"
    
    # Connect to SMTP server
    try:
        # If no real auth is provided, we might be using a local MailHog or debug server
        server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
        
        if Config.SMTP_USER and Config.SMTP_PASSWORD:
            server.starttls()
            server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            
        for recipient in recipients:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = recipient
            
            part = MIMEText(body_html, "html")
            msg.attach(part)
            
            server.sendmail(sender, recipient, msg.as_string())
            
        server.quit()
        return True, "Emails sent successfully."
    except ConnectionRefusedError:
        print("\n" + "="*50)
        print("MOCK EMAIL SENT (SMTP Connection Refused)")
        print(f"Subject: {subject}")
        print(f"To: {recipients}")
        print(f"Body: {body_html}")
        print("="*50 + "\n")
        return True, "Email successfully printed to console (Mock)."
    except Exception as e:
        print(f"SMTP Error: {e}")
        return False, str(e)
