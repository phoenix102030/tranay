# tranay/studio/tasks.py

import subprocess
import tempfile
import os
from .app import celery_app

@celery_app.task
def run_sumo_simulation(config_file_path: str, output_prefix: str):
    """
    Runs a SUMO simulation as a background Celery task.

    Args:
        config_file_path: The absolute path to the .sumocfg file.
        output_prefix: A prefix for all output files (e.g., tripinfo, fcd-output).
    """
    try:
        sim_dir = os.path.dirname(config_file_path)
        output_dir = os.path.join(sim_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        tripinfo_path = os.path.join(output_dir, f"{output_prefix}_tripinfo.xml")

        # Construct the SUMO command
        # This is a safe way to build command-line arguments, preventing security issues.
        sumo_command = [
            "sumo",
            "-c", config_file_path,
            "--tripinfo-output", tripinfo_path,
            "--log", os.path.join(output_dir, f"{output_prefix}_sumo.log"),
            "--verbose"
        ]

        # Log the command we are about to run
        print(f"Executing SUMO command: {' '.join(sumo_command)}")

        # Run the simulation
        # capture_output=True saves stdout/stderr
        # text=True decodes them as text
        # check=True raises an exception if SUMO returns a non-zero exit code (i.e., an error)
        result = subprocess.run(
            sumo_command,
            capture_output=True,
            text=True,
            check=True
        )

        # If we reach here, the simulation was successful
        print(f"SUMO simulation successful for {config_file_path}")
        print(f"Results saved in: {output_dir}")

        # The task returns the path to the directory containing the results
        return {
            "status": "SUCCESS",
            "output_dir": output_dir,
            "stdout": result.stdout
        }

    except FileNotFoundError:
        # This error occurs if the 'sumo' command is not found in the system's PATH
        error_message = "Error: 'sumo' command not found. Make sure SUMO is installed and its bin directory is in your system's PATH."
        print(error_message)
        return {"status": "FAILURE", "error": error_message}

    except subprocess.CalledProcessError as e:
        # This error occurs if the simulation fails for any reason
        error_message = f"SUMO simulation failed with exit code {e.returncode}."
        print(error_message)
        # We include stderr from SUMO to help with debugging
        return {
            "status": "FAILURE",
            "error": error_message,
            "stderr": e.stderr,
            "stdout": e.stdout
        }

    except Exception as e:
        # Catch any other unexpected errors
        error_message = f"An unexpected error occurred: {str(e)}"
        print(error_message)
        return {"status": "FAILURE", "error": error_message}