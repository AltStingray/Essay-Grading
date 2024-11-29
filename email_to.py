import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

def send_email(user_email, html_content):
    
    smtp = smtplib.SMTP("mail.smtp2go.com", 587)

    smtp.starttls()

    #email_password = "u99W1dmIHBPLslPX"
    #oetspeakingsummary@mail
    email_password = "ccvsaldikydyktgk"
    #altstingray@gmail.com

    smtp.login("altstingray@gmail.com", email_password)

    msg = MIMEMultipart("related")
    msg["Subject"] = "Your OET Summary Report"
    msg["From"] = "altstingray@gmail.com"
    msg["To"] = user_email

    html = MIMEText(html_content, "html")

    msg.attach(html)

    # Image
    logo = "static/finalblue.jpeg"

    with open(logo, "rb") as img:
        image = MIMEImage(img.read())
        image.add_header("Content-ID", "header_image")
        image.add_header("Content-Disposition", "inline", filename=logo)
        msg.attach(image)

    smtp.send_message(msg)

    smtp.quit()

    return "Email has been sent successfully!"