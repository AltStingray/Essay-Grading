import smtplib
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase

def send_email(user_email, html_content):
    
    smtp = smtplib.SMTP("smtp.gmail.com", 587)

    smtp.starttls()

    email_password = "ccvsaldikydyktgk"
    #info@edubenchmark.com
    smtp.login("altstingray@gmail.com", email_password)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your OET Summary Report"
    msg["From"] = "altstingray@gmail.com"
    msg["To"] = user_email

    html = MIMEText(html_content, "html")

    msg.attach(html)

    # Image
    with open("/static/finalblue.jpeg", "rb") as p:
        photo = MIMEBase("application", "octet-stream")
        photo.set_payload(p.read())

    encoders.encode_base64(photo)

    photo.add_header(
        "Content-Disposition",
        "attachment; filename=/static/finalblue.jpeg",
    )

    msg.attach(photo)

    smtp.send_message(msg)

    smtp.quit()

    return "Email has been sent successfully!"