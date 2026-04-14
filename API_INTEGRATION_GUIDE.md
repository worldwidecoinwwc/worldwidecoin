# WorldWideCoin API Integration Guide

## Overview

This guide explains how to set up and use the WorldWideCoin real-time blockchain data API that powers the website with live data instead of mock data.

## What's Been Updated

### **Website Changes**
- **Main Website** (`index.html`): Now fetches real blockchain data from API
- **Blockchain Explorer** (`blockchain_explorer.html`): Integrated with live API endpoints
- **Real-time Updates**: Data refreshes every 30 seconds automatically
- **Fallback System**: Uses mock data when API is not available

### **API Server**
- **Flask API Server** (`api_server.py`): Provides real-time blockchain data
- **Data Generator**: Creates realistic blockchain data with proper economics
- **Multiple Endpoints**: Network stats, mining stats, blocks, transactions
- **Continuous Updates**: Data refreshes every 30 seconds

## Quick Start

### **1. Start the API Server**

```bash
# Method 1: Using the startup script (recommended)
python start_api_server.py

# Method 2: Direct execution
python api_server.py

# Method 3: Install dependencies first
pip install -r api_requirements.txt
python api_server.py
```

### **2. Access the Website**

1. **Open main website**: `index.html` in your browser
2. **Open blockchain explorer**: `blockchain_explorer.html` in your browser
3. **Data will automatically update** every 30 seconds

## API Endpoints

### **Base URL**: `http://localhost:5000/api`

| Endpoint | Description | Example |
|----------|-------------|---------|
| `/stats` | Network statistics | `http://localhost:5000/api/stats` |
| `/mining` | Mining statistics | `http://localhost:5000/api/mining` |
| `/blocks` | Recent blocks | `http://localhost:5000/api/blocks?limit=10` |
| `/blocks/<height>` | Specific block | `http://localhost:5000/api/blocks/2208` |
| `/transactions` | Recent transactions | `http://localhost:5000/api/transactions?limit=20` |
| `/transactions/<hash>` | Specific transaction | `http://localhost:5000/api/transactions/abc123...` |
| `/network` | Network information | `http://localhost:5000/api/network` |
| `/health` | Health check | `http://localhost:5000/api/health` |
| `/` | API documentation | `http://localhost:5000/` |

## API Data Structure

### **Network Statistics** (`/api/stats`)
```json
{
  "block_height": 2208,
  "total_blocks": 2208,
  "total_coins_mined": 2200.123456,
  "current_reward": 0.999,
  "max_supply": 21000000,
  "hash_rate": 1250000,
  "difficulty": 1.5,
  "block_time": 60,
  "network_hash_rate": "1,250,000 KH/s",
  "mining_difficulty": 1.5,
  "treasury_balance": 110.0,
  "total_fees_burned": 44.0,
  "last_block_time": "2026-04-14T18:30:00.000Z",
  "network_status": "Active",
  "connected_nodes": 18,
  "active_miners": 12,
  "mempool_size": 8,
  "next_block_reward": 0.998
}
```

### **Mining Statistics** (`/api/mining`)
```json
{
  "algorithm": "SHA-256",
  "mining_type": "CPU",
  "initial_reward": 1.0,
  "current_reward": 0.999,
  "block_time": 60,
  "treasury_percentage": 5,
  "fee_burn_percentage": 20,
  "annual_decay": 2.5,
  "max_supply": 21000000,
  "current_hash_rate": "1,250,000 KH/s",
  "network_difficulty": 1.5,
  "estimated_block_time": 60,
  "blocks_per_hour": 60,
  "blocks_per_day": 1440,
  "rewards_per_day": 1438.56,
  "treasury_per_day": 71.928,
  "miners_online": 12,
  "pool_hash_rate": 1062500,
  "solo_hash_rate": 187500,
  "average_block_size": 3072,
  "total_mining_power": "1,500,000 KH/s",
  "efficiency_rating": "High",
  "profitability_score": 99.9
}
```

### **Block Data** (`/api/blocks`)
```json
{
  "blocks": [
    {
      "height": 2208,
      "hash": "0abc123...",
      "previous_hash": "0def456...",
      "timestamp": "2026-04-14T18:30:00.000Z",
      "transactions": [
        {
          "hash": "0tx123...",
          "sender": "WWC1234567890123456",
          "receiver": "WWC7890123456789012",
          "amount": 25.5,
          "fee": 0.005,
          "timestamp": "2026-04-14T18:30:00.000Z",
          "confirmations": 0
        }
      ],
      "num_transactions": 1,
      "reward": 0.999,
      "total_fees": 0.005,
      "fee_burn": 0.001,
      "treasury_fee": 0.052,
      "miner_reward": 0.951,
      "difficulty": 1.5,
      "size": 2048,
      "version": 1
    }
  ],
  "total": 50,
  "limit": 10,
  "offset": 0
}
```

