## ⚙️ Setup and Installation
### Prerequisites
Python 3.12+

pip and venv (included with standard Python installations)

### Installation Steps
Clone the Repository

Bash

git clone https://gitlabe2.ext.net.nokia.com/sityang/mcp_llm.git
cd tranay
Create and Activate Virtual Environment

Bash
'
python3 -m venv .venv
source .venv/bin/activate
'
Install Dependencies
This project uses pyproject.toml to manage dependencies. Install the project in editable mode, which will also install all required packages.

Bash
'
pip install -e .
'
## 🔧 Configuration
Before you can analyze data, you need to configure your LLM and data sources.

Run the Application Once to generate the initial configuration files.

Bash
'
tranay_studio
'
Open the Web Interface by navigating to http://127.0.0.1:6066 in your browser.

Configure the LLM:

Navigate to the Settings page from the sidebar.

Enter your API Endpoint and API Key for the Large Language Model you are using.

Configure Data Sources:

Navigate to the Manage Sources page.

To add the Transport API Source:

In the "Link A Database Using URL" field, enter the API's location using the custom protocol format: tranay-api://http://<your_api_server_ip>:<port>

Example: tranay-api://http://192.168.60.229:31280

To add MongoDB:

Use a standard MongoDB connection string.

Example: mongodb://localhost:27017/traffic_data

You can also upload local files like CSVs.

## ▶️ Running the Demo
Activate the Virtual Environment in your terminal:

Bash
'
source .venv/bin/activate
'
Start the Flask Server:

Bash
'
tranay_studio
'
Open the Studio in your web browser at http://127.0.0.1:6066.

## 💡 Example Usage
Here is a sample conversation to test the tranay_api source:

Start a new chat and ask the agent to discover the data:

What data sources are available?

The agent will list api_data-tranay_api. Ask it to list the available projects within that source:

Using the api_data-tranay_api source, list the available projects.

The agent will return a table with the "Lyon M6" project. Now, ask for a specific analysis, referencing the project and a sensor:

Create a line plot of speed over time for the "Lyon M6" project. Only show data for sensor 1974.

The agent will now use the project_id and dataframe_query parameters to fetch the data and generate a visualization directly in the chat.