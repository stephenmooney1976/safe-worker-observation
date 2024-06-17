import sys
import traceback
import numpy as np
import pandas as pd
import configparser
import datetime as dt
from logger import execution_logger, TZ, error_logger
from database_connections import sqlite_con, sqlite_cur, sqlite_file_con, sqlite_file_cur, xdo_con, xdo_cur

pd.set_option("expand_frame_repr", False)
config = configparser.ConfigParser()
config.optionxform = str
config.read('../config/spreadsheet_locs.properties')
WEEK_LIST = ['ThisWeek', 'LastWeek', 'WeekBeforeLast']


class BaseCustomException(Exception):
    """Base super class that formats display of exception messages"""
    def __init__(self, message):
        super().__init__(message)


class ComplianceDownloadException(BaseCustomException):
    """Raised when current compliance download record count is plus or minus more than 10% from previous."""

    def __init__(self, message):
        super().__init__(message)


class OracleDeletionException(BaseCustomException):
    """Raised when count of rows after delete does not equal zero."""

    def __init__(self, message):
        super().__init__(message)


def build_three_week_range():
    """
        Builds ranges for current week and previous two.
        Weeks start on Monday and end on Sunday.
    """
    today = pd.Timestamp.today().date()
    date_dict = dict()
    for i, week in enumerate(WEEK_LIST):
        mon_dt = today - dt.timedelta(days=today.weekday() + (i * 7))
        sun_dt = mon_dt + dt.timedelta(days=6)
        mon_str = '{d.month}/{d.day}/{d.year}'.format(d=mon_dt)
        sun_str = '{d.month}/{d.day}/{d.year}'.format(d=sun_dt)
        date_dict[week] = dict(
            start_dt=mon_dt, end_dt=sun_dt,
            start_str=mon_str, end_str=sun_str,
            period_str=f'{mon_str} - {sun_str}',
            start_api_str=mon_dt.strftime('%Y-%m-%d'),
            end_api_str=sun_dt.strftime('%Y-%m-%d'),
        )
    return date_dict


def df_to_sqlite(api_dic=None):
    """
        Parses api_dic and transforms all nine dataframes before writing to in memory SQLite instance.
    """
    conv_dic = {
        'Sap ID': int,
        'Completed': int,
        'Expected': int,
        'Leader Compliance': int,
    }
    for week, inner_dic in api_dic.items():
        tmp_df = inner_dic['compliance_df'].copy()
        indexes = tmp_df[tmp_df['Sap ID'].isnull()].index
        tmp_df.drop(indexes, inplace=True)
        tmp_df.drop('Expected Observations Per Week', axis=1, inplace=True)
        tmp_df.rename(columns={tmp_df.columns[6]: 'UNKNOWN'}, inplace=True)
        tmp_df.rename(columns={'Actual Weeks Compliant': 'Completed'}, inplace=True)
        tmp_df.rename(columns={'Expected Weeks Compliant': 'Expected'}, inplace=True)
        tmp_df.insert(7, 'Period', inner_dic['period_str'], allow_duplicates=True)
        tmp_df.loc[(tmp_df['Leader Compliance'] == 'Indeterminate') |
                   (tmp_df['Leader Compliance'] == '0%'),
                   'Leader Compliance'] = '0'
        tmp_df.loc[tmp_df['Leader Compliance'] == '100%', 'Leader Compliance'] = '1'
        comp_df = tmp_df.astype(conv_dic)
        comp_len = len(comp_df)
        pair_df = inner_dic['paired_df'].iloc[:, 0:19]
        pan_df = inner_dic['pandemic_df'].iloc[:, 0:19]
        record = (comp_len, dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), inner_dic['period_str'])
        sqlite_file_cur.execute("INSERT INTO ComplianceHistory VALUES (?, ?, ?);", record)
        sqlite_file_con.commit()
        comp_df.to_sql(f'Compliance{week}', sqlite_con, if_exists='replace', index=False)
        pair_df.to_sql(f'Paired{week}', sqlite_con, if_exists='replace', index=False)
        pan_df.to_sql(f'Pandemic{week}', sqlite_con, if_exists='replace', index=False)


def read_excel_to_sqlite():
    """
        Parses ini style properties file to read Do_Org_Linked and Do Target-Master spreadsheets
         into dataframes and commits them to SQLite instance.
    """
    sections = config.sections()
    for section in sections:
        xcel_files = config.items(section)
        for xcel_file in xcel_files:
            key, path = xcel_file
            file_name, tab = key.split('.')
            df = pd.read_excel(path, sheet_name=tab)
            df.to_sql(file_name, sqlite_con, if_exists='replace', index=False)


