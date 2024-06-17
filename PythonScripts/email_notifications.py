import sys
import smtplib
import traceback
import datetime as dt
from email.message import EmailMessage
from logger import error_logger
from utils import TZ


def est_tz_time_stamp():
    return dt.datetime.now().astimezone(TZ).strftime('%Y-%m-%d %H:%M:%S')


def send_email(subject=None, message=None):
    fail_str = 'Email Notification Failed:'
    stack_trace = traceback.format_exc()
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = 'DO_PERFORMANCE_CENTER@dteenergy.com'
    msg['To'] = ['christopher.maher@dteenergy.com', 'stephen.mooney@dteenergy.com',
                 'yong.li@dteenergy.com', 'hassan.fawaz@dteenergy.com', 'joseph.naiman@dteenergy.com']
    msg.set_content(message)

    try:
        with smtplib.SMTP('smtp.dteco.com', 25) as smtp:
            smtp.send_message(msg)
    except smtplib.SMTPException:
        error_logger.error(f'{fail_str}\n{stack_trace}{"=" * 120}')
        sys.exit(f'{fail_str}\n{stack_trace}')
