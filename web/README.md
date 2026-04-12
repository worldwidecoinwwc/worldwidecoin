# WorldWideCoin Web Dashboard

A modern web interface for interacting with the WorldWideCoin blockchain network.

## Features

- **📊 Blockchain Overview**: View recent blocks, network statistics, and difficulty
- **💰 Wallet Management**: Check balances, send transactions, view transaction history
- **🌐 Network Status**: Monitor connected peers and add new network connections
- **⛏️ Mining Dashboard**: View mining status and controls
- **🔄 Real-time Updates**: Automatic data refresh every 30 seconds
- **📱 Responsive Design**: Works on desktop and mobile devices

## Quick Start

### Prerequisites
- WorldWideCoin blockchain node running (REST API available)
- Modern web browser

### Running the Dashboard

#### Option 1: Python Server (Recommended)
```bash
# From the worldwidecoin directory
python web_server.py --open
```

This starts the dashboard server on `http://localhost:8080` and opens it in your browser.

#### Option 2: Direct File Access
Open `web/index.html` directly in your browser (limited functionality due to CORS).

#### Option 3: Any Web Server
Serve the `web/` directory with any static web server:
```bash
# Using Python's built-in server
cd web
python -m http.server 8080

# Using Node.js
npx serve web -p 8080

# Using PHP
cd web
php -S localhost:8080
```

## Configuration

### API Endpoint
By default, the dashboard connects to `http://localhost:8001` (first Docker node).

To use a different API endpoint:
1. Open browser developer tools (F12)
2. Go to Console
3. Run: `dashboard.apiBaseUrl = 'http://your-api-url:port'`

### Command Line Options
```bash
python web_server.py [options]

Options:
  --port PORT        Port to serve dashboard on (default: 8080)
  --host HOST        Host to bind to (default: localhost)
  --open             Open browser automatically
  --api-url URL      WorldWideCoin API URL (for reference only)
```

## Usage Guide

### Overview Tab
- View blockchain statistics (blocks, difficulty, peers, mempool)
- See recent blocks with timestamps and transaction counts

### Wallet Tab
- **Address**: Enter your wallet address to view balance and transactions
- **Balance**: Shows your current WWC balance
- **Send Coins**: Transfer WWC to other addresses
- **Transaction History**: View your recent transactions

### Network Tab
- **Connected Peers**: List of active network connections
- **Add Peer**: Connect to additional blockchain nodes

### Mining Tab
- **Mining Status**: Current mining activity and statistics
- **Mining Controls**: Start/stop mining (requires CLI or miner service)

## API Integration

The dashboard communicates with the WorldWideCoin REST API endpoints:

- `GET /chain` - Blockchain data
- `GET /utxo/{address}` - Address balance
- `POST /transaction` - Send transactions
- `GET /peers` - Network peers
- `POST /peer` - Add peer
- `GET /mempool` - Pending transactions
- `GET /mining/status` - Mining information

## Troubleshooting

### "Disconnected" Status
- Ensure a WorldWideCoin node is running
- Check that the API is accessible at the configured URL
- Verify CORS settings if using direct file access

### Transaction Failures
- Verify you have sufficient balance
- Check that your address is correct
- Ensure the recipient address is valid

### Mining Not Working
- Mining controls require a running miner process
- Use the CLI (`python cli/cli.py mine`) or Docker miner service

## Development

### File Structure
```
web/
├── index.html      # Main dashboard HTML
├── styles.css      # Dashboard styling
├── app.js         # JavaScript functionality
└── README.md      # This file
```

### Adding New Features
1. Add HTML structure to `index.html`
2. Add CSS styles to `styles.css`
3. Implement JavaScript logic in `app.js`
4. Update API calls as needed

### Building for Production
- Minify CSS and JavaScript files
- Optimize images and assets
- Enable gzip compression on your web server
- Consider using a CDN for static assets

## Browser Support

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This dashboard is part of the WorldWideCoin project. See main project license for details.