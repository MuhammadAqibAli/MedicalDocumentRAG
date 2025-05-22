import os
import subprocess
import sys

def run_development_server():
    """
    Sets the APP_ENV environment variable to 'development'
    and runs the Django development server.
    """
    print("Setting APP_ENV=development for this process...")
    
    # Create a copy of the current environment variables
    env = os.environ.copy()
    # Set/update the APP_ENV variable
    env['APP_ENV'] = 'development'

    # Construct the command
    # sys.executable ensures we use the same Python interpreter that's running this script
    command = [sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000']
    
    # If your manage.py is not in the current directory where you run this script,
    # you might need to adjust the path to manage.py, e.g.:
    # manage_py_path = os.path.join(os.path.dirname(__file__), 'manage.py')
    # command = [sys.executable, manage_py_path, 'runserver', '0.0.0.0:8000']

    print(f"Starting Django development server with command: {' '.join(command)}")
    
    try:
        # Run the command with the modified environment.
        # subprocess.Popen is used here to allow the server to run interactively
        # and handle Ctrl+C correctly.
        process = subprocess.Popen(command, env=env)
        process.wait()  # Wait for the server process to terminate (e.g., by Ctrl+C)
    except FileNotFoundError:
        print(f"Error: Could not find '{sys.executable}' or 'manage.py'.")
        print("Make sure Python is in your PATH and manage.py is in the correct location.")
    except KeyboardInterrupt:
        print("\nDevelopment server shutdown requested by user (Ctrl+C).")
    finally:
        # Ensure the process is terminated if it's still running and the script exits
        if 'process' in locals() and process.poll() is None:
            print("Terminating server process...")
            process.terminate()
            process.wait()

if __name__ == "__main__":
    run_development_server()