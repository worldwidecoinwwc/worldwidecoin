# WorldWideCoin API Documentation

## Overview

This document provides comprehensive API documentation for the WorldWideCoin (WWC) cryptocurrency system. The API allows developers to interact with the blockchain, mining operations, and various network services.

## Base URL

```
http://localhost:8080/api/v1
```

## Authentication

Currently, the API does not require authentication for read operations. Write operations may require API keys in future versions.

## Response Format

All API responses return JSON format with the following structure:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "timestamp": "2026-04-13T12:00:00Z"
}
```

## Endpoints

### Blockchain Operations

#### Get Blockchain Info
```http
GET /blockchain/info
```

Returns general information about the blockchain state.

**Response:**
```json
{
  "success": true,
  "data": {
    "height": 12345,
    "difficulty": 1.23,
    "hash_rate": 1234567,
    "total_supply": 21000000,
    "block_reward": 50,
    "network_hashrate": 987654321
  }
}
```

#### Get Block by Height
```http
GET /blockchain/block/{height}
```

Retrieves block information by its height.

**Parameters:**
- `height` (integer): Block height

**Response:**
```json
{
  "success": true,
  "data": {
    "height": 12345,
    "hash": "abc123...",
    "previous_hash": "def456...",
    "timestamp": "2026-04-13T12:00:00Z",
    "transactions": [],
    "difficulty": 1.23,
    "nonce": 123456
  }
}
```

#### Get Block by Hash
```http
GET /blockchain/block/hash/{hash}
```

Retrieves block information by its hash.

**Parameters:**
- `hash` (string): Block hash

#### Get Latest Block
```http
GET /blockchain/block/latest
```

Returns the most recent block in the chain.

### Transaction Operations

#### Get Transaction by ID
```http
GET /transaction/{txid}
```

Retrieves transaction details.

**Parameters:**
- `txid` (string): Transaction ID

**Response:**
```json
{
  "success": true,
  "data": {
    "txid": "abc123...",
    "inputs": [],
    "outputs": [],
    "amount": 1000,
    "fee": 10,
    "timestamp": "2026-04-13T12:00:00Z",
    "block_height": 12345,
    "confirmations": 6
  }
}
```

#### Submit Transaction
```http
POST /transaction/submit
```

Submits a new transaction to the network.

**Request Body:**
```json
{
  "inputs": [
    {
      "txid": "abc123...",
      "vout": 0,
      "script_sig": "..."
    }
  ],
  "outputs": [
    {
      "address": "WWC123...",
      "amount": 1000,
      "script_pubkey": "..."
    }
  ]
}
```

### Mining Operations

#### Get Mining Info
```http
GET /mining/info
```

Returns current mining information.

**Response:**
```json
{
  "success": true,
  "data": {
    "difficulty": 1.23,
    "network_hashrate": 987654321,
    "block_reward": 50,
    "current_block": 12345,
    "estimated_time_to_block": 600
  }
}
```

#### Submit Block
```http
POST /mining/submit
```

Submits a mined block to the network.

**Request Body:**
```json
{
  "block": {
    "version": 1,
    "previous_hash": "def456...",
    "merkle_root": "ghi789...",
    "timestamp": "2026-04-13T12:00:00Z",
    "difficulty": 1.23,
    "nonce": 123456
  }
}
```

### Wallet Operations

#### Get Wallet Balance
```http
GET /wallet/balance
```

Returns the wallet's current balance.

**Response:**
```json
{
  "success": true,
  "data": {
    "confirmed": 1000000,
    "unconfirmed": 50000,
    "total": 1050000
  }
}
```

#### Get Wallet Address
```http
GET /wallet/address
```

Returns a new wallet address.

**Response:**
```json
{
  "success": true,
  "data": {
    "address": "WWC123abc456def789..."
  }
}
```

#### Send Transaction
```http
POST /wallet/send
```

Creates and sends a transaction from the wallet.

**Request Body:**
```json
{
  "to_address": "WWC123abc456def789...",
  "amount": 1000,
  "fee": 10
}
```

### Network Operations

#### Get Network Stats
```http
GET /network/stats
```

Returns network statistics.

**Response:**
```json
{
  "success": true,
  "data": {
    "connected_peers": 25,
    "total_peers": 100,
    "network_hashrate": 987654321,
    "difficulty": 1.23,
    "block_height": 12345
  }
}
```

#### Get Peer List
```http
GET /network/peers
```

Returns list of connected peers.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "address": "192.168.1.100:8080",
      "version": "1.0.0",
      "height": 12345,
      "ping": 50
    }
  ]
}
```

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |
| 503 | Service Unavailable - Node is syncing |

## Rate Limits

- Read operations: 100 requests per minute
- Write operations: 10 requests per minute

## WebSocket API

Real-time updates are available through WebSocket connections.

### Connection

```
ws://localhost:8080/ws
```

### Events

#### New Block
```json
{
  "type": "new_block",
  "data": {
    "height": 12345,
    "hash": "abc123...",
    "timestamp": "2026-04-13T12:00:00Z"
  }
}
```

#### New Transaction
```json
{
  "type": "new_transaction",
  "data": {
    "txid": "abc123...",
    "amount": 1000,
    "fee": 10
  }
}
```

#### Mining Update
```json
{
  "type": "mining_update",
  "data": {
    "hashrate": 1234567,
    "blocks_found": 5,
    "difficulty": 1.23
  }
}
```

## SDK Examples

### Python

```python
import requests

base_url = "http://localhost:8080/api/v1"

# Get blockchain info
response = requests.get(f"{base_url}/blockchain/info")
blockchain_info = response.json()

# Get wallet balance
response = requests.get(f"{base_url}/wallet/balance")
balance = response.json()

# Send transaction
tx_data = {
    "to_address": "WWC123abc456def789...",
    "amount": 1000,
    "fee": 10
}
response = requests.post(f"{base_url}/wallet/send", json=tx_data)
```

### JavaScript

```javascript
const baseURL = "http://localhost:8080/api/v1";

// Get blockchain info
async function getBlockchainInfo() {
  const response = await fetch(`${baseURL}/blockchain/info`);
  return await response.json();
}

// Get wallet balance
async function getWalletBalance() {
  const response = await fetch(`${baseURL}/wallet/balance`);
  return await response.json();
}

// Send transaction
async function sendTransaction(toAddress, amount, fee) {
  const response = await fetch(`${baseURL}/wallet/send`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      to_address: toAddress,
      amount: amount,
      fee: fee
    })
  });
  return await response.json();
}
```

## Testing

The API includes a test suite that can be run with:

```bash
python -m pytest tests/api/
```

## Support

For API support and questions:
- GitHub Issues: https://github.com/worldwidecoinwwc/worldwidecoin/issues
- Documentation: https://worldwidecoinwwc.github.io/worldwidecoin/
- Community: [Link to community forum/discord]

---

*This API documentation is for WorldWideCoin version 1.0.0. API may change in future versions.*
