from fuzzywuzzy import fuzz
import pandas as pd

def fuzz_run_table_search(search_text, connection_name="", schema=""):
    '''This method takes in a target text and uses fuzzy matching to find the most similar row in a "connection_schema.csv" dataframe.'''
    df = pd.read_csv('/tmp/snippets/connection_schema.csv')
    if connection_name != "" and schema != "":
        df = df.where(df['schema'] == schema).where(df['connection_name'] == connection_name).drop_duplicates()
    elif connection_name != "" and schema == "":
        df = df.where(df['connection_name'] == connection_name).drop_duplicates()
    elif connection_name == "" and schema != "":
        df = df.where(df['schema'] == schema).drop_duplicates()
    
    df_copy = df.copy()
    df_copy['similarity_score'] = df_copy['table'].apply(lambda x: fuzz.token_set_ratio(x, search_text))
    #most_similar_row = df_copy.loc[df_copy['similarity_score'].idxmax()]
    n = 10
    top_n_matches = df_copy.sort_values(by='similarity_score', ascending=False).head(n)
    return top_n_matches[['connection_name', 'schema', 'table', 'similarity_score']]
