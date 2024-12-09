import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

OET_EMAIL_PASSWORD = os.environ.get("OET_EMAIL_PASSWORD")

def send_email(user_email, html_content):
    
    smtp = smtplib.SMTP("mail.smtp2go.com", 587)

    smtp.starttls()

    smtp.login("oetspeakingsummary", OET_EMAIL_PASSWORD)
 
    msg = MIMEMultipart("related")
    msg["Subject"] = "Summary of OET Speaking Mock Test - Benchmark"
    msg["From"] = "info@edubenchmark.com"
    msg["To"] = user_email
    msg["X-Mailer"] = "Benchmark Education Solutions"

    html = MIMEText(html_content, "html")

    msg.attach(html)

    smtp.send_message(msg)

    smtp.quit()

    return "Email has been sent successfully!"