import smtplib, ssl
import subprocess
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from .models import MailTemplate

SMTP_PORT = 465 
SMTP_SERVER = "smtp.gmail.com"
SENDER = "ScanX <scanx.cloud@gmail.com>"
GMAIL = "scanx.cloud@gmail.com"
GMAIL_PASS = "abc@123@def"

def sendMail2(to, subject, body):

    proc = subprocess.Popen(['mail',
                 '-s', f'{subject}\nContent-Type: text/html', 
                 '-a', f'From: {SENDER}',
                 to],
             stdin=subprocess.PIPE)
    proc.stdin.write(body.encode())
    proc.stdin.close()

def sendMail(to, subject, body):

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = SENDER
    msg['To'] = to
    msg.attach(MIMEText(body, 'html'))
    
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(GMAIL, GMAIL_PASS)
        server.sendmail(GMAIL, to, msg.as_string())
        

def getMailTemplate(template_code):
    mail_template = MailTemplate.objects.filter(code=template_code).first()
    if mail_template:
        return mail_template.subject, mail_template.body
    
    return '', ''

def sendResellerInvitationMail(fullname, email, password):
    try:
        subject, body = getMailTemplate(settings.MAIL_TEMPLATE_CODES['RESELLER_INVITATION'])

        html = body.replace('${Link.ACCEPT_INVITATION}', settings.INVITE_URL + f'?email={email}')
        html = html.replace('${User.FULL_NAME}', fullname)
        html = html.replace('${User.PASSWORD}', password)

        sendMail(email, subject, html)
    except:
        traceback.print_exc()

def sendAdminInvitationMail(organization, fullname, email, password):
    try:
        subject, body = getMailTemplate(settings.MAIL_TEMPLATE_CODES['ADMIN_INVITATION'])

        html = body.replace('${Link.ACCEPT_INVITATION}', settings.INVITE_URL + f'?email={email}')
        html = html.replace('${User.ORGANIZATION}', organization)
        html = html.replace('${User.FULL_NAME}', fullname)
        html = html.replace('${User.PASSWORD}', password)

        sendMail(email, subject, html)
    except:
        traceback.print_exc()

def sendInvitationMail(organization, fullname, email, password):
    try:
        subject, body = getMailTemplate(settings.MAIL_TEMPLATE_CODES['USER_INVITATION'])

        html = body.replace('${Link.ACCEPT_INVITATION}', settings.INVITE_URL + f'?email={email}')
        html = html.replace('${User.ORGANIZATION}', organization)
        html = html.replace('${User.FULL_NAME}', fullname)
        html = html.replace('${User.PASSWORD}', password)

        sendMail(email, subject, html)
    except:
        traceback.print_exc()

def sendResetPasswordMail(fullname, email, password):
    try:
        subject, body = getMailTemplate(settings.MAIL_TEMPLATE_CODES['RESET_PASSWORD'])

        html = body.replace('${Link.RESET_PASSWORD}', settings.RESET_PASSWORD_URL + f'?email={email}&token={password}')
        html = html.replace('${User.FULL_NAME}', fullname)

        sendMail(email, subject, html)
    except:
        traceback.print_exc()        


def sendAdminCreateNotificationMail(fullname, email, newFullname, newEmail):
    try:
        subject, body = getMailTemplate(settings.MAIL_TEMPLATE_CODES['ADMIN_CREATE_NOTIFICATION'])

        html = body.replace('${User.FULL_NAME}', fullname)
        html = html.replace('${NewUser.FULL_NAME}', newFullname)
        html = html.replace('${NewUser.EMAIL}', newEmail)

        sendMail(email, subject, html)
    except:
        traceback.print_exc()        