def sqlite_to_df(week=None):
    """
        Queries in memory SQLite tables to coalesce and aggregate SWO data into three dataframes.
    """
    qryselect = f'qrySelect{week}'
    qryappend = f'qryAppend{week}'
    compliancetable = f'Compliance{week}'
    pairedtable = f'Paired{week}'
    pandemictable = f'Pandemic{week}'
    sql_select_str = f'''
              SELECT
                a.Name           
              , a.[SAP ID]   
              , a.Email              
              , a.Title           
              , a.[Direct Supervisor]                                                                                                                                                            
              , a.Director
              , a.UNKNOWN
              , a.Period                                                                                                     
              , a.Completed
              , a.Expected
              , a.[Leader Compliance]           
              , Count(b.[Observer Employee ID]) AS [CountOfObserver Employee ID]
              , d.[COVID Requirement]
              , d.[DO Elevated]                                                           
              , d.[JULY2020 Requirement]                                                        
              , d.[Dec2020 Requirement]                   
                FROM
                    {compliancetable} a 
                    LEFT JOIN {pairedtable} b ON a.[Sap ID] = b.[Observer Employee ID]
                    LEFT JOIN DoOrgLinked c ON a.[SAP ID] = c.SAPID                                                                                                                        
                    LEFT JOIN DoTargetMaster d ON UPPER(c.USER_ID) = UPPER(d.[User ID])                              
                GROUP BY                                                   
                  a.Name                           
                  , a.[Sap ID]                       
                  , a.Email                                
                  , a.Title                                   
                  , a.[Direct Supervisor]                     
                  , a.Director                                
                  , a.UNKNOWN                                 
                  , a.Period                                  
                  , a.Completed                               
                  , a.Expected                                
                  , a.[Leader Compliance]                                             
                  , d.[COVID Requirement]
                  , d.[DO Elevated]                      
                  , d.[JULY2020 Requirement]                   
                  , d.[Dec2020 Requirement]; 
              '''

    sql_append_str = f'''
            SELECT 
                  a.Name
                , a.[Sap ID]
                , a.Email
                , a.Title
                , a.[Direct Supervisor]
                , a.Director
                , a.UNKNOWN
                , a.Period
                , a.Completed
                , a.Expected
                , a.[Leader Compliance]
                , a.[CountOfObserver Employee ID] AS PAIRED
                , COUNT(b.[Observer Employee ID]) AS PANDEMIC
                , a.[COVID Requirement]
                , a.[DO Elevated]
                , a.[JULY2020 Requirement]
                , a.[Dec2020 Requirement]
            FROM 
                {qryselect} a
            LEFT JOIN {pandemictable} b ON a.[Sap ID] = b.[Observer Employee ID]
            GROUP BY 
                a.Name, 
                a.[Sap ID], 
                a.Email, 
                a.Title, 
                a.[Direct Supervisor], 
                a.Director, 
                a.UNKNOWN, 
                a.Period, 
                a.Completed, 
                a.Expected, 
                a.[Leader Compliance], 
                a.[CountOfObserver Employee ID],
                a.[COVID Requirement], 
                a.[DO Elevated], 
                a.[JULY2020 Requirement], 
                a.[Dec2020 Requirement];
            '''
    df_select = pd.DataFrame(sqlite_cur.execute(sql_select_str), columns=[c[0] for c in sqlite_cur.description])
    df_select.to_sql(qryselect, sqlite_con, if_exists='replace', index=False)

    df_append = pd.DataFrame(sqlite_cur.execute(sql_append_str), columns=[c[0] for c in sqlite_cur.description])
    df_append.to_sql(qryappend, sqlite_con, if_exists='replace', index=False)
    final_df = df_append.replace(np.nan, None)
    return final_df


def commit_to_xdo(df_week=None):
    """
        Receives final dataframes for all three weeks.
        Writes current record count to ComplianceHistory table in SQLite file on disk.
        Deletes existing records and writes updated ones to XDO.SWO_COMPLIANCE table on dv46.
    """
    xdo_sql_str = """
                      insert into XDO.SWO_COMPLIANCE VALUES(
                      :1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13, :14, :15, :16, :17
                      )
                  """
    week_list = df_week.values.tolist()
    period = df_week.iloc[0].Period
    for i, row in enumerate(week_list):
        if i == 0:
            del_sql_str = f"delete from SWO_COMPLIANCE WHERE PERIOD like '{period}'"
            xdo_cur.execute(del_sql_str)
            delete_count = xdo_cur.execute(
                f"select COUNT(*) from SWO_COMPLIANCE WHERE PERIOD like '{period}'").fetchone()[0]
            if delete_count != 0:
                raise OracleDeletionException(
                    f'Current Count: {delete_count} | Expected Count: 0'
                )
            execution_logger.info(f'Post Delete | {delete_count:3} rows | {period}')
        xdo_cur.execute(xdo_sql_str, row)
    commit_count = xdo_cur.execute(
        f"select COUNT(*) from SWO_COMPLIANCE WHERE PERIOD like '{period}'").fetchone()[0]
    xdo_con.commit()
    return commit_count, period
