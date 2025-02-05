import os
import json
import logging
import requests
import urllib3
import pandas as pd
import duckdb
from datetime import datetime
from typing import Annotated
from ..core.config.environment import Environment
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)  # Set the logging level as needed
logger = logging.getLogger(__name__)  # Create a logger for this module

def get_api_token() -> str:
    """Get API token for DQ service"""
    env_vars = Environment.get_required_vars()
    
    try:
        url = env_vars.get("DQ_URL") + '/v3/auth/signin'
        payload = {
            'username': env_vars.get("DQ_USERNAME"),
            'password': env_vars.get("DQ_CREDENTIAL"),
            'iss': env_vars.get("DQ_TENANT")
        }
        headers = {
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json'
        }
        
        # Log request details (excluding sensitive info)
        logger.info(f"Making auth request to: {url}")
        logger.info(f"With username: {payload['username']} and tenant: {payload['iss']}")
        logger.info(f"Headers: {headers}")
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,  # Use json parameter instead of data for proper JSON encoding
            verify=False,
            timeout=30  # Add timeout
        )
        
        logger.info(f"Auth response status code: {response.status_code}")
        
        if response.status_code == 401:
            error_msg = "Authentication failed: Invalid credentials or tenant"
            logger.error(error_msg)
            logger.error(f"Response content: {response.text}")
            raise ValueError(error_msg)
        elif response.status_code != 200:
            error_msg = f"Auth API returned status code {response.status_code}"
            logger.error(error_msg)
            logger.error(f"Response content: {response.text}")
            raise ValueError(error_msg)
            
        try:
            data = response.json()
            logger.info("Successfully parsed auth response")
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse auth response: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Raw response: {response.text}")
            raise ValueError(error_msg)
            
        if not data.get("token"):
            error_msg = "No token in auth response"
            logger.error(error_msg)
            logger.error(f"Response data: {data}")
            raise ValueError(error_msg)
            
        logger.info("Successfully obtained auth token")
        return data["token"]
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error during auth: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error during auth: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

def get_metadata_path():
    """Get the path to the metadata CSV file"""
    return str(Path(__file__).parent.parent.parent / 'data' / 'connection_schema.csv')

def run_dq_job(
    dataset: Annotated[str, "dataset name to use"],
    query: Annotated[str, "query to use"],
    connection_name: Annotated[str, "connection name to use"], 
    schema_name: Annotated[str, "schema name to use"]
) -> str:
    """Run a DQ job with the given parameters"""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    env_vars = Environment.get_required_vars()
    
    # Validate table exists
    try:
        conn = duckdb.connect(database=':memory:')
        metadata_path = get_metadata_path()
        conn.sql(f"create table metadata as select * from read_csv_auto('{metadata_path}')")
        # schema_name = query.split(' ')[3].split('.')[0].strip()

        # #if query.contains 3 periods database.schema.table 
        # # then schema_name is the middle one
        # if '.' in query and len(query.split('.')) == 3:
        #     schema_name = query.split('.')[1].strip()

        logger.info(f"query: {query}")
        logger.info(f"connection_name: {connection_name}")
        logger.info(f"schema_name: {schema_name}")
        logger.info(f"dataset: {dataset}")

        # remove schema name if it exists in dataset name
        dataset2table = dataset
        if schema_name in dataset:
            dataset2table = dataset.replace(schema_name, "")
        
        # if schema_name contains non-alphanumeric characters, replace them with an underscore
        if not schema_name.isalnum():
            schema_name = re.sub(r'[^a-zA-Z0-9]+', '', schema_name)

        sql_statement = f"""
            SELECT * FROM metadata 
            WHERE connection_name like '%{connection_name}%' 
            AND schema_name like '%{schema_name}%' 
            AND table_name like '%{dataset2table}%' 
            LIMIT 1
        """
        logger.info(f"look-up query: {query}")
        logger.info(f"sql statement: {sql_statement}")

        rs = conn.sql(sql_statement.replace("\\","").replace("```sql", "").replace("```", ""))
        if rs.to_df().shape[0] == 0:
            return f"Unable to look-up and validate table {dataset} in schema {schema_name} for connection {connection_name}."
            
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return f"Error validating table {dataset} in schema {schema_name} for connection {connection_name}."

    # Run DQ job
    try:
        token = get_api_token()
        headers = {'Authorization': f'Bearer {token}'}
        run_id = datetime.now().strftime("%Y-%m-%d")
        
        # Job paramters 
        job_dataset_name = f"AI_{dataset}"
        job_query = query.replace("\\", "").replace("```sql", "").replace("```", "")
        job_connection_name = connection_name
        job_schema_name = schema_name
        
        logger.info(f"job_dataset_name: {job_dataset_name}")
        logger.info(f"job_query: {job_query}")
        logger.info(f"job_connection_name: {job_connection_name}")
        logger.info(f"job_schema_name: {job_schema_name}")
        
        params = {
            'dataset': job_dataset_name,
            'runId': run_id,
            'pushdown': {
                'connectionName': job_connection_name,
                'sourceQuery': job_query
            },
            'agentId': {'id': 0}
        }
        
        response = requests.post(
            env_vars.get("DQ_URL") + '/v2/run-job-json',
            headers=headers,
            json=params,
            verify=False
        )
        
        if response.status_code == 200:
            return f"Job triggered successfully for {dataset} in schema {schema_name}. Response: {response.json()}"
        else:
            return f"Job failed with status code {response.status_code}"
            
    except Exception as e:
        logger.error(f"DQ job error: {str(e)}")
        return f"Error running DQ job: {str(e)}"

