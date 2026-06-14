import subprocess
import sys

if __name__ == "__main__":
    print("==============================================")
    print("Launching JioSaavn Connect App in Streamlit...")
    print("==============================================")
    
    try:
        # Launch Streamlit server using the virtual environment's executable
        subprocess.run([r".venv\Scripts\streamlit", "run", "app.py"], check=True)
    except KeyboardInterrupt:
        print("\n[System] Music Application stopped by user.")
    except FileNotFoundError:
        print("\nError: Streamlit command-line tool not found.")
        print("Please ensure your Python dependencies are installed using:")
        print("    pip install -r requirements.txt")
        sys.exit(1)
