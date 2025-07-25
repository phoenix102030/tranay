import clickhouse_connect
import duckdb
import numpy as np
import os
import pandas as pd
import sqlalchemy
from sqlalchemy.orm import Session
import time
from typing import List
from tranay.tools import config
import pymongo
import json

from tranay.tools import api_client


def list_tables(source):
    try:
        match source['source_type']:
            case "mongodb":
                client = pymongo.MongoClient(source['url'])
                db_name = pymongo.uri_parser.parse_uri(source['url'])['database']
                if not db_name:
                    return "Error: Database name missing in connection string."
                db = client[db_name]
                return db.list_collection_names()
            
            case "tranay_api":
                # The API provides one logical "table" of sensor data.
                return ['sensor_readings']
            
            case "sqlite":
                result = execute_query(source,
                    "SELECT name FROM sqlite_schema WHERE type ='table' AND name NOT LIKE 'sqlite_%';"
                )
                return result['name'].to_list()

            case "postgresql":
                result = execute_query(source,
                    "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';"
                )
                return result['tablename'].to_list()

            case "mysql":
                result = execute_query(source, "SHOW TABLES")
                for col in list(result):
                    if col.startswith("Tables_in_"):
                        return result[col].to_list()
                
            case "duckdb" | "csv" | "parquet" | "clickhouse":
                result = execute_query(source, "SHOW TABLES")
                return result['name'].to_list()

    except Exception as e:
        return str(e)


def describe_table(source, table_name):
    match source['source_type']:
        case 'tranay_api':
            print("Fetching a sample document from the API to describe the table...")
            base_url = source['url']
            all_projects = api_client.get_all_projects(base_url)
            if not all_projects:
                return "Could not fetch any projects from the API."
            
            sample_data = api_client.get_sensor_data_for_project(base_url, all_projects[0]['id'])
            if sample_data:
                sample_doc = sample_data[0]
                return f"Sample document from the API source '{table_name}':\n{json.dumps(sample_doc, indent=2)}"
            return "Could not retrieve a sample document from the API."
        
        case 'mongodb':
            client = pymongo.MongoClient(source['url'])
            db_name = pymongo.uri_parser.parse_uri(source['url'])['database']
            if not db_name:
                return "Error: Database name missing in connection string."
            db = client[db_name]
            collection = db[table_name]
            sample_doc = collection.find_one()
            if sample_doc:
                sample_doc['_id'] = str(sample_doc['_id']) # Convert ObjectId
                return f"Sample document from '{table_name}':\n{json.dumps(sample_doc, indent=2)}"
            return "Collection is empty or does not exist."
        
        case 'sqlite':
            return execute_query(source,
                f'PRAGMA table_info("{table_name}");'
            )
            
        case 'postgresql':
            return execute_query(source,
                f"SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '{table_name}';"
            )
            
        case "mysql" | "duckdb" | "csv" | "parquet" | "clickhouse":
            if ' ' in table_name:
                table_name = f'`{table_name}`'
                
            return execute_query(source,
                f'DESCRIBE {table_name};'
            )
            

