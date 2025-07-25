import argparse
import os
import platformdirs
import pkg_resources
import sys

from fastmcp import FastMCP

from tranay.tools import tranayTools

# Basic Setup
USER_DATA_DIR = platformdirs.user_data_dir('tranay', 'tranay')
SOURCES_FILE = os.path.join(USER_DATA_DIR, 'sources.txt')

# Parse command line args
parser = argparse.ArgumentParser(
    description="tranay MCP: A read-only BI tool for analyzing various data sources"
)
parser.add_argument('sources', nargs=argparse.REMAINDER, default=[], 
    help='Data source (can be specified multiple times). Can be a MongoDB, SQLite, MySQL, PostgreSQL connection string, or a path to CSV, Parquet, or DuckDB file.'
)
args = parser.parse_args()

source_list = []
if os.path.exists(SOURCES_FILE):
    with open(SOURCES_FILE) as f:
        source_list = [line.strip('\n') for line in f.readlines() if line.strip('\n')]

if not source_list:
    source_list = args.sources

if not source_list:
    source_list = [
        pkg_resources.resource_filename(
            'tranay',
            os.path.join('mcp', 'example_data', 'all_pokemon_data.csv')
        )
    ]
    print("No data sources provided. Loading example dataset for demonstration.")
    print(f"\nTo load your datasets, add them to {SOURCES_FILE} (one source URL or full file path per line)")
    print("\nOr use command line args to specify data sources:")
    print("tranay_mcp mongodb://localhost/mydb sqlite:///path/to/mydata.db /path/to/my_file.csv")
    print(f"\nNOTE: Sources in command line args will be ignored if sources are found in {SOURCES_FILE}")

    
SOURCES = {}
for s in source_list:
    source = s.lower()
    if source.startswith('sqlite://'):
        source_type = 'sqlite'
        source_name = source.split('/')[-1].split('?')[0].split('.db')[0]
    elif source.startswith('postgresql://'):
        source_type = 'postgresql'
        source_name = source.split('/')[-1].split('?')[0]
    elif source.startswith("mysql://") or source.startswith("mysql+pymysql://"):
        source_type = 'mysql'
        s = s.replace('mysql://', 'mysql+pymysql://')
        source_name = source.split('/')[-1].split('?')[0]
    elif source.startswith('mongodb://') or source.startswith('mongodb+srv://'):
        source_type = 'mongodb'
        source_name = source.split('/')[-1].split('?')[0]
        if not source_name: 
            source_name = 'mongodb_db'
    elif source.startswith('tranay-api://'):
        source_type = 'tranay_api'
        source_name = source.split('://')[1]


    elif source.startswith('clickhouse://'):
        source_type = 'clickhouse'
        source_name = source.split('/')[-1].split('?')[0]
    elif source.endswith(".duckdb"):
        source_type = "duckdb"
        source_name = source.split('/')[-1].split('.')[0]
    elif source.endswith(".csv"):
        source_type = "csv"
        source_name = source.split('/')[-1].split('.')[0]
    elif source.endswith(".parquet") or source.endswith(".pq"):
        source_type = "parquet"
        source_name = source.split('/')[-1].split('.')[0]
    else:
        continue

    source_id = f'{source_name}-{source_type}'
    if source_id in SOURCES:
        i = 2
        while True:
            source_id = f'{source_name}{i}-{source_type}'
            if source_id not in SOURCES:
                break
            i += 1

    SOURCES[source_id] = {'url': s, 'source_type': source_type}


def tranayMCP(sources):
    tranay_tools = tranayTools(sources)
    tranay_mcp = FastMCP()
    for tool in tranay_tools.tools:
        tranay_mcp.add_tool(tool)

    return tranay_mcp


def main():
    # print("Final SOURCES dictionary passed to tranayMCP:")
    # print(SOURCES)
    tranayMCP(SOURCES).run()

if __name__ == '__main__':
    main()