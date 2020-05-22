import smtplib, ssl
import subprocess
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from .consts import ADMIN_MAIL_TEMPLATE_PATH, MAIL_TEMPLATE_PATH

HOST_URL = "https://scanx.cloud"
INVITE_TITLE = 'Invitation to join ScanX'

with open(ADMIN_MAIL_TEMPLATE_PATH, encoding="utf-8") as fi:
    ADMIN_INVITE_TEMPLATE = fi.read()

with open(MAIL_TEMPLATE_PATH, encoding="utf-8") as fi:
    INVITE_TEMPLATE = fi.read()

SMTP_PORT = 465 
SMTP_SERVER = "smtp.gmail.com"
SENDER_EMAIL = "ScanX <contact@screenx.cloud>"
GMAIL = "dttvn0010@gmail.com"
GMAIL_PASS = "Ab01234567"

def sendMail(fro, to, subject, body):
    proc = subprocess.Popen(['mail',
                 '-s', f'{subject}\nContent-Type: text/html', 
                 '-a', f'From: {fro}',
                 to],
             stdin=subprocess.PIPE)
    proc.stdin.write(body.encode())
    proc.stdin.close()

def sendMail2(fro, to, subject, body):
    context = ssl.create_default_context()

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = fro
    msg.attach(MIMEText(body, 'html'))
    
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(GMAIL, GMAIL_PASS)
        server.sendmail(fro, to, msg.as_string())

def sendAdminInvitationMail(hostURL, organization, fullname, email, password):
    try:
        html = ADMIN_INVITE_TEMPLATE.replace('${Link.ACCEPT_INVITATION}', HOST_URL)
        html = html.replace('${User.ORGANIZATION}', organization)
        html = html.replace('${User.FULL_NAME}', fullname)
        html = html.replace('${User.PASSWORD}', password)

        sendMail(SENDER_EMAIL, email, INVITE_TITLE, html)
    except:
        traceback.print_exc()

def sendInvitationMail(hostURL, organization, fullname, email, password):
    try:
        html = INVITE_TEMPLATE.replace('${Link.ACCEPT_INVITATION}', HOST_URL)
        html = html.replace('${User.ORGANIZATION}', organization)
        html = html.replace('${User.FULL_NAME}', fullname)
        html = html.replace('${User.PASSWORD}', password)

        sendMail(SENDER_EMAIL, email, INVITE_TITLE, html)
    except:
        traceback.print_exc()