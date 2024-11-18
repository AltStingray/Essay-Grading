import smtplib
from email.message import EmailMessage

def send_email(user_email, html_content):
    
    smtp = smtplib.SMTP("smtp.gmail.com", 587)

    smtp.starttls()

    email_password = "ccvsaldikydyktgk"

    smtp.login("altstingray@gmail.com", email_password)

    msg = EmailMessage()
    msg["Subject"] = "Your OET Summary Report"
    msg["From"] = "altstingray@gmail.com"
    msg["To"] = user_email
    msg.set_content(html_content)

    smtp.send_message(msg)

    smtp.quit()

    return "Email has been sent successfully!"