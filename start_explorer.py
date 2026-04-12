#!/usr/bin/env python3
"""
Start WorldWideCoin Block Explorer Web Dashboard
Run this script to open the web interface in your browser
"""

import sys
import time
import webbrowser
from threading import Timer
from core.blockchain import Blockchain
from explorer.block_explorer import create_block_explorer


def open_browser(url):
    """Open browser after a short delay"""
    webbrowser.open(url)


def main():
    """Start the WorldWideCoin Block Explorer"""
    print("WorldWideCoin Block Explorer")
    print("=" * 50)
    
    try:
        # Create blockchain
        print("Initializing blockchain...")
        blockchain = Blockchain()
        
        # Mine some blocks if needed
        if len(blockchain.chain) < 2:
            print("Mining initial blocks...")
            for i in range(2):
                block = blockchain.create_block(f"initial_miner_{i}")
                blockchain.add_block(block)
        
        print(f"Blockchain ready: {len(blockchain.chain)} blocks")
        
        # Create block explorer
        print("Starting web explorer...")
        explorer = create_block_explorer(blockchain, host="127.0.0.1", port=5000)
        
        # Open browser after 2 seconds
        url = "http://127.0.0.1:5000"
        Timer(2.0, open_browser, [url]).start()
        print(f"Opening dashboard at: {url}")
        
        # Start the web server
        print("Web dashboard is running...")
        print("Press Ctrl+C to stop")
        print()
        print("Available pages:")
        print(f"  Home: {url}/")
        print(f"  Blocks: {url}/blocks")
        print(f"  Search: {url}/search")
        print(f"  Stats: {url}/stats")
        print()
        print("Available API endpoints:")
        print(f"  Blockchain Info: {url}/api/v1/blockchain/info")
        print(f"  Latest Blocks: {url}/api/v1/blocks")
        print(f"  Network Stats: {url}/api/v1/stats")
        print()
        
        explorer.run(debug=False)
        
    except KeyboardInterrupt:
        print("\nStopping explorer...")
    except Exception as e:
        print(f"Error starting explorer: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
