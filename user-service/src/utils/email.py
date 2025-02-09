import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..config.environment import env

def send_email(to_email: str, subject: str, body: str):
    try:
        msg = MIMEMultipart()
        msg["From"] = env.EMAIL_FROM
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        # Connect to Mailtrap's SMTP server
        with smtplib.SMTP(env.SMTP_HOST, env.SMTP_PORT) as server:
            server.ehlo()  # Identify with the mail server
            server.starttls()  # Secure the connection
            server.ehlo()  # Identify again after securing connection
            server.login(env.SMTP_USERNAME, env.SMTP_PASSWORD)  # Authenticate
            server.sendmail(env.EMAIL_FROM, to_email, msg.as_string())

        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False