def get_job_status() -> str:
    """Check the status of DQ jobs"""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    env_vars = Environment.get_required_vars()

    try:
        token = get_api_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        params = {
            'jobStatus': 'ALL',  # Get all job statuses
            'limit': '5',
            'tenant': env_vars.get("DQ_TENANT")
        }

        url = f"{env_vars.get('DQ_URL')}/v2/getowlcheckq"
        logger.info(f"Making request to: {url}")
        logger.info(f"With params: {params}")

        response = requests.get(
            url,
            params=params,
            headers=headers,
            verify=False
        )

        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response content: {response.text}")

        if response.status_code != 200:
            error_msg = f"API returned status code {response.status_code}"
            logger.error(error_msg)
            return f"Error checking job status: {error_msg}"

        if not response.text:
            error_msg = "API returned empty response"
            logger.error(error_msg)
            return f"Error checking job status: {error_msg}"

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON response: {str(e)}\nResponse text: {response.text}"
            logger.error(error_msg)
            return f"Error checking job status: {error_msg}"

        if not data.get('data'):
            return "No jobs found in the last 5 runs"

        df = pd.DataFrame(data['data'], columns=['dataset', 'status', 'activity'])
        if df.empty:
            return "No jobs found in the last 5 runs"
            
        return f"job status: ~~~{df.to_markdown(index=False, tablefmt='presto', floatfmt='.0%').replace('000','')}~~~"
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error: {str(e)}"
        logger.error(error_msg)
        return f"Error checking job status: {error_msg}"
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return f"Error checking job status: {error_msg}"

def run_sql_statement(sql_statement: Annotated[str, "SQL statement to execute"]) -> str:
    """Run a SQL statement on the metadata table"""
    try:
        conn = duckdb.connect(database=':memory:')
        metadata_path = get_metadata_path()
        conn.sql(f"create table metadata as select * from read_csv_auto('{metadata_path}')")
        rs = conn.sql(sql_statement.replace("\\","").replace("```sql", "").replace("```", ""))
        return f"results: ~~~{sql_statement} \n {rs.to_df().drop_duplicates().head(15).to_markdown(index=False)}~~~"
    
    except Exception as e:
        logger.error(f"Error running SQL statement: {str(e)}")
        return f"Error executing SQL: {str(e)}" 