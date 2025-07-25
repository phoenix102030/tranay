import asyncio
import json

from function_schema import get_function_schema
import httpx
from mcp.types import ImageContent


class Agent:

    def __init__(self, 
        endpoint: str,
        api_key: str,
        model: str,
        tools: list = [],
        image_input: bool = False,
    ):
    
        self._post_url = f'{endpoint}/chat/completions'
        self._api_key = api_key
        self._model = model
        self._image_input = image_input
        self._system_message = {
            'role': 'system',
                'content': """You are an expert data analysis assistant. Your goal is to help users understand their data by using the tools provided.

            ## Core Directives
            - **Tool-Based:** You'd better use only the provided tools to answer questions.
            - **Concise Replies:** The tool outputs are shown directly to the user, so your text replies should be brief summaries or next steps. Do not repeat the tool's output.
            - **CRITICAL RULE:** For any tool that acts on a data source, you **MUST ALWAYS** provide the `source` argument.

            Your primary tools are listed below. You **MUST** use these exact names when calling a tool.
            - **Data Discovery:** `list_data_sources`, `describe_table`, `list_projects` # <-- Use the new name
            - **Data Querying:** `run_query`
            - **Plotting:** `scatter_plot`, `line_plot`, `bar_plot`, `histogram`, `box_plot`, `strip_plot`

            ## Standard Workflow
            For any user request, follow this three-step process:
            1.  **Discover:** To see available data sources and the tables/collections inside them, use the `list_data_sources` tool.
            2.  **Explore:** Before querying, understand the data structure. Use `describe_table` or `list_projects`.
            3.  **Execute:** Once you know the source and structure, use `run_query` or a plotting function.

            ## Source-Specific Instructions

            ### ### MongoDB Sources
            - **Querying with `run_query`:** Use the `collection` parameter. You can also use `filter`, `pipeline`, or `projection`.
            - **Plotting (e.g., `bar_plot`):** You **MUST** provide the `collection` parameter. You can also use `filter`. **DO NOT** use `query` or `project_id` for MongoDB sources.
            - **Dot Notation:** Use dot notation for nested fields (e.g., `metadata.lane_id`).

                - **`lane_data`**:
                    ```json
                    {
                        "timestamp": "YYYY-MM-DDTNN:NN:NN",
                        "metadata": { "lane_id": "NN", "simulation_session_id": "sim*" },
                        "measurement": { "speed": NN.NN, "density": NN.NN, "occupancy": NN.NN, "waiting_time": NN.NN, "travel_time": NN.NN, "time_loss": NN.NN }
                    }
                    ```
                - **`measurements`**:
                    ```json
                    {
                        "timestamp": "YYYY-MM-DDTNN:NN:NN",
                        "metadata": { "source_id": "NN", "reference_id": "sim*" },
                        "measurement": { "speed": NN.NN, "count": NN, "flow": NN.NN, "occupancy": NN.NN }
                    }
                    ```

            ### ### Tranay API Source (`tranay_api`)
            When the user asks about the API source (api_data-tranay_api), you are a specialized transport data analyst. 
            Your goal is to help them explore transport simulation results. The data is organized into Projects, 
            which contain time-series measurements from various Sensors.

            ### Available Data Fields
            Once you fetch data for a project, the following columns will be available for querying and plotting:
            project_id: The unique identifier for the simulation project.
            sensor_id: The unique identifier for an individual sensor within the project.
            location: The geographical coordinates of the sensor.
            timestamp: The date and time of the measurement.
            speed: The average speed of vehicles at the sensor.
            flow: The number of vehicles passing the sensor per hour.
            occupancy: The percentage of time the sensor is detecting a vehicle.
            count: The raw number of vehicles detected during the measurement interval.

            This source requires a two-step process.
            1.  **Step 1: Identify the Project: You MUST first use the list_projects tool to see which simulation projects are available. 
            Show this list to the user so they can choose which project to analyze. 
            The project_id from this step is required for all data fetching.
            2.  **Step 2: Fetch Data:**
                - **Using `run_query`:** You **MUST** provide the `project_id`. To filter, use `dataframe_query`.
                - **Using a plotting tool (e.g., `bar_plot`):** You **MUST** provide the `project_id`. To filter for a specific sensor, use `dataframe_query`.
                - **Example Plot Call:** `bar_plot(source="api_data-tranay_api", project_id="...", dataframe_query="sensor_id == 2007", ...)`
                - **CRITICAL:** **NEVER** use the `table`, `collection`, or `filter` parameters for `tranay_api` sources.
            """
        }
        
        self._tools = []
        self._tool_map = {}
        for tool in tools:
            tool_schema = get_function_schema(tool)
            self._tools.append({
                'type': 'function', 
                'function': tool_schema,
            })
            self._tool_map[tool_schema['name']] = tool


    def _prepare_input_messages(self, messages):
        input_messages = [self._system_message]
        for message in messages:
            if message['role']!='tool':
                input_messages.append(message)
            elif type(message['content']) is not list:
                input_messages.append(message)
            else:
                new_content = []
                image_content = None
                for content in message['content']:
                    if content['type']=='image_url':
                        image_content = content
                        new_content.append({
                            'type': 'text',
                            'text': 'Tool call returned an image to the user.',
                        })
                    else:
                        new_content.append(content)
                input_messages.append({
                    'role': message['role'],
                    'tool_call_id': message['tool_call_id'],
                    'name': message['name'],
                    'content': new_content,
                })

        return input_messages                
        
    
    def run(self, messages):
        if type(messages) is str:
            messages = [{'role': 'user', 'content': messages}]

        while True:
            # Conditionally create the headers
            headers = {}
            if self._api_key:
                headers['Authorization'] = f'Bearer {self._api_key}'
            
            # Make the request using the new headers variable
            res = httpx.post(
                url = self._post_url,
                headers = headers,
                timeout = 240.0,
                json = {
                    'model': self._model,
                    'messages': self._prepare_input_messages(messages),
                    'tools': self._tools,
                    'reasoning': {'exclude': True},
                }
            )

            print(res.text)
            resj = res.json()
            reply = resj['choices'][0]['message']
            messages.append(reply)

            tool_calls = reply.get('tool_calls')
            if tool_calls:
                for tool_call in tool_calls:
                    tool_name = tool_call['function']['name']
                    tool_args = json.loads(tool_call['function']['arguments'])
                    tool_response = self._tool_map[tool_name](**tool_args)
                    if type(tool_response) is ImageContent:
                        b64_data = tool_response.data
                        data_url = f'data:image/png;base64,{b64_data}'
                        content = [{
                            'type': 'image_url',
                            'image_url': {
                                "url": data_url,
                            }                            
                        }]
                    else:
                        content = [{
                            'type': 'text',
                            'text': json.dumps(tool_response)
                        }]
                        
                    messages.append({
                        'role': 'tool',
                        'tool_call_id': tool_call['id'],
                        'name': tool_name,
                        'content': content
                    })
            else:
                break

        return messages

    
