#!/usr/bin/env python3
"""
WorldWideCoin Web Dashboard Server
Serves the static web dashboard files and provides a simple web interface
for interacting with the WorldWideCoin blockchain.
"""

import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
import argparse
import webbrowser
import threading
import time

class WWCDashboardHandler(SimpleHTTPRequestHandler):
    """Custom handler for the WorldWideCoin dashboard"""

    def __init__(self, *args, **kwargs):
        # Remove directory from kwargs if present
        kwargs.pop('directory', None)
        super().__init__(*args, **kwargs)

    def end_headers(self):
        # Add CORS headers for API calls
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_GET(self):
        # Serve index.html for root path
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()

def main():
    parser = argparse.ArgumentParser(description='WorldWideCoin Web Dashboard Server')
    parser.add_argument('--port', type=int, default=8080, help='Port to serve dashboard on')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--open', action='store_true', help='Open browser automatically')
    parser.add_argument('--api-url', default='http://localhost:8001', help='WorldWideCoin API URL')

    args = parser.parse_args()

    # Change to web directory
    web_dir = os.path.join(os.path.dirname(__file__), 'web')
    if not os.path.exists(web_dir):
        print(f"❌ Error: Web directory not found at {web_dir}")
        print("Make sure you're running this from the worldwidecoin directory")
        sys.exit(1)

    os.chdir(web_dir)

    class ThreadingHTTPServer(socketserver.ThreadingTCPServer):
        allow_reuse_address = True

    server_port = args.port

    def start_server(port):
        with ThreadingHTTPServer((args.host, port), WWCDashboardHandler) as httpd:
            print("🌐 WorldWideCoin Web Dashboard")
            print(f"📊 Dashboard: http://{args.host}:{port}")
            print(f"🔗 API Endpoint: {args.api_url}")
            print("💡 Press Ctrl+C to stop the server")
            print("")

            if args.open:
                def open_browser():
                    time.sleep(1)
                    webbrowser.open(f"http://{args.host}:{port}")

                threading.Thread(target=open_browser, daemon=True).start()

            httpd.serve_forever()

    try:
        start_server(server_port)
    except KeyboardInterrupt:
        print("\n👋 Dashboard server stopped")
    except OSError as e:
        if e.errno in (48, 10048):  # Address already in use
            alternate_port = server_port + 1
            print(f"⚠️ Port {server_port} is already in use. Trying port {alternate_port}...")
            try:
                start_server(alternate_port)
            except OSError as e2:
                if e2.errno in (48, 10048):
                    print(f"❌ Ports {server_port} and {alternate_port} are both unavailable. Use --port to choose an open port.")
                else:
                    print(f"❌ Error starting server: {e2}")
                sys.exit(1)
        else:
            print(f"❌ Error starting server: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()