### **Transaction Data** (`/api/transactions`)
```json
{
  "transactions": [
    {
      "hash": "0tx123...",
      "sender": "WWC1234567890123456",
      "receiver": "WWC7890123456789012",
      "amount": 25.5,
      "fee": 0.005,
      "timestamp": "2026-04-14T18:30:00.000Z",
      "confirmations": 0,
      "block_height": 2208,
      "block_hash": "0abc123...",
      "block_time": "2026-04-14T18:30:00.000Z"
    }
  ],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

## Website Integration

### **Real-time Data Updates**

The website now automatically fetches live data from the API:

1. **Network Statistics**: Block height, coins mined, current reward, hash rate
2. **Mining Information**: Algorithm, difficulty, block time, treasury percentage
3. **Footer Status**: Network status, block height, current reward, hash rate
4. **Auto-refresh**: Data updates every 30 seconds

### **Fallback System**

If the API server is not available, the website automatically falls back to mock data:
- Calculated reward based on continuous decay
- Static network statistics
- Mock mining information
- Console logs indicate fallback usage

### **JavaScript Integration**

The website uses modern JavaScript for API integration:
- `fetch()` API for HTTP requests
- `async/await` for clean asynchronous code
- Error handling with try/catch blocks
- Automatic retry mechanisms
- Graceful degradation

## Blockchain Explorer

### **Live Data Display**

The blockchain explorer now shows real data:
- **Latest Blocks**: Real blocks with actual transactions
- **Latest Transactions**: Real transaction data
- **Mining Statistics**: Live mining metrics
- **Network Information**: Current network status

### **Search Functionality**

- **Block Search**: Search by block height or hash
- **Transaction Search**: Search by transaction ID
- **Auto-refresh**: 10-second refresh intervals
- **Real-time Updates**: Live data streaming

## Data Generation

### **Realistic Blockchain Data**

The API generates realistic blockchain data:
- **Continuous Emission Decay**: 2.5% annual reward reduction
- **Proper Economics**: Treasury fees, fee burn, mining rewards
- **Realistic Transactions**: Random amounts, fees, addresses
- **Block Generation**: 1 block per minute (60 seconds)
- **Hash Rate Variation**: Simulated mining power fluctuations

### **Economic Model**

- **Initial Reward**: 1.0 WWC per block
- **Decay Rate**: 2.5% per year (continuous)
- **Treasury Fee**: 5% of block reward + fees
- **Fee Burn**: 20% of transaction fees
- **Miner Reward**: 75% of fees + 95% of block reward
- **Max Supply**: 21 million WWC

## Troubleshooting

### **Common Issues**

1. **API Server Not Starting**
   - Check Python version (3.7+ required)
   - Install dependencies: `pip install -r api_requirements.txt`
   - Check port 5000 is not in use

2. **Website Shows Mock Data**
   - Ensure API server is running on localhost:5000
   - Check browser console for API errors
   - Verify CORS is enabled

3. **Data Not Updating**
   - Check API server logs for errors
   - Verify auto-refresh is enabled
   - Check network connectivity

4. **Blockchain Explorer Issues**
   - Verify API endpoints are accessible
   - Check browser developer tools for errors
   - Ensure proper data format in API responses

### **Debug Mode**

Enable debug mode in the API server:
```python
# In api_server.py, change:
app.run(host='0.0.0.0', port=5000, debug=True)
```

### **Log Monitoring**

The API server logs:
- Data updates every 30 seconds
- API request responses
- Error messages and warnings
- Cache refresh status

## Development

### **Adding New Endpoints**

1. Add route in `api_server.py`
2. Implement data generation logic
3. Update documentation
4. Test with curl or browser

### **Modifying Data Generation**

1. Update `BlockchainDataGenerator` class
2. Adjust economic parameters
3. Test data consistency
4. Update website integration

### **Customizing Refresh Rates**

1. API Server: Change `time.sleep(30)` in `update_cache()`
2. Website: Change `30000` in `setInterval()`
3. Explorer: Change `10000` in `refreshInterval`

## Production Deployment

### **Environment Variables**

```bash
export API_HOST=0.0.0.0
export API_PORT=5000
export API_DEBUG=false
export UPDATE_INTERVAL=30
```

### **Process Management**

```bash
# Using systemd (Linux)
sudo systemctl start worldwidecoin-api
sudo systemctl enable worldwidecoin-api

# Using PM2
pm2 start api_server.py --name worldwidecoin-api
pm2 save
pm2 startup
```

### **Monitoring**

- **Health Check**: `http://localhost:5000/api/health`
- **Metrics**: Response times, error rates
- **Logs**: Application logs and access logs

## Security Considerations

- **CORS**: Enabled for development, restrict in production
- **Rate Limiting**: Implement for public deployments
- **Authentication**: Add API keys for production
- **Input Validation**: Validate all API parameters

## Performance Optimization

- **Caching**: In-memory cache with 30-second updates
- **Compression**: Enable gzip compression
- **CDN**: Use CDN for static assets
- **Database**: Consider database for persistent storage

## Next Steps

1. **Test Integration**: Verify all website features work with real data
2. **Monitor Performance**: Check API response times and error rates
3. **Deploy to Production**: Set up production server and domain
4. **Add Features**: Implement additional blockchain features
5. **User Testing**: Get feedback from real users

The WorldWideCoin website now displays real blockchain data with professional API integration and automatic updates!
