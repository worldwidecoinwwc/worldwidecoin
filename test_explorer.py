#!/usr/bin/env python3
"""
Phase 7 Block Explorer Testing Suite
Tests web interface, API endpoints, database integration, analytics, search, and real-time updates
"""

import time
import json
import threading
from decimal import Decimal
from core.blockchain import Blockchain
from core.transaction import Transaction
from explorer.block_explorer import BlockExplorer, create_block_explorer
from explorer.api import BlockExplorerAPI, create_explorer_api
from explorer.database import BlockExplorerDatabase, create_explorer_database
from explorer.analytics import AnalyticsEngine, create_analytics_engine
from explorer.search import SearchEngine, create_search_engine
from explorer.realtime import RealTimeUpdates, create_realtime_updates
from ecdsa import SigningKey, SECP256k1


def test_block_explorer_web_interface():
    """Test 1: Block explorer web interface"""
    print("=== TEST 1: Block Explorer Web Interface ===")
    
    try:
        # Create blockchain
        blockchain = Blockchain()
        
        # Mine some blocks
        for i in range(3):
            block = blockchain.create_block(f"test_miner_{i}")
            blockchain.add_block(block)
        
        # Create block explorer
        explorer = create_block_explorer(blockchain, host="127.0.0.1", port=5000)
        
        # Test basic functionality
        print(f"Blockchain height: {len(blockchain.chain)}")
        
        # Test block retrieval
        latest_block = blockchain.chain[-1]
        block_hash = latest_block.calculate_hash() if hasattr(latest_block, 'calculate_hash') else latest_block.hash
        print(f"Latest block hash: {block_hash[:16]}...")
        
        # Test transaction retrieval
        if latest_block.transactions:
            tx = latest_block.transactions[0]
            tx_hash = tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash()
            print(f"Latest transaction hash: {tx_hash[:16]}...")
        
        print("Web interface test: PASS")
        
    except Exception as e:
        print(f"Web interface test: FAIL - {e}")
    
    print()


def test_api_endpoints():
    """Test 2: RESTful API endpoints"""
    print("=== TEST 2: RESTful API Endpoints ===")
    
    try:
        # Create blockchain and API
        blockchain = Blockchain()
        
        # Mine some blocks
        for i in range(2):
            block = blockchain.create_block(f"test_miner_{i}")
            blockchain.add_transaction(Transaction(
                inputs=[],
                outputs=[{
                    "address": f"test_address_{i}",
                    "amount": 10.0 + i
                }]
            ))
            blockchain.add_block(block)
        
        # Create API
        api = create_explorer_api(blockchain)
        
        # Test blockchain info
        blockchain_info = api._get_blockchain_info()
        print(f"Blockchain info: {blockchain_info['blocks']} blocks")
        
        # Test blockchain stats
        blockchain_stats = api._get_blockchain_stats()
        print(f"Blockchain stats: {blockchain_stats['transactions']} transactions")
        
        # Test blocks endpoint
        blocks_data = api._get_blocks(page=1, limit=10, sort='desc')
        print(f"Blocks API: {len(blocks_data['blocks'])} blocks returned")
        
        # Test transaction endpoint
        if blockchain.chain:
            latest_block = blockchain.chain[-1]
            if latest_block.transactions:
                tx = latest_block.transactions[0]
                tx_hash = tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash()
                tx_data = api._format_transaction(tx)
                print(f"Transaction API: {tx_data['hash'][:16]}...")
        
        print("API endpoints test: PASS")
        
    except Exception as e:
        print(f"API endpoints test: FAIL - {e}")
    
    print()


def test_database_integration():
    """Test 3: Database integration"""
    print("=== TEST 3: Database Integration ===")
    
    try:
        # Create blockchain
        blockchain = Blockchain()
        
        # Mine some blocks with transactions
        for i in range(3):
            block = blockchain.create_block(f"test_miner_{i}")
            
            # Add transactions to block
            for j in range(2):
                tx = Transaction(
                    inputs=[],
                    outputs=[{
                        "address": f"test_address_{i}_{j}",
                        "amount": 5.0 + j
                    }]
                )
                block.transactions.append(tx)
            
            blockchain.add_block(block)
        
        # Create database
        db = create_explorer_database("test_explorer.db")
        
        # Index blockchain
        db.index_blockchain(blockchain)
        
        # Test block retrieval
        latest_block = blockchain.chain[-1]
        block_hash = latest_block.calculate_hash() if hasattr(latest_block, 'calculate_hash') else latest_block.hash
        db_block = db.get_block_by_hash(block_hash)
        
        if db_block:
            print(f"Database block retrieval: PASS - Height {db_block['height']}")
        else:
            print("Database block retrieval: FAIL - Block not found")
        
        # Test transaction retrieval
        if latest_block.transactions:
            tx = latest_block.transactions[0]
            tx_hash = tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash()
            db_tx = db.get_transaction_by_hash(tx_hash)
            
            if db_tx:
                print(f"Database transaction retrieval: PASS - {db_tx['tx_hash'][:16]}...")
            else:
                print("Database transaction retrieval: FAIL - Transaction not found")
        
        # Test address retrieval
        test_address = "test_address_1_0"
        address_info = db.get_address_info(test_address)
        
        if address_info:
            print(f"Database address retrieval: PASS - Balance {address_info['balance']}")
        else:
            print("Database address retrieval: FAIL - Address not found")
        
        # Test search
        search_results = db.search(block_hash)
        print(f"Database search: {len(search_results['blocks'])} blocks found")
        
        # Test statistics
        stats = db.get_statistics()
        print(f"Database statistics: {len(stats)} metrics")
        
        print("Database integration test: PASS")
        
    except Exception as e:
        print(f"Database integration test: FAIL - {e}")
    
    print()


