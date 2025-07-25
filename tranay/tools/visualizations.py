# tranay/tools/visualizations.py

from base64 import b64encode
from typing import Any, List, Union, Annotated
import json # Import json for potential MongoDB query parsing (though not strictly needed here)

from mcp.types import ImageContent
import plotly.express as px
from pydantic import Field

from tranay.tools import query_utils


def _fig_to_image(fig):
    fig_encoded = b64encode(fig.to_image(format='png')).decode()
    # img_b64 = "data:image/png;base64," + fig_encoded # This line was redundant

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

    def _get_df_from_source(self, source_id, query):
        """
        Executes the query against the specified source and returns a DataFrame.

        For MongoDB sources (source_type == 'mongodb'), the 'query' parameter
        must be a JSON string compatible with query_utils.execute_query for MongoDB.
        Example: '{"collection": "my_collection", "filter": {"field": "value"}}'

        For other sources, 'query' should be a standard SQL string.
        """
        source = self.data_sources.get(source_id)
        if not source:
            raise Exception(f"Source {source_id} Not Found")

        # The logic for handling different source types (including MongoDB)
        # is encapsulated within query_utils.execute_query.
        # We just pass the source and query (string) to it.
        # The query_utils.execute_query function already handles the
        # source['source_type'] check and processes the 'query' string accordingly.
        return query_utils.execute_query(source, query)


    # --- Updated Docstrings for all visualization methods ---

    def scatter_plot(self,
        source_id: Annotated[
            str, Field(description='The data source to run the query on')
        ],
        query: Annotated[
            str, Field(
                description=(
                    "Query to run on the data source. "
                    "For SQL sources (sqlite, mysql, postgresql, duckdb, csv, parquet, clickhouse), use SQL syntax. "
                    "For MongoDB, provide a JSON string with 'collection' and optional 'filter'/'projection'. "
                    "Example for MongoDB: '{\"collection\": \"users\", \"filter\": {\"age\": {\"$gt\": 30}}}'"
                )
            )
        ],
        x: Annotated[
            str, Field(description='Column name from query result to use for x-axis')
        ],
        y: Annotated[
            str, Field(description='Column name from query result to use for y-axis')
        ],
        color: Annotated[
            str | None, Field(description='Optional; column name from query result to use for coloring the points, with color representing another dimension')
        ] = None,
    ) -> str:
        """
        Run query against specified source and make a scatter plot using the result.
        The query format depends on the source type:
        - SQL sources: Standard SQL query string.
        - MongoDB: JSON string specifying 'collection' and optionally 'filter'/'projection'.
        This will return an image of the plot.
        """

        try:
            df = self._get_df_from_source(source_id, query)
            fig = px.scatter(df, x=x, y=y, color=color)
            fig.update_xaxes(autotickangles=[0, 45, 60, 90])

            return _fig_to_image(fig)
        except Exception as e:
            # Consider logging the exception for debugging
            # import logging
            # logging.exception(f"Error in scatter_plot for source {source_id}: {e}")
            return f"Error generating scatter plot: {str(e)}"


    def line_plot(self,
        source_id: Annotated[
            str, Field(description='The data source to run the query on')
        ],
        # Inside line_plot definition in visualizations.py
        query: Annotated[
            str, Field(
                description=(
                    "Query to run on the data source. "
                    "For SQL sources (sqlite, mysql, postgresql, duckdb, csv, parquet, clickhouse), use SQL syntax. "
                    "For MongoDB, provide a JSON string with 'collection' and optional 'filter'/'projection'. "
                    "Example for MongoDB: '{\"collection\": \"metrics\", \"filter\": {\"timestamp\": {\"$gte\": \"2023-01-01\"}}}'"
                )
            )
        ],
        x: Annotated[
            str, Field(description='Column name from query result to use for x-axis')
        ],
        y: Annotated[
            str, Field(description='Column name from query result to use for y-axis')
        ],
        color: Annotated[
            str | None, Field(description='Optional; column name from query result to use for drawing multiple colored lines representing another dimension')
        ] = None,
    ) -> str:
        """
        Run query against specified source and make a line plot using the result.
        The query format depends on the source type:
        - SQL sources: Standard SQL query string.
        - MongoDB: JSON string specifying 'collection' and optionally 'filter'/'projection'.
        This will return an image of the plot.
        """

        try:
            df = self._get_df_from_source(source_id, query)
            fig = px.line(df, x=x, y=y, color=color)
            fig.update_xaxes(autotickangles=[0, 45, 60, 90])

            return _fig_to_image(fig)
        except Exception as e:
            return f"Error generating line plot: {str(e)}"


    def histogram(self,
        source_id: Annotated[
            str, Field(description='The data source to run the query on')
        ],
        query: Annotated[
            str, Field(
                description=(
                    "Query to run on the data source. "
                    "For SQL sources, use SQL syntax. "
                    "For MongoDB, provide a JSON string with 'collection' and optional 'filter'/'projection'. "
                    "Example for MongoDB: '{\"collection\": \"scores\", \"filter\": {\"subject\": \"math\"}}'"
                )
            )
        ],
        column: Annotated[
            str, Field(description='Column name from query result to use for the histogram')
        ],
        color: Annotated[
            str | None, Field(description='Optional; column name from query result to use for drawing multiple colored histograms representing another dimension')
        ] = None,
        nbins: Annotated[
            int | None, Field(description='Optional; number of bins')
        ] = None,
    ) -> str:
        """
        Run query against specified source and make a histogram using the result.
        The query format depends on the source type:
        - SQL sources: Standard SQL query string.
        - MongoDB: JSON string specifying 'collection' and optionally 'filter'/'projection'.
        This will return an image of the plot.
        """

        try:
            df = self._get_df_from_source(source_id, query)
            fig = px.histogram(df, x=column, color=color, nbins=nbins)
            fig.update_xaxes(autotickangles=[0, 45, 60, 90])

            return _fig_to_image(fig)
        except Exception as e:
            return f"Error generating histogram: {str(e)}"


    def strip_plot(self,
        source_id: Annotated[
            str, Field(description='The data source to run the query on')
        ],
        query: Annotated[
            str, Field(
                description=(
                    "Query to run on the data source. "
                    "For SQL sources, use SQL syntax. "
                    "For MongoDB, provide a JSON string with 'collection' and optional 'filter'/'projection'. "
                    "Example for MongoDB: '{\"collection\": \"experiments\", \"filter\": {\"group\": \"A\"}}'"
                )
            )
        ],
        x: Annotated[
            str, Field(description='Column name from query result to use for x-axis')
        ],
        y: Annotated[
            str, Field(description='Column name from query result to use for y-axis')
        ],
        color: Annotated[
            str | None, Field(description='Optional column name from query result to show multiple colored strips representing another dimension')
        ] = None,
    ) -> str:
        """
        Run query against specified source and make a strip plot using the result.
        The query format depends on the source type:
        - SQL sources: Standard SQL query string.
        - MongoDB: JSON string specifying 'collection' and optionally 'filter'/'projection'.
        This will return an image of the plot.
        """

        try:
            df = self._get_df_from_source(source_id, query)
            fig = px.strip(df, x=x, y=y, color=color) # Note: px.strip might not exist, consider px.scatter with marginal_y?
            fig.update_xaxes(autotickangles=[0, 45, 60, 90])

            return _fig_to_image(fig)
        except Exception as e:
             # px.strip might not be standard in older plotly versions or might behave differently
             # Consider using px.scatter with marginal_y='rug' or similar if px.strip is problematic
            return f"Error generating strip plot (check px.strip availability): {str(e)}"


    def box_plot(self,
        source_id: Annotated[
            str, Field(description='The data source to run the query on')
        ],
        query: Annotated[
            str, Field(
                description=(
                    "Query to run on the data source. "
                    "For SQL sources, use SQL syntax. "
                    "For MongoDB, provide a JSON string with 'collection' and optional 'filter'/'projection'. "
                    "Example for MongoDB: '{\"collection\": \"salaries\", \"filter\": {\"department\": \"Sales\"}}'"
                )
            )
        ],
        x: Annotated[
            str, Field(description='Column name from query result to use for x-axis (grouping)')
        ],
        y: Annotated[
            str, Field(description='Column name from query result to use for y-axis (values)')
        ],
        color: Annotated[
            str | None, Field(description='Optional column name from query result to show multiple colored boxes representing another dimension')
        ] = None,
    ) -> str:
        """
        Run query against specified source and make a box plot using the result.
        The query format depends on the source type:
        - SQL sources: Standard SQL query string.
        - MongoDB: JSON string specifying 'collection' and optionally 'filter'/'projection'.
        This will return an image of the plot.
        """

        try:
            df = self._get_df_from_source(source_id, query)
            fig = px.box(df, x=x, y=y, color=color)
            fig.update_xaxes(autotickangles=[0, 45, 60, 90])

            return _fig_to_image(fig)
        except Exception as e:
            return f"Error generating box plot: {str(e)}"


    def bar_plot(self,
        source_id: Annotated[
            str, Field(description='The data source to run the query on')
        ],
        query: Annotated[
            str, Field(
                description=(
                    "Query to run on the data source. "
                    "For SQL sources, use SQL syntax. "
                    "For MongoDB, provide a JSON string with 'collection' and optional 'filter'/'projection'. "
                    "Example for MongoDB: '{\"collection\": \"inventory\", \"filter\": {\"category\": \"Electronics\"}}'"
                )
            )
        ],
        x: Annotated[
            str, Field(description='Column name from query result to use for x-axis')
        ],
        y: Annotated[
            str, Field(description='Column name from query result to use for y-axis')
        ],
        color: Annotated[
            str | None, Field(description='Optional column name from query result to use as a 3rd dimension by splitting each bar into colored sections')
        ] = None,
        orientation: Annotated[
            str, Field(description="Orientation of the bar plot, use 'v' for vertical (default) and 'h' for horizontal. Be mindful of choosing the correct X and Y columns as per orientation")
        ] = 'v',
    ) -> str:
        """
        Run query against specified source and make a bar plot using the result.
        The query format depends on the source type:
        - SQL sources: Standard SQL query string.
        - MongoDB: JSON string specifying 'collection' and optionally 'filter'/'projection'.
        This will return an image of the plot.
        """

        try:
            df = self._get_df_from_source(source_id, query)
            fig = px.bar(df, x=x, y=y, color=color, orientation=orientation)
            fig.update_xaxes(autotickangles=[0, 45, 60, 90])

            return _fig_to_image(fig)
        except Exception as e:
            return f"Error generating bar plot: {str(e)}"


if __name__ == "__main__":
    print(ImageContent)
