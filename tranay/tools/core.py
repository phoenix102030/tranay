# tranay/tools/core.py

import json
from typing import Annotated, Union
import pandas as pd
from pydantic import Field
from tranay.tools import query_utils
from . import api_client

class Core:

    def __init__(self, data_sources): 
        self.data_sources = data_sources
        # The self.tools list now includes our new `list_api_projects` tool.
        self.tools = [
            self.list_sources,
            self.describe_table,
            self.run_query,
            self.list_projects, # <-- Use the new, simpler name
        ]

    def list_sources(self) -> str:
        """
        List all available data sources and the tables/collections within them.
        Returns a list of unique source IDs to be used for other queries.
        """
        try:
            if not self.data_sources:
                return "No data sources available. Add data sources."
            
            result = "Available data sources:\n\n"
            for source_id, source_info in self.data_sources.items():
                tables = query_utils.list_tables(source_info)
                if isinstance(tables, list):
                    tables_str = ', '.join(tables) if tables else "No tables found"
                else:
                    tables_str = str(tables)
                result += f"- {source_id}\n  Has tables: {tables_str}\n"
                
            return result
        except Exception as e:
            return f"Error listing data sources: {e}"

    def describe_table(self, 
        source: Annotated[str, Field(description='The unique data source ID.')], 
        table: Annotated[str, Field(description='The table or collection name in the data source.')] # <-- RENAME this parameter
    ) -> str:
        """
        Lists columns and their types for a table or shows a sample document for a collection.
        """
        try:
            source_info = self.data_sources.get(source)
            if not source_info:
                return f"Source '{source}' Not Found"
            
            # --- IMPORTANT: Use the new parameter name here as well ---
            result = query_utils.describe_table(source_info, table)

            if isinstance(result, pd.DataFrame):
                 return result.to_markdown(index=False)
                
            return str(result)
        except Exception as e:
            return f"Error describing table: {e}"

    def list_api_projects(self,
        source: Annotated[str, Field(description="The unique ID of the tranay_api data source.")]
    ) -> str:
        """
        Lists all available projects from the specified tranay_api data source.
        Returns a table of project names and their corresponding IDs.
        """
        try:
            source_info = self.data_sources.get(source)
            if not source_info or source_info.get('source_type') != 'tranay_api':
                return f"Error: Source '{source}' is not a valid tranay_api source."

            projects = api_client.get_all_projects(source_info['url'])
            if not projects:
                return "No projects found for this API source."
            
            df = pd.DataFrame(projects)
            return df.to_markdown(index=False)
        except Exception as e:
            return f"Error listing API projects: {e}"

    def run_query(self,
        source: Annotated[
            str, Field(description="The unique data source ID from 'list_sources'.")
        ],  
        query: Annotated[
            str | None, Field(description="For SQL sources, the SQL query to run.")
        ] = None,
        collection: Annotated[
            str | None, Field(description="For MongoDB sources, the name of the collection to query.")
        ] = None,
        filter: Annotated[
            Union[str, dict, None], Field(description="For MongoDB, a JSON filter string or a dictionary.")
        ] = None,
        pipeline: Annotated[
            list | None, Field(description="For MongoDB aggregations, a list of pipeline stages.")
        ] = None,
        projection: Annotated[
            dict | None, Field(description="For MongoDB finds, a projection document.")
        ] = None,
        project_id: Annotated[
            str | None, Field(description="For tranay_api sources, the ID of the project to fetch.")
        ] = None,
        # --- ADD THIS NEW ARGUMENT ---
        dataframe_query: Annotated[
            str | None, Field(description="A query string to filter data after it's fetched. E.g., 'sensor_id == 2007'.")
        ] = None
    ) -> str:
        """
        Run a query against a specified data source.
        - For SQL, use 'query'.
        - For MongoDB, use 'collection' with 'filter', 'pipeline', or 'projection'.
        - For the tranay_api source, use 'project_id' and optionally 'dataframe_query'.
        """
        try:
            source_info = self.data_sources.get(source)
            if not source_info:
                return f"Source '{source}' Not Found"
            
            source_type = source_info['source_type']
            final_query_str = query_utils.build_query_str(
                source_info, query=query, collection=collection, 
                filter_obj=filter, pipeline=pipeline, projection=projection, project_id=project_id
            )

            if not final_query_str:
                return "Error: Could not build a valid query. Please provide correct parameters for the source type."

            result_df = query_utils.execute_query(source_info, final_query_str)
            
            if not isinstance(result_df, pd.DataFrame):
                return str(result_df) # Return error string directly

            # --- ADD THIS BLOCK TO APPLY IN-MEMORY FILTERING ---
            if dataframe_query:
                try:
                    result_df = result_df.query(dataframe_query)
                    if result_df.empty:
                        return f"The dataframe_query '{dataframe_query}' resulted in no data."
                except Exception as e:
                    return f"Error applying dataframe_query: {e}"

            if result_df.empty:
                return "The query returned no results."
            
            return result_df.to_markdown(index=False)

        except Exception as e:
            return f"Error running query: {e}"
        
    def list_projects(self,
        source: Annotated[str, Field(description="The unique ID of the tranay_api data source.")]
    ) -> str:
        """
        Lists all available projects from the specified tranay_api data source.
        Returns a table of project names and their corresponding IDs.
        """
        try:
            source_info = self.data_sources.get(source)
            if not source_info or source_info.get('source_type') != 'tranay_api':
                return f"Error: Source '{source}' is not a valid tranay_api source."

            # The function now calls the api_client.get_all_projects
            projects = api_client.get_all_projects(source_info['url'])
            if not projects:
                return "No projects found for this API source."
            
            df = pd.DataFrame(projects)
            return df.to_markdown(index=False)
        except Exception as e:
            return f"Error listing API projects: {e}"
