import smtplib, ssl
import subprocess
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.conf import settings

HOST_URL = "https://scanx.cloud"
INVITE_TITLE = 'Invitation to join ScanX'

SMTP_PORT = 465 
SMTP_SERVER = "smtp.gmail.com"
SENDER_EMAIL = "ScanX <contact@scanx.cloud>"
GMAIL = "scanx.cloud@gmail.com"
GMAIL_PASS = "abc@123@def"

def sendMail2(fro, to, subject, body):
    print('===============', body)

    proc = subprocess.Popen(['mail',
                 '-s', f'{subject}\nContent-Type: text/html', 
                 '-a', f'From: {fro}',
                 to],
             stdin=subprocess.PIPE)
    proc.stdin.write(body.encode())
    proc.stdin.close()

port = 465  # For SSL
smtp_server = "smtp.gmail.com"
sender_email = "scanx.cloud@gmail.com"
receiver_email = "duongthanhtungvn01@hotmail.com"
password = 'abc@123@def'

def sendMail3(fro, to, subject, body):
    message = """        
       Sample Email sent by Python.
       """

    msg = MIMEText(message)
    msg['Subject'] = 'Mail subject'
    msg['From'] = 'from'
    msg['To'] = 'to'


    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
    
def sendMail(fro, to, subject, body):
    print('===============', body)
   
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
        with open(settings.ADMIN_MAIL_TEMPLATE_PATH, encoding="utf-8") as fi:
            ADMIN_INVITE_TEMPLATE = fi.read()

        html = ADMIN_INVITE_TEMPLATE.replace('${Link.ACCEPT_INVITATION}', HOST_URL)
        html = html.replace('${User.ORGANIZATION}', organization)
        html = html.replace('${User.FULL_NAME}', fullname)
        html = html.replace('${User.PASSWORD}', password)

        sendMail(SENDER_EMAIL, email, INVITE_TITLE, html)
    except:
        traceback.print_exc()

def sendInvitationMail(hostURL, organization, fullname, email, password):
    try:
        with open(settings.MAIL_TEMPLATE_PATH, encoding="utf-8") as fi:
            INVITE_TEMPLATE = fi.read()

        html = INVITE_TEMPLATE.replace('${Link.ACCEPT_INVITATION}', HOST_URL)
        html = html.replace('${User.ORGANIZATION}', organization)
        html = html.replace('${User.FULL_NAME}', fullname)
        html = html.replace('${User.PASSWORD}', password)

        sendMail(SENDER_EMAIL, email, INVITE_TITLE, html)
    except:
        traceback.print_exc()