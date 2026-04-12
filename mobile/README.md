# WorldWideCoin Mobile Wallet

A lightweight mobile wallet interface for WorldWideCoin. This wallet is built as a mobile-first web app and runs in the browser on smartphones, tablets, or desktop devices.

## Features

- Generate a new wallet locally
- Import an existing private key
- View address and balance
- Query UTXOs from the WorldWideCoin API
- Build, sign, and broadcast transactions from the client
- View recent transaction history for the wallet address
- Encrypted backup and restore of your wallet private key

## Getting Started

### 1. Start the WorldWideCoin API

Make sure your API server is running and accessible.

```bash
python cli/cli.py api --host 0.0.0.0 --port 8001
```

### 2. Serve the mobile wallet

From the `mobile/` directory:

```bash
cd mobile
python -m http.server 8082
```

Then open the browser on your phone or computer:

```text
http://localhost:8082
```

If you want to access the wallet from another device, replace `localhost` with your machine IP in both the URL and the API endpoint.

## API Requirements

The mobile wallet uses these API endpoints:

- `GET /health` - API health check
- `GET /utxo/<address>` - Fetch UTXOs and balance
- `GET /history/<address>` - Fetch address transaction history
- `POST /tx` - Broadcast raw signed transaction

## Security Notes

- Private keys are stored locally in browser `localStorage`
- Keys never leave the device unless exported manually
- The wallet only broadcasts signed transactions to the API

## Advanced Usage

- Import a wallet by pasting a private key
- Add the app to your home screen for a native feel
- Use a custom API URL if your WorldWideCoin node is hosted elsewhere

## Development

If you want to extend the wallet:

- `mobile/index.html` - UI layout
- `mobile/styles.css` - Mobile styling
- `mobile/app.js` - Wallet logic and API integration
