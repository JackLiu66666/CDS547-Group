# run_app.py: EXE entry file after packaging
import sys
import os
import subprocess

def main():
    # --------------------------
    # 1. Auto-detect path
    # --------------------------
    if getattr(sys, 'frozen', False):
        # If running as packaged EXE, get EXE directory
        base_path = os.path.dirname(sys.executable)
    else:
        # If running directly with Python, get current file directory
        base_path = os.path.dirname(os.path.abspath(__file__))

    # Ensure app.py exists
    app_path = os.path.join(base_path, "app.py")
    if not os.path.exists(app_path):
        print(f"Error: Cannot find app.py!")
        print(f"Please ensure app.py is in the same folder as the EXE.")
        print(f"Current path: {app_path}")
        input("Press Enter to exit...")
        return

    # --------------------------
    # 2. Start Streamlit service
    # --------------------------
    print("Starting LLM Information Aggregation Tool...")
    print(f"Program directory: {base_path}")
    print("Please wait, browser will open automatically (first launch may take 10-20 seconds)...")

    # Streamlit startup command
    cmd = [
        sys.executable, "-m", "streamlit", "run", app_path,
        "--server.headless", "false",
        "--server.port", "8501",
        "--server.enableCORS", "false"
    ]

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nProgram exited")
    except Exception as e:
        print(f"Startup failed: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()