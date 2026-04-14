#!/usr/bin/env python3
"""
WorldWideCoin API Server Startup Script
Easy launcher for the real-time blockchain data API
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    print("Checking dependencies...")
    
    try:
        import flask
        print(" Flask: OK")
    except ImportError:
        print(" Flask: Missing")
        return False
    
    try:
        import flask_cors
        print(" Flask-CORS: OK")
    except ImportError:
        print(" Flask-CORS: Missing")
        return False
    
    return True

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "api_requirements.txt"])
        print("Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("Failed to install dependencies")
        return False

def start_api_server():
    """Start the API server"""
    print("\n" + "="*60)
    print("WorldWideCoin API Server Starting...")
    print("="*60)
    
    # Check if we're in the right directory
    if not Path("api_server.py").exists():
        print("Error: api_server.py not found in current directory")
        print("Please run this script from the worldwidecoin root directory")
        return False
    
    # Check dependencies
    if not check_dependencies():
        print("\nDependencies are missing. Installing them now...")
        if not install_dependencies():
            return False
    
    print("\nStarting API server...")
    print("API will be available at: http://localhost:5000")
    print("API Documentation: http://localhost:5000")
    print("Network Stats: http://localhost:5000/api/stats")
    print("Mining Stats: http://localhost:5000/api/mining")
    print("Recent Blocks: http://localhost:5000/api/blocks")
    print("Recent Transactions: http://localhost:5000/api/transactions")
    print("\nPress Ctrl+C to stop the server")
    print("-"*60)
    
    try:
        # Start the API server
        subprocess.run([sys.executable, "api_server.py"], check=True)
    except KeyboardInterrupt:
        print("\nAPI server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Error starting API server: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print("WorldWideCoin API Server Launcher")
    print("This script starts the real-time blockchain data API server")
    print()
    
    # Change to the script's directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Start the API server
    if start_api_server():
        print("\nAPI server stopped successfully")
    else:
        print("\nFailed to start API server")
        sys.exit(1)

if __name__ == "__main__":
    main()
