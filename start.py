import subprocess
import sys
import time
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    # Start the background worker
    worker = subprocess.Popen([sys.executable, "main.py"], cwd=PROJECT_DIR)

    # Give it a moment
    time.sleep(1)

    # Start Streamlit dashboard
    ui = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py"], cwd=PROJECT_DIR)

    # Wait until one exits, then stop the other
    try:
        ui.wait()
    finally:
        worker.terminate()

if __name__ == "__main__":
    main()
