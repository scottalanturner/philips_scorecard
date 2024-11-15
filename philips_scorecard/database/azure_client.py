import pymssql
import pandas as pd
from contextlib import contextmanager
from typing import Optional

class AzureClientMSSQL:
    def __init__(self, server: str, database: str, username: str, password: str):
        self.server = server
        self.database = database
        self.username = username
        self.password = password

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = pymssql.connect(
                server=self.server,
                database=self.database,
                user=f"{self.username}@{self.server.split('.')[0]}",
                password=self.password
            )
            yield conn
        finally:
            if conn is not None:
                conn.close()

    def load_table_to_dataframe(self, table_name: str, schema: str = 'dbo', 
                              custom_query: Optional[str] = None) -> pd.DataFrame:
        """Load data from Azure SQL table into a pandas DataFrame"""
        try:
            with self.get_connection() as conn:
                if custom_query:
                    query = custom_query
                else:
                    query = f"SELECT * FROM [{schema}].[{table_name}]"
                
                return pd.read_sql(query, conn)
                
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            raise