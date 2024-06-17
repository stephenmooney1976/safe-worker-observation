import sys
import sqlite3
import cx_Oracle
import traceback
from logger import error_logger
import credentials
from email_notifications import send_email, est_tz_time_stamp

try:
    sqlite_file_con = sqlite3.connect('../data/sqlite/swo_db.sqlite')
    sqlite_file_cur = sqlite_file_con.cursor()

    sqlite_con = sqlite3.connect(':memory:')
    sqlite_cur = sqlite_con.cursor()

    xdo_connection_string = credentials.CONNECTION_STRING
    xdo_con = cx_Oracle.connect(xdo_connection_string)
    xdo_cur = xdo_con.cursor()

except Exception:
    fail_str = 'Database Connection Failed'
    stack_trace = traceback.format_exc()
    error_logger.error(f'{fail_str}\n{stack_trace}{"=" * 120}')
    send_email(
        subject=fail_str,
        message=f'{fail_str} @ {est_tz_time_stamp()}\n{fail_str}\n{stack_trace}')
    sys.exit(f'{fail_str}\n{stack_trace}')
