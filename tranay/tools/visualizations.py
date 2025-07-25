# tranay/tools/visualizations.py

from base64 import b64encode
from typing import Any, List, Union, Annotated
import json
import pandas as pd

from mcp.types import ImageContent
import plotly.express as px
from pydantic import Field

from tranay.tools import query_utils


def _fig_to_image(fig):
    """Converts a Plotly figure to a base64 encoded image content object."""
    fig_encoded = b64encode(fig.to_image(format='png')).decode()
    return ImageContent(
        type='image',
        data=fig_encoded,
        mimeType='image/png',
        annotations=None,
    )


class Visualizations:

    def __init__(self, data_sources):
        self.data_sources = data_sources
        self.tools = [
            self.scatter_plot,
            self.line_plot,
            self.histogram,
            self.strip_plot,
            self.box_plot,
            self.bar_plot,
        ]

    def _get_df_from_source(self, source, query):
        """
        Executes the query against the specified source and returns a DataFrame.
        """
        source_info = self.data_sources.get(source)
        if not source_info:
            raise Exception(f"Source {source} Not Found")

        df = query_utils.execute_query(source_info, query)

        # Flatten nested object columns for easier plotting
        if isinstance(df, pd.DataFrame):
            df_final = df.copy()
            cols_to_drop = []
            for col in df.columns:
                # Check if column contains dictionaries
                if df[col].dtype == 'object' and df[col].dropna().apply(lambda x: isinstance(x, dict)).any():
                    normalized_df = pd.json_normalize(df[col], sep='.')
                    # Prefix the new columns with the original column name
                    normalized_df.columns = [f"{col}.{sub_col}" for sub_col in normalized_df.columns]
                    df_final = df_final.join(normalized_df)
                    cols_to_drop.append(col)
            
            if cols_to_drop:
                df_final = df_final.drop(columns=cols_to_drop)
            return df_final
            
        return df

    # --- ✨ All plotting functions now have a consistent, final structure ✨ ---

    def scatter_plot(self,
        source: Annotated[str, Field(description="The unique data source ID.")],
        x: Annotated[str, Field(description="Column for x-axis. For nested data, use dot notation.")],
        y: Annotated[str, Field(description="Column for y-axis. For nested data, use dot notation.")],
        query: Annotated[str | None, Field(description="For SQL sources, the SQL query to run.")] = None,
        collection: Annotated[str | None, Field(description="For MongoDB, the collection name.")] = None,
        filter: Annotated[str | None, Field(description="For MongoDB, a JSON filter string.")] = None,
        project_id: Annotated[str | None, Field(description="For tranay_api sources, the project ID.")] = None,
        dataframe_query: Annotated[str | None, Field(description="A query string to filter data after it's fetched. E.g., 'sensor_id == 2007'.")] = None,
        color: Annotated[str | None, Field(description='Optional; column name for coloring points.')] = None,
        title: Annotated[str | None, Field(description='Optional; a title for the plot.')] = None
    ) -> str:
        """Generates a scatter plot from a data source."""
        try:
            source_info = self.data_sources.get(source)
            if not source_info: return f"Source '{source}' Not Found"
            
            final_query = query_utils.build_query_str(source_info, query=query, collection=collection, filter_obj=filter, project_id=project_id)
            if not final_query: return "Query building failed. Please provide valid parameters for the source type."
            
            df = self._get_df_from_source(source, final_query)

            if dataframe_query:
                try:
                    df = df.query(dataframe_query)
                    if df.empty: return f"The dataframe_query '{dataframe_query}' resulted in no data."
                except Exception as e: return f"Error applying dataframe_query: {e}"

            fig = px.scatter(df, x=x, y=y, color=color, title=title)
            fig.update_xaxes(autotickangles=[0, 45, 60, 90])
            return _fig_to_image(fig)
        except Exception as e:
            return f"Error generating scatter plot: {str(e)}"

    def line_plot(self,
        source: Annotated[str, Field(description="The unique data source ID.")],
        x: Annotated[str, Field(description="Column for x-axis. For nested data, use dot notation.")],
        y: Annotated[str, Field(description="Column for y-axis. For nested data, use dot notation.")],
        query: Annotated[str | None, Field(description="For SQL sources, the SQL query to run.")] = None,
        collection: Annotated[str | None, Field(description="For MongoDB, the collection name.")] = None,
        filter: Annotated[str | None, Field(description="For MongoDB, a JSON filter string.")] = None,
        project_id: Annotated[str | None, Field(description="For tranay_api sources, the project ID.")] = None,
        dataframe_query: Annotated[str | None, Field(description="A query string to filter data after it's fetched. E.g., 'sensor_id == 2007'.")] = None,
        color: Annotated[str | None, Field(description='Optional; column name for coloring lines.')] = None,
        title: Annotated[str | None, Field(description='Optional; a title for the plot.')] = None
    ) -> str:
        """Generates a line plot from a data source."""
        try:
            source_info = self.data_sources.get(source)
            if not source_info: return f"Source '{source}' Not Found"

            final_query = query_utils.build_query_str(source_info, query=query, collection=collection, filter_obj=filter, project_id=project_id)
            if not final_query: return "Query building failed. Please provide valid parameters for the source type."

            df = self._get_df_from_source(source, final_query)
            
            if dataframe_query:
                try:
                    df = df.query(dataframe_query)
                    if df.empty: return f"The dataframe_query '{dataframe_query}' resulted in no data."
                except Exception as e: return f"Error applying dataframe_query: {e}"

            fig = px.line(df, x=x, y=y, color=color, title=title)
            fig.update_xaxes(autotickangles=[0, 45, 60, 90])
            return _fig_to_image(fig)
        except Exception as e:
            return f"Error generating line plot: {str(e)}"

    def histogram(self,
        source: Annotated[str, Field(description="The unique data source ID.")],
        column: Annotated[str, Field(description="Column to plot. For nested data, use dot notation.")],
        query: Annotated[str | None, Field(description="For SQL sources, the SQL query to run.")] = None,
        collection: Annotated[str | None, Field(description="For MongoDB, the collection name.")] = None,
        filter: Annotated[str | None, Field(description="For MongoDB, a JSON filter string.")] = None,
        project_id: Annotated[str | None, Field(description="For tranay_api sources, the project ID.")] = None,
        dataframe_query: Annotated[str | None, Field(description="A query string to filter data after it's fetched. E.g., 'sensor_id == 2007'.")] = None,
        color: Annotated[str | None, Field(description='Optional; column name for coloring histograms.')] = None,
        nbins: Annotated[int | None, Field(description='Optional; number of bins')] = None,
        title: Annotated[str | None, Field(description='Optional; a title for the plot.')] = None
    ) -> str:
        """Generates a histogram from a data source."""
        try:
            source_info = self.data_sources.get(source)
            if not source_info: return f"Source '{source}' Not Found"

            final_query = query_utils.build_query_str(source_info, query=query, collection=collection, filter_obj=filter, project_id=project_id)
            if not final_query: return "Query building failed. Please provide valid parameters for the source type."

            df = self._get_df_from_source(source, final_query)

            if dataframe_query:
                try:
                    df = df.query(dataframe_query)
                    if df.empty: return f"The dataframe_query '{dataframe_query}' resulted in no data."
                except Exception as e: return f"Error applying dataframe_query: {e}"

            fig = px.histogram(df, x=column, color=color, nbins=nbins, title=title)
            fig.update_xaxes(autotickangles=[0, 45, 60, 90])
            return _fig_to_image(fig)
        except Exception as e:
            return f"Error generating histogram: {str(e)}"

    def strip_plot(self,
        source: Annotated[str, Field(description="The unique data source ID.")],
        x: Annotated[str, Field(description="Column for x-axis. For nested data, use dot notation.")],
        y: Annotated[str, Field(description="Column for y-axis. For nested data, use dot notation.")],
        query: Annotated[str | None, Field(description="For SQL sources, the SQL query to run.")] = None,
        collection: Annotated[str | None, Field(description="For MongoDB, the collection name.")] = None,
        filter: Annotated[str | None, Field(description="For MongoDB, a JSON filter string.")] = None,
        project_id: Annotated[str | None, Field(description="For tranay_api sources, the project ID.")] = None,
        dataframe_query: Annotated[str | None, Field(description="A query string to filter data after it's fetched. E.g., 'sensor_id == 2007'.")] = None,
        color: Annotated[str | None, Field(description='Optional; column name for coloring strips.')] = None,
        title: Annotated[str | None, Field(description='Optional; a title for the plot.')] = None
    ) -> str:
        """Generates a strip plot from a data source."""
        try:
            source_info = self.data_sources.get(source)
            if not source_info: return f"Source '{source}' Not Found"

            final_query = query_utils.build_query_str(source_info, query=query, collection=collection, filter_obj=filter, project_id=project_id)
            if not final_query: return "Query building failed. Please provide valid parameters for the source type."
            
            df = self._get_df_from_source(source, final_query)

            if dataframe_query:
                try:
                    df = df.query(dataframe_query)
                    if df.empty: return f"The dataframe_query '{dataframe_query}' resulted in no data."
                except Exception as e: return f"Error applying dataframe_query: {e}"

            fig = px.strip(df, x=x, y=y, color=color, title=title)
            fig.update_xaxes(autotickangles=[0, 45, 60, 90])
            return _fig_to_image(fig)
        except Exception as e:
            return f"Error generating strip plot: {str(e)}"

    def box_plot(self,
        source: Annotated[str, Field(description="The unique data source ID.")],
        x: Annotated[str, Field(description="Column for x-axis (grouping). For nested data, use dot notation.")],
        y: Annotated[str, Field(description="Column for y-axis (values). For nested data, use dot notation.")],
        query: Annotated[str | None, Field(description="For SQL sources, the SQL query to run.")] = None,
        collection: Annotated[str | None, Field(description="For MongoDB, the collection name.")] = None,
        filter: Annotated[str | None, Field(description="For MongoDB, a JSON filter string.")] = None,
        project_id: Annotated[str | None, Field(description="For tranay_api sources, the project ID.")] = None,
        dataframe_query: Annotated[str | None, Field(description="A query string to filter data after it's fetched. E.g., 'sensor_id == 2007'.")] = None,
        color: Annotated[str | None, Field(description='Optional; column name for coloring the boxes.')] = None,
        title: Annotated[str | None, Field(description='Optional; a title for the plot.')] = None
    ) -> str:
        """Generates a box plot from a data source."""
        try:
            source_info = self.data_sources.get(source)
            if not source_info: return f"Source '{source}' Not Found"

            final_query = query_utils.build_query_str(source_info, query=query, collection=collection, filter_obj=filter, project_id=project_id)
            if not final_query: return "Query building failed. Please provide valid parameters for the source type."

            df = self._get_df_from_source(source, final_query)

            if dataframe_query:
                try:
                    df = df.query(dataframe_query)
                    if df.empty: return f"The dataframe_query '{dataframe_query}' resulted in no data."
                except Exception as e: return f"Error applying dataframe_query: {e}"

            fig = px.box(df, x=x, y=y, color=color, title=title)
            fig.update_xaxes(autotickangles=[0, 45, 60, 90])
            return _fig_to_image(fig)
        except Exception as e:
            return f"Error generating box plot: {str(e)}"

    def bar_plot(self,
        source: Annotated[str, Field(description="The unique data source ID.")],
        x: Annotated[str, Field(description="Column for x-axis. For nested data, use dot notation.")],
        y: Annotated[str, Field(description="Column for y-axis. For nested data, use dot notation.")],
        query: Annotated[str | None, Field(description="For SQL sources, the SQL query to run.")] = None,
        collection: Annotated[str | None, Field(description="For MongoDB, the collection name.")] = None,
        filter: Annotated[str | None, Field(description="For MongoDB, a JSON filter string.")] = None,
        project_id: Annotated[str | None, Field(description="For tranay_api sources, the project ID.")] = None,
        dataframe_query: Annotated[str | None, Field(description="A query string to filter data after it's fetched. E.g., 'sensor_id == 2007'.")] = None,
        color: Annotated[str | None, Field(description='Optional; column name for coloring the bars.')] = None,
        orientation: Annotated[str, Field(description="Orientation of the bar plot, 'v' for vertical or 'h' for horizontal.")] = 'v',
        title: Annotated[str | None, Field(description='Optional; a title for the plot.')] = None
    ) -> str:
        """Generates a bar plot from a data source."""
        try:
            source_info = self.data_sources.get(source)
            if not source_info: return f"Source '{source}' Not Found"

            final_query = query_utils.build_query_str(source_info, query=query, collection=collection, filter_obj=filter, project_id=project_id)
            if not final_query: return "Query building failed. Please provide valid parameters for the source type."

            df = self._get_df_from_source(source, final_query)

            if dataframe_query:
                try:
                    df = df.query(dataframe_query)
                    if df.empty: return f"The dataframe_query '{dataframe_query}' resulted in no data."
                except Exception as e: return f"Error applying dataframe_query: {e}"

            fig = px.bar(df, x=x, y=y, color=color, orientation=orientation, title=title)
            fig.update_xaxes(autotickangles=[0, 45, 60, 90])
            return _fig_to_image(fig)
        except Exception as e:
            return f"Error generating bar plot: {str(e)}"