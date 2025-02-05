import requests
import pandas as pd
from typing import Dict
from .dq_tools import DQTools

class JobTools:
    @staticmethod
    def get_job_status() -> str:
        try:
            token = DQTools.get_api_token()
            headers = {'Authorization': f'Bearer {token}'}
            params = {
                'jobStatus': '',
                'limit': '5',
            }

            response = requests.get(
                os.environ.get("DQ_URL") + '/v2/getowlcheckq',
                params=params,
                headers=headers,
                verify=False
            )

            df = pd.DataFrame(
                response.json()['data'],
                columns=['dataset', 'status', 'activity']
            )
            
            return f"job status: ~~~{df.to_markdown(index=False, tablefmt='presto', floatfmt='.0%').replace('000','')}~~~"
        except Exception as e:
            return f"Error getting job status: {str(e)}" 