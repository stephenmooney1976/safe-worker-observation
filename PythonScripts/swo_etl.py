#!/usr/bin/env python
import sys
import time
import traceback
from cognition_connection import get_api_responses
from database_connections import sqlite_con, xdo_con
from logger import execution_logger, error_logger
from email_notifications import send_email, est_tz_time_stamp
from utils import *


def main():
    """
        Calls cognition_connection.py and utils.py functions.
    """
    week_ranges = build_three_week_range()
    read_excel_to_sqlite()
    api_res_dic = get_api_responses(week_dic=week_ranges)
    df_to_sqlite(api_dic=api_res_dic)
    for week in WEEK_LIST:
        final_df = sqlite_to_df(week)
        num_rows, period = commit_to_xdo(df_week=final_df)
        execution_logger.info(f'Post Commit | {num_rows:3} rows | {period}')


def main_wrapper():
    """
        Execution of main is nested in try block that logs run and elapsed time to execution_log.txt.
        Except block catches all exceptions and logs to error_log.txt
        Finally block performs clean up of gracefully closing any open database connections.
    """
    try:
        start = time.perf_counter()
        main()
        end = time.perf_counter()
        elapsed = round(end - start, 2)
        execution_logger.info(f'Elapsed Time: {elapsed} seconds\n{"=" * 120}')
    except Exception:
        fail_str = 'Safe Worker Observation Failed'
        stack_trace = traceback.format_exc()
        send_email(
            subject=fail_str,
            message=f'{fail_str} @ {est_tz_time_stamp()}\n{stack_trace}')
        error_logger.error(f'{fail_str}\n{stack_trace}{"=" * 120}')
        sys.exit(f'{fail_str}{stack_trace}')
    else:
        success_str = 'Safe Worker Observation Successful'
        send_email(
            subject=success_str,
            message=f'{success_str} @ {est_tz_time_stamp()}\nCompleted in {elapsed} seconds')
    finally:
        sqlite_con.close()
        xdo_con.close()


if __name__ == '__main__':
    main_wrapper()
    print('end of program')
