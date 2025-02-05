import numpy as np
import pandas as pd
import duckdb
from openai import OpenAI
from typing import Dict, Any, List
import os
from pathlib import Path

class PreprocessingRoutine:
    EMBEDDING_MODEL = "text-embedding-ada-002"
    
    @staticmethod
    def get_data_paths():
        """Get paths to data files"""
        base_path = Path(__file__).parent.parent.parent / 'data'
        return {
            'metadata': str(base_path / 'connection_schema.csv'),
            'actions': str(base_path / 'actions_with_embeddings.csv')
        }
    
    def __init__(self):
        self.client = OpenAI(max_retries=5)
        self.conn = self._setup_database()
        self.docs_df = self._load_docs()

    def _setup_database(self):
        conn = duckdb.connect(database=':memory:')
        data_paths = self.get_data_paths()
        conn.sql(
            f"create table metadata as select * from read_csv_auto('{data_paths['metadata']}')"
        )
        return conn

    def _load_docs(self):
        data_paths = self.get_data_paths()
        docs_df = pd.read_csv(data_paths['actions'])
        docs_df.dropna(inplace=True)
        docs_df['saved_embedding'] = docs_df['embedding'].apply(ast.literal_eval)
        return docs_df

    def get_embedding(self, text: str) -> List[float]:
        text = text.replace("\n", " ")
        return self.client.embeddings.create(
            input=[text],
            model=self.EMBEDDING_MODEL
        ).data[0].embedding

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def search_docs(self, user_query: str, top_n: int = 3) -> pd.DataFrame:
        embedding = self.get_embedding(user_query)
        self.docs_df["similarities"] = self.docs_df.saved_embedding.apply(
            lambda x: self.cosine_similarity(x, embedding)
        )
        return self.docs_df.sort_values("similarities", ascending=False).head(top_n)

    def get_next_task(self, user_query: str, top_n: int = 3) -> pd.DataFrame:
        return self.search_docs(user_query, top_n=top_n)

    # ... rest of the methods from preroutine.py ... 