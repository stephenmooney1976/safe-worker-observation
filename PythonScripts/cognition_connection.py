"""
Created on Fri Feb 11 14:55:39 2022
@author: Stephen Mooney
"""
import json
import msal
from msal_extensions import *
import pandas as pd
import sys
import requests
import credentials
from utils import ComplianceDownloadException
from database_connections import sqlite_file_cur

AZURE_APP_DOMAIN = 'dteenergy.onmicrosoft.com'
LOGIN_AUTHORITY = f'https://login.microsoftonline.com/{AZURE_APP_DOMAIN}'


def msal_persistence(location, fallback_to_plaintext=False):
    """
        Build suitable persistence instance based on current os.
    """
    if sys.platform.startswith('win'):
        return FilePersistenceWithDataProtection(location)
    if sys.platform.startswith('darwin'):
        return KeychainPersistence(location, "my_service_name", "my_account_name")
    return FilePersistence(location)


def get_api_responses(week_dic=None):
    """
        Initiate GET requests with cognition api's to retrieve SWO data for three weeks.
        Updates and returns week_dic with nine dataframes total.
        Three dataframes (compliance, paired, pandemic) for each of the three weeks.
        Raises custom exception if record count of compliance download is plus or minus 10% of previous count.
    """
    persistence = msal_persistence('token_cache.bin')
    cache = PersistedTokenCache(persistence)
    app = msal.ConfidentialClientApplication(
        client_id=credentials.CLIENT_ID
        , authority=LOGIN_AUTHORITY
        , token_cache=cache
        , client_credential=credentials.SECRET
    )

    res = app.acquire_token_by_username_password(
        username=credentials.USERNAME,
        password=credentials.PASSWORD,
        scopes=[f'api://{credentials.SWO_CLIENT_ID}/.default']
    )
    headers = {'Authorization': f'Bearer {res["access_token"]}', 'Content-Type': 'application/json'}

    for week, inner_dic in week_dic.items():
        start = inner_dic['start_api_str']
        end = inner_dic['end_api_str']
        api_dict = {
            'compliance': {
                'url': f'https://cognition.dteenergy.com/api/v1/reports/responses/export/leader-compliance?azureId=c21b67de-187e-4bab-8876-36994b951dc7&endDate={end}&startDate={start}'},
            'paired': {
                'url': f'https://cognition.dteenergy.com/api/v1/reports/responses/export/epo/single-line?azureId=c21b67de-187e-4bab-8876-36994b951dc7&endDate={end}&observationType=employee-performing-observation&questionnaireId=5&startDate={start}'},
            'pandemic': {
                'url': f'https://cognition.dteenergy.com/api/v1/reports/responses/export/epo/single-line?azureId=c21b67de-187e-4bab-8876-36994b951dc7&endDate={end}&observationType=employee-performing-observation&questionnaireId=11&startDate={start}'}
        }
        for api, dic in api_dict.items():
            api_response = requests.get(dic['url'], headers=headers)
            api_text = api_response.text
            json_obj = json.loads(api_text)
            df = pd.read_csv(json_obj['url'])
            if api == 'compliance':
                prev_count = sqlite_file_cur.execute(
                    "SELECT Record_Count FROM ComplianceHistory ORDER BY Date_Time DESC").fetchone()[0]
                current_count = len(df.index)
                diff = abs((prev_count - current_count) / float(prev_count))
                if diff > 0.10:
                    raise ComplianceDownloadException(
                        f'Current Count: {current_count} | Previous Count: {prev_count} | Difference: {round(diff * 100, 2)}%'
                    )
            inner_dic['_'.join([api, 'df'])] = df
    return week_dic