def execute_query(source: dict, query: str):
    """Run the query using the appropriate engine and read only config"""
    url = source['url']
                
    match source['source_type']:
        case "tranay_api":
            try:
                query_doc = json.loads(query)
                project_id = query_doc.get("project_id")

                if not project_id:
                    raise ValueError("The query for a tranay_api source must be a JSON string containing a 'project_id' key.")

                api_data = api_client.get_sensor_data_for_project(source['url'], project_id)
                
                if api_data is not None:
                    return pd.DataFrame(api_data)
                else:
                    return pd.DataFrame()
            except json.JSONDecodeError:
                return "Error: The provided query for the tranay_api source is not a valid JSON string."
            except Exception as e:
                return f"Error processing API query: {e}"
        
        case "mongodb":
            client = pymongo.MongoClient(source['url'])
            db_name = pymongo.uri_parser.parse_uri(source['url'])['database']
            if not db_name:
                raise Exception("Database name missing from MongoDB connection string.")
            db = client[db_name]

            query_doc = json.loads(query)
            collection_name = query_doc.get('collection')
            if not collection_name:
                raise Exception("Query for MongoDB must include a 'collection' key.")
            
            collection = db[collection_name]
            
            # Check if it's an aggregation or a simple find
            pipeline = query_doc.get('pipeline')
            if pipeline:
                # Execute an aggregation pipeline
                cursor = collection.aggregate(pipeline)
            else:
                # Execute a simple find query
                find_filter = query_doc.get('filter', {})
                projection = query_doc.get('projection', None)
                cursor = collection.find(find_filter, projection)
            
            return pd.DataFrame(list(cursor))
        
        case "sqlite":
            with sqlalchemy.create_engine(url).connect() as conn:
                conn.execute(sqlalchemy.text('PRAGMA query_only = ON;'))
                result = conn.execute(sqlalchemy.text(query))
                return pd.DataFrame(result)

        case "mysql":
            engine = sqlalchemy.create_engine(url)
            with Session(engine) as session:
                session.autoflush = False
                session.autocommit = False
                session.flush = lambda *args: None
                session.execute(sqlalchemy.text('SET SESSION TRANSACTION READ ONLY;'))
                result = session.execute(sqlalchemy.text(query))
                return pd.DataFrame(result)

        case "postgresql":
            engine = sqlalchemy.create_engine(url)
            with engine.connect() as conn:
                conn = conn.execution_options(
                    isolation_level="SERIALIZABLE",
                    postgresql_readonly=True,
                    postgresql_deferrable=True,
                )
                with conn.begin():
                    result = conn.execute(sqlalchemy.text(query))
                    return pd.DataFrame(result)

        case "clickhouse":
            client = clickhouse_connect.get_client(dsn=url)
            client.query('SET readonly=1;')
            return client.query_df(query, use_extended_dtypes=False)

        case "duckdb":
            conn = duckdb.connect(url, read_only=True)
            return conn.execute(query).df()

        case "csv":
            conn = duckdb.connect(database=':memory:')
            conn.execute(f"CREATE VIEW CSV AS SELECT * FROM read_csv('{url}')")
            return conn.execute(query).df()

        case "parquet":
            conn = duckdb.connect(database=':memory:')
            conn.execute(f"CREATE VIEW PARQUET AS SELECT * FROM read_parquet('{url}')")
            return conn.execute(query).df()
        
        case _:
            raise Exception("Unsupported Source")


def save_query(df: pd.DataFrame):
    """Save query results to disk and return a unique reference id"""
    query_id = 'q' + str(int(time.time()))
    filepath = os.path.join(config.QUERIES_DIR, f'{query_id}.parquet')
    df.replace({np.nan: None}).to_parquet(filepath, engine='pyarrow', index=False)
    return query_id


def load_query(query_id: str):
    """Load query results from disk using unique reference id"""
    filepath = os.path.join(config.QUERIES_DIR, f'{query_id}.parquet')
    df = pd.read_parquet(filepath, engine='pyarrow').replace({np.nan: None})
    df.reset_index(drop=True, inplace=True)
    return df

def build_query_str(source_info, query=None, collection=None, filter_obj=None, pipeline=None, projection=None, project_id=None):
    """Builds the final query string based on source type and provided parameters."""
    source_type = source_info.get('source_type')
    
    if source_type == 'tranay_api':
        if not project_id: return None
        return json.dumps({"project_id": project_id})
    
    elif source_type == 'mongodb':
        if not collection: return None
        mongo_query = {"collection": collection}
        if pipeline:
            mongo_query["pipeline"] = pipeline
        else:
            if filter_obj:
                if isinstance(filter_obj, str):
                    try:
                        mongo_query["filter"] = json.loads(filter_obj)
                    except json.JSONDecodeError:
                        return None # Invalid JSON string for filter
                else: # Assumes it's a dict
                    mongo_query["filter"] = filter_obj
            if projection:
                mongo_query["projection"] = projection
        return json.dumps(mongo_query)
    
    elif query:
        return query
        
    return None