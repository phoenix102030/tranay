from tranay.studio.app import app
from . import tasks 

def main():
    app.run(port=6066, debug=True)
