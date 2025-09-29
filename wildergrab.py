# -*- coding: utf-8 -*-
"""
Created on Thu May 19 08:40:34 2022

@author: lfullard
"""

#api stuff
import pandas as pd
import requests
from aws_requests_auth.aws_auth import AWSRequestsAuth
from io import StringIO
import unicodedata


###############################################################################
###############################################################################
###############################################################################
#user settings
save_location = 'eDNA_Data_September_2025.xlsx'
include_jobs    = True
include_samples = True
include_taxa    = True
include_records = True

def api_credentials() -> tuple[str, str, str]:
    """
    Return AWS and API credentials.

    This function first tries to read credentials from environment variables:
      - WILDERLAB_AWS_ACCESS_KEY
      - WILDERLAB_AWS_SECRET_KEY
      - WILDERLAB_XAPI_KEY

    If not found, it falls back to placeholder strings (which should be replaced
    before use). It's strongly recommended to set environment variables instead
    of editing the source.

    Returns:
        (access_key, secret_key, xapi_key)
    """
    access_key = 'access_key_here'
    secret_key = 'secret_key_here'
    xapi_key   = 'xapi_key_here'
    
    # #below are the test API keys from https://wilderlab.co/api-instructions
    # access_key  =  "AKIATVYXGCYLWADFJVEX"
    # secret_key  =  "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"
    # xapi_key    =  "7CCm580l5vgeKbalwIEy565uFhbEudTauAq80B38"
    return access_key,secret_key,xapi_key



###############################################################################
###############################################################################
###############################################################################
def api_call(URL: str, access_key: str, secret_key: str, xapi_key: str,
                ) -> tuple[pd.DataFrame, int]:
    """
    Perform an authenticated GET to the Wilderlab API and return a DataFrame.

    The Wilderlab API returns a JSON with a 'message' field containing CSV text.
    This function signs the request using AWSRequestsAuth by passing `auth=` to
    requests.get(), and supplies the X-API-Key header.

    Args:
        URL: Full API URL to call.
        access_key: AWS access key ID.
        secret_key: AWS secret access key.
        xapi_key: Wilderlab provided API key (X-API-Key).
        timeout: Requests timeout in seconds (default 30).

    Returns:
        (DataFrame or None, HTTP status code)

    Raises:
        ValueError on problems building auth, sending request, or parsing CSV.
    """

    #generate authentication
    try: auth = AWSRequestsAuth(aws_access_key = access_key,
                            aws_secret_access_key = secret_key,
                            aws_host="connect.wilderlab.co.nz",
                            aws_region='ap-southeast-2',
                            aws_service='execute-api')
    except Exception as e: 
        raise ValueError(f'ERROR: Issue found trying to get AWS signature : {e}')

    #form request
    req = requests.Request('GET', URL)
    req.body = b''
    req.method = ''
    req.prepare()

    #form headers to send with request
    try: 
        headers = {"x-amz-date" : auth.get_aws_request_headers_handler(req)['x-amz-date'],
                "Authorization" : auth.get_aws_request_headers_handler(req)['Authorization'],
                "X-API-Key" : xapi_key}
    except Exception as e: 
        raise ValueError(f'ERROR: Issue forming header: {e}')

    response = requests.get(URL,auth=auth, headers=headers)
    try: response = requests.get(URL,auth=auth, headers=headers)
    except Exception as e: 
        raise ValueError(f'ERROR: Issue found sending request: {e}')

    #check response code
    response_code = response.status_code

    if response_code < 400:
        #get data in dataframe
        try:
            Data = pd.read_csv(StringIO(response.json()['message']),encoding = 'utf-8')
            Data.fillna('', inplace=True)
        except Exception as e: 
            raise ValueError(f'ERROR: Issue storing data in dataframe: {e}')
    else:
        print(response)
        Data = None

    return Data, response_code



###############################################################################
###############################################################################
###############################################################################
###############################################################################


def get_api_data(query_table: str = "jobs") -> tuple[pd.DataFrame, int]:
    """
        Convenience function to fetch one top-level table (jobs, samples, taxa etc).

        Args:
            query_table: The table name to request from the API (e.g., 'jobs', 'samples').

        Returns:
            (DataFrame or None, HTTP status code)
    """

    #Get API credentials
    try:   
        access_key,secret_key,xapi_key = api_credentials()
    except Exception as e: 
        raise ValueError(f'ERROR: Issue found trying to get api credentials: {e}')
    #form URL
    URL = f'https://connect.wilderlab.co.nz/edna/?query={query_table}'
    Data, response_code = api_call(URL, access_key,secret_key,xapi_key)

    return Data,response_code

