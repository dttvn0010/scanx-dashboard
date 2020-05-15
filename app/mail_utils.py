import smtplib, ssl
from email.mime.text import MIMEText
from .consts import ADMIN_MAIL_TEMPLATE_PATH, MAIL_TEMPLATE_PATH

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
    html = ADMIN_INVITE_TEMPLATE.replace('${Link.ACCEPT_INVITATION}', hostURL)
    html = html.replace('${User.ORGANIZATION}', organization)
    html = html.replace('${User.FULL_NAME}', fullname)
    html = html.replace('${User.PASSWORD}', password)

    msg = MIMEText(html, 'html')
    msg['Subject'] = INVITE_TITLE
    msg['From'] = 'ScanX'

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())

def sendInvitationMail(hostURL, organization, fullname, email, password):
    html = INVITE_TEMPLATE.replace('${Link.ACCEPT_INVITATION}', hostURL)
    html = html.replace('${User.ORGANIZATION}', organization)
    html = html.replace('${User.FULL_NAME}', fullname)
    html = html.replace('${User.PASSWORD}', password)

    msg = MIMEText(html, 'html')
    msg['Subject'] = INVITE_TITLE
    msg['From'] = 'ScanX'

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())