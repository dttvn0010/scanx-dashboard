import smtplib, ssl
import traceback
from email.mime.text import MIMEText, MIMEMultipart
from .consts import ADMIN_MAIL_TEMPLATE_PATH, MAIL_TEMPLATE_PATH

HOST_URL = "https://scanx.cloud"
INVITE_TITLE = 'Invitation to join ScanX'

with open(ADMIN_MAIL_TEMPLATE_PATH, encoding="utf-8") as fi:
    ADMIN_INVITE_TEMPLATE = fi.read()

with open(MAIL_TEMPLATE_PATH, encoding="utf-8") as fi:
    INVITE_TEMPLATE = fi.read()

SMTP_PORT = 465 
SMTP_SERVER = "smtp.gmail.com"
SENDER_EMAIL = "dttvn0010@gmail.com"
SENDER_PASSWORD = "Ab01234567"

def sendAdminInvitationMail(hostURL, organization, fullname, email, password):
    try:
        html = ADMIN_INVITE_TEMPLATE.replace('${Link.ACCEPT_INVITATION}', HOST_URL)
        html = html.replace('${User.ORGANIZATION}', organization)
        html = html.replace('${User.FULL_NAME}', fullname)
        html = html.replace('${User.PASSWORD}', password)

        #msg = MIMEText(html, 'html')
        msg = MIMEMultipart('alternative')
        msg['Subject'] = INVITE_TITLE
        msg['From'] = 'ScanX'
        msg.attach(MIMEText(html, 'html'))

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, email, msg.as_string())
    except:
        traceback.print_exc()

def sendInvitationMail(hostURL, organization, fullname, email, password):
    try:
        html = INVITE_TEMPLATE.replace('${Link.ACCEPT_INVITATION}', HOST_URL)
        html = html.replace('${User.ORGANIZATION}', organization)
        html = html.replace('${User.FULL_NAME}', fullname)
        html = html.replace('${User.PASSWORD}', password)

        #msg = MIMEText(html, 'html')
        msg = MIMEMultipart('alternative')
        msg['Subject'] = INVITE_TITLE
        msg['From'] = 'ScanX'
        msg.attach(MIMEText(html, 'html'))

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, email, msg.as_string())
    except:
        traceback.print_exc()