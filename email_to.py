import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
    plain_text = MIMEText(plain_text, "plain")

    msg.attach(html)

    smtp.send_message(msg)

    smtp.quit()

    return "Email has been sent successfully!"