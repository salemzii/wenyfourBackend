
import base64
from email.mime.text import MIMEText
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from requests import HTTPError

import smtplib
from email.mime.text import MIMEText

# Email configuration
smtp_server = 'smtp-relay.gmail.com'
smtp_port = 587  # or 465 for SSL
from_email = 'support@wenyfour.com'
to_email = 'salemododa2@gmail.com'
subject = 'Test Email'
body = 'This is a test email from Google Workspace SMTP relay.'

# Create the email content
msg = MIMEText(body)
msg['Subject'] = subject
msg['From'] = from_email
msg['To'] = to_email

# Send the email
with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()
    #server.login('support@wenyfour.com', '!Wenyfour@2024')  # if authentication required
    server.sendmail(from_email, [to_email], msg.as_string())

