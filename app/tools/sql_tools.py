import duckdb
import pandas as pd
from typing import Annotated
import os
from pathlib import Path

class SQLTools:
    @staticmethod
    def get_metadata_path():
        """Get the path to the metadata CSV file"""
        return str(Path(__file__).parent.parent.parent / 'data' / 'connection_schema.csv')

    @staticmethod
    def run_sql_statement(sql_statement: Annotated[str, "SQL statement to execute"]) -> str:
        try:
            conn = duckdb.connect(database=':memory:')
            metadata_path = SQLTools.get_metadata_path()
            conn.sql(f"create table metadata as select * from read_csv_auto('{metadata_path}')")
            rs = conn.sql(sql_statement.replace("\\","").replace("```sql", "").replace("```", ""))
            result_df = rs.to_df().drop_duplicates().head(15)
            return f"results: ~~~{sql_statement} \n {result_df.to_markdown(index=False)}~~~"
        except Exception as e:
            return f"Error executing SQL: {str(e)}" 