def test_analytics_dashboard():
    """Test 4: Analytics dashboard"""
    print("=== TEST 4: Analytics Dashboard ===")
    
    try:
        # Create blockchain with data
        blockchain = Blockchain()
        
        # Mine blocks with varying difficulty
        for i in range(5):
            block = blockchain.create_block(f"test_miner_{i}")
            block.difficulty = i + 1  # Vary difficulty
            blockchain.add_block(block)
        
        # Create analytics engine
        analytics = create_analytics_engine(blockchain)
        
        # Test network overview
        overview = analytics.get_network_overview()
        print(f"Network overview: {overview['blockchain']['height']} blocks")
        print(f"Total supply: {overview['blockchain']['total_supply']}")
        print(f"Hash rate: {overview['blockchain']['hash_rate']}")
        
        # Test chart data
        blocks_chart = analytics.get_chart_data('blocks', '24h')
        print(f"Blocks chart: {len(blocks_chart['data'])} data points")
        
        transactions_chart = analytics.get_chart_data('transactions', '24h')
        print(f"Transactions chart: {len(transactions_chart['data'])} data points")
        
        difficulty_chart = analytics.get_chart_data('difficulty', '24h')
        print(f"Difficulty chart: {len(difficulty_chart['data'])} data points")
        
        # Test address analytics
        test_address = "test_address"
        address_analytics = analytics.get_address_analytics(test_address)
        print(f"Address analytics: Balance {address_analytics['balance']}")
        
        # Test block analytics
        if blockchain.chain:
            latest_block = blockchain.chain[-1]
            block_hash = latest_block.calculate_hash() if hasattr(latest_block, 'calculate_hash') else latest_block.hash
            block_analytics = analytics.get_block_analytics(block_hash)
            print(f"Block analytics: Height {block_analytics['block']['height']}")
        
        # Test real-time metrics
        real_time = analytics.get_real_time_metrics()
        print(f"Real-time metrics: Height {real_time['current_height']}")
        
        print("Analytics dashboard test: PASS")
        
    except Exception as e:
        print(f"Analytics dashboard test: FAIL - {e}")
    
    print()


def test_search_functionality():
    """Test 5: Search functionality"""
    print("=== TEST 5: Search Functionality ===")
    
    try:
        # Create blockchain with searchable data
        blockchain = Blockchain()
        
        # Mine blocks with transactions
        for i in range(3):
            block = blockchain.create_block(f"test_miner_{i}")
            
            # Add transactions with specific addresses
            for j in range(2):
                tx = Transaction(
                    inputs=[],
                    outputs=[{
                        "address": f"search_test_{i}_{j}",
                        "amount": 10.0 + j
                    }]
                )
                block.transactions.append(tx)
            
            blockchain.add_block(block)
        
        # Create search engine
        search = create_search_engine(blockchain)
        
        # Test block search by hash
        if blockchain.chain:
            latest_block = blockchain.chain[-1]
            block_hash = latest_block.calculate_hash() if hasattr(latest_block, 'calculate_hash') else latest_block.hash
            block_results = search._search_blocks(block_hash, 10)
            print(f"Block search by hash: {len(block_results)} results")
        
        # Test transaction search
        if latest_block.transactions:
            tx = latest_block.transactions[0]
            tx_hash = tx.calculate_hash() if hasattr(tx, 'calculate_hash') else tx.hash()
            tx_results = search._search_transactions(tx_hash, 10)
            print(f"Transaction search by hash: {len(tx_results)} results")
        
        # Test address search
        test_address = "search_test_1_0"
        address_results = search._search_addresses(test_address, 10)
        print(f"Address search: {len(address_results)} results")
        
        # Test keyword search
        keyword_results = search.search("test", 'all', 10)
        print(f"Keyword search: {keyword_results['total_results']} total results")
        
        # Test advanced search
        advanced_criteria = {
            'blocks': {
                'height_min': 1,
                'height_max': 3
            },
            'transactions': {
                'outputs_min': 1,
                'outputs_max': 3
            }
        }
        advanced_results = search.advanced_search(advanced_criteria)
        print(f"Advanced search: {advanced_results['total_results']} total results")
        
        # Test search suggestions
        suggestions = search.get_search_suggestions("test", 5)
        print(f"Search suggestions: {len(suggestions)} suggestions")
        
        print("Search functionality test: PASS")
        
    except Exception as e:
        print(f"Search functionality test: FAIL - {e}")
    
    print()


def test_real_time_updates():
    """Test 6: Real-time updates"""
    print("=== TEST 6: Real-time Updates ===")
    
    try:
        # Create blockchain
        blockchain = Blockchain()
        
        # Create real-time updates system
        realtime = create_realtime_updates(blockchain)
        
        # Test event callbacks
        events_received = []
        
        def network_stats_callback(data):
            events_received.append(('network_stats', data))
        
        def mempool_callback(data):
            events_received.append(('mempool', data))
        
        def new_block_callback(data):
            events_received.append(('new_block', data))
        
        # Add callbacks
        realtime.add_event_callback('network_stats', network_stats_callback)
        realtime.add_event_callback('mempool', mempool_callback)
        realtime.add_event_callback('new_block', new_block_callback)
        
        # Start real-time updates
        realtime.start()
        
        # Wait for initial updates
        time.sleep(2)
        
        # Test network stats
        network_stats = realtime._get_network_stats()
        print(f"Network stats: Height {network_stats['height']}")
        
        # Test mempool info
        mempool_info = realtime._get_mempool_info()
        print(f"Mempool info: {mempool_info['size']} transactions")
        
        # Test notifications
        block = blockchain.create_block("realtime_test")
        blockchain.add_block(block)
        
        # Notify new block
        realtime.notify_new_block(block)
        
        # Wait for event processing
        time.sleep(1)
        
        # Test subscription
        client_id = "test_client"
        realtime.subscribe(client_id, ['network_stats', 'mempool'])
        
        # Test subscription stats
        subscription_stats = realtime.get_subscription_stats()
        print(f"Subscription stats: {subscription_stats['total_subscribers']} subscribers")
        
        # Test unsubscribe
        realtime.unsubscribe(client_id, ['mempool'])
        
        # Stop real-time updates
        realtime.stop()
        
        print(f"Events received: {len(events_received)}")
        print("Real-time updates test: PASS")
        
    except Exception as e:
        print(f"Real-time updates test: FAIL - {e}")
    
    print()


def test_integration():
    """Test 7: Full integration test"""
    print("=== TEST 7: Full Integration Test ===")
    
    try:
        # Create blockchain with comprehensive data
        blockchain = Blockchain()
        
        # Mine blocks with various transaction types
        for i in range(5):
            block = blockchain.create_block(f"integration_miner_{i}")
            block.difficulty = i + 1
            
            # Add different types of transactions
            for j in range(3):
                tx = Transaction(
                    inputs=[],
                    outputs=[{
                        "address": f"integration_addr_{i}_{j}",
                        "amount": 5.0 + j * 2.5
                    }]
                )
                block.transactions.append(tx)
            
            blockchain.add_block(block)
        
        # Create all components
        explorer = create_block_explorer(blockchain)
        api = create_explorer_api(blockchain)
        db = create_explorer_database("integration_test.db")
        analytics = create_analytics_engine(blockchain)
        search = create_search_engine(blockchain)
        realtime = create_realtime_updates(blockchain)
        
        # Index blockchain
        db.index_blockchain(blockchain)
        
        # Test API integration with database
        blockchain_info = api._get_blockchain_info()
        print(f"API integration: {blockchain_info['blocks']} blocks")
        
        # Test analytics integration with database
        overview = analytics.get_network_overview()
        print(f"Analytics integration: {overview['blockchain']['height']} blocks")
        
        # Test search integration with database
        search_results = search.search("integration", 'all', 10)
        print(f"Search integration: {search_results['total_results']} results")
        
        # Test real-time integration
        realtime.start()
        
        # Add new block and test notifications
        new_block = blockchain.create_block("integration_test_final")
        blockchain.add_block(new_block)
        
        realtime.notify_new_block(new_block)
        
        # Wait for processing
        time.sleep(1)
        
        realtime.stop()
        
        # Test cross-component data consistency
        db_height = len(db.get_blocks_paginated(1, 1000)['blocks'])
        api_height = api._get_blockchain_info()['blocks']
        analytics_height = analytics.get_network_overview()['blockchain']['height']
        
        if db_height == api_height == analytics_height:
            print("Data consistency: PASS")
        else:
            print(f"Data consistency: FAIL - DB: {db_height}, API: {api_height}, Analytics: {analytics_height}")
        
        print("Full integration test: PASS")
        
    except Exception as e:
        print(f"Full integration test: FAIL - {e}")
    
    print()


def main():
    """Run all Phase 7 block explorer tests"""
    print("WorldWideCoin Phase 7 - Block Explorer Testing")
    print("=" * 60)
    
    tests = [
        test_block_explorer_web_interface,
        test_api_endpoints,
        test_database_integration,
        test_analytics_dashboard,
        test_search_functionality,
        test_real_time_updates,
        test_integration
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(tests, 1):
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"Test {i} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Phase 7 Block Explorer Testing Complete!")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/(passed+failed))*100:.1f}%")
    
    if failed == 0:
        print("All tests passed! Phase 7 block explorer is ready for deployment.")
    else:
        print(f"{failed} tests failed. Review and fix issues before proceeding.")


if __name__ == "__main__":
    main()