###############################################################################
###############################################################################
###############################################################################
###############################################################################
def get_api_data_records(job_numbers: list[str], query_table: str = "records"
                             ) -> tuple[pd.DataFrame, int, list[str]]:
    """
        Fetch 'records' CSV for each job id and concatenate into one DataFrame.

        Args:
            job_numbers: Iterable of job IDs (converted to str).
            query_table: usually 'records' (kept parameter for flexibility).

        Returns:
            - concatenated DataFrame (may be empty if no data)
            - largest HTTP response code observed across calls
            - list of "job: {id}, response code: {code}||" strings for quick logging
        """

    #Get API credentials
    try:   access_key,secret_key,xapi_key = api_credentials()
    except Exception as e: 
        raise ValueError(f'ERROR: Issue found trying to get api credentials: {e}')


    #create empty pandas dataframe
    record_data = pd.DataFrame()
    # print(Data)
    all_response_codes = []
    largest_response_code = 0
    for job_i in job_numbers:
        #form URL

        URL = f'https://connect.wilderlab.co.nz/edna/?query={query_table}&JobID={job_i}'

        job_Data, response_code = api_call(URL, access_key,secret_key,xapi_key)
        largest_response_code = max(largest_response_code,response_code)
        #concat latest data
        all_response_codes.append(f"job: {job_i}, response code: {response_code}||")

        print(f"Working on job: {job_i}, server response code: {response_code}")

        record_data = job_Data if record_data.empty else pd.concat([record_data,job_Data])


    #ensure no duplicate rows
    record_data.drop_duplicates(inplace = True)
    #reset index
    record_data.reset_index(drop = True, inplace = True)

    return record_data,largest_response_code,all_response_codes

###############################################################################
###############################################################################
###############################################################################
###############################################################################
def get_all_records():
    """
    High-level function to fetch requested tables and write them into an Excel file.
    Splits the 'records' sheet across multiple sheets if it exceeds Excel row limits.

    Returns:
        None. Writes an Excel file or prints 'No outputs requested'.
    """
    EXCEL_MAX_ROWS = 1_048_576
    
    #get jobs information
    if include_jobs:
        jobs_data,jobs_response_code = get_api_data(query_table = 'jobs')
    
    #get samples information
    if include_samples: 
        samples_data,samples_response_code = get_api_data(query_table = 'samples')
    
    #get taxa information
    if include_taxa:
        taxa_data,taxa_response_code = get_api_data(query_table = 'taxa')
    
    #get all records for ALL jobs 
    #CAUTION, this can take a while...
    if include_records:
        if not include_jobs:
            jobs_data,jobs_response_code = get_api_data(query_table = 'jobs')
        all_job_numbers = list(jobs_data['JobID'].unique())
        records_data,records_largest_response_code,records_all_response_codes = get_api_data_records(job_numbers = all_job_numbers,query_table = 'records')
    
    if include_taxa+include_samples+include_taxa+include_records>=1:
        with pd.ExcelWriter(save_location, engine="xlsxwriter") as writer:
            # --- Write other (small) dataframes ---
            if include_jobs:
                jobs_data.to_excel(writer,    sheet_name="Jobs",    index=False)
            if include_samples:     
                samples_data.to_excel(writer, sheet_name="Samples", index=False)
            if include_taxa:    
                taxa_data.to_excel(writer,    sheet_name="Taxa",    index=False)
        
            # --- Write large dataframe, splitting if needed ---
            if include_records:
                n_rows = len(records_data)
                if n_rows <= EXCEL_MAX_ROWS:
                    records_data.to_excel(writer, sheet_name="records", index=False)
                else:
                    # Split into chunks
                    for i, start in enumerate(range(0, n_rows, EXCEL_MAX_ROWS)):
                        end = min(start + EXCEL_MAX_ROWS, n_rows)
                        chunk = records_data.iloc[start:end]
                        sheet_name = f"records_part{i+1}"
                        chunk.to_excel(writer, sheet_name=sheet_name, index=False)
    else: print('No outputs requested')                    
    

if __name__ == '__main__':
    get_all_records()

