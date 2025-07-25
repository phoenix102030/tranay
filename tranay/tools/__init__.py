from tranay.tools import core, visualizations


class tranayTools:

    def __init__(self, data_sources):
        self.tools = [
            *core.Core(data_sources).tools,
            *visualizations.Visualizations(data_sources).tools,
        ]
        

    
