// WorldWideCoin Dashboard JavaScript

class WWCDashboard {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8001'; // Default to first node
        this.walletAddress = localStorage.getItem('walletAddress') || '';
        this.notifications = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkAPIConnection();
        this.loadInitialData();

        // Auto-refresh data every 30 seconds
        setInterval(() => {
            this.refreshData();
        }, 30000);
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.showSection(e.target.textContent.toLowerCase());
            });
        });

        // Wallet address input
        const addressInput = document.getElementById('walletAddress');
        if (addressInput) {
            addressInput.value = this.walletAddress;
            addressInput.addEventListener('input', (e) => {
                this.walletAddress = e.target.value;
                localStorage.setItem('walletAddress', this.walletAddress);
                this.updateBalance();
            });
        }
    }

    showSection(sectionName) {
        // Update navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[onclick="showSection('${sectionName}')"]`).classList.add('active');

        // Show section
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(sectionName).classList.add('active');

        // Load section-specific data
        switch(sectionName) {
            case 'overview':
                this.loadOverviewData();
                break;
            case 'wallet':
                this.updateBalance();
                this.loadTransactionHistory();
                break;
            case 'network':
                this.loadPeers();
                break;
            case 'mining':
                this.loadMiningStatus();
                break;
        }
    }

    async checkAPIConnection() {
        const statusElement = document.getElementById('apiStatus');
        try {
            const response = await fetch(`${this.apiBaseUrl}/chain`);
            if (response.ok) {
                statusElement.textContent = 'Connected';
                statusElement.className = 'connected';
            } else {
                throw new Error('API returned error');
            }
        } catch (error) {
            statusElement.textContent = 'Disconnected';
            statusElement.className = 'disconnected';
            this.showNotification('Failed to connect to API. Make sure the blockchain node is running.', 'error');
        }
    }

    async loadInitialData() {
        await Promise.all([
            this.loadOverviewData(),
            this.updateBalance(),
            this.loadPeers(),
            this.loadMiningStatus()
        ]);
    }

    async refreshData() {
        const activeSection = document.querySelector('.section.active').id;
        switch(activeSection) {
            case 'overview':
                await this.loadOverviewData();
                break;
            case 'wallet':
                await this.updateBalance();
                break;
            case 'network':
                await this.loadPeers();
                break;
            case 'mining':
                await this.loadMiningStatus();
                break;
        }
    }

    async loadOverviewData() {
        try {
            // Load blockchain data
            const chainResponse = await fetch(`${this.apiBaseUrl}/chain`);
            const chainData = await chainResponse.json();

            // Update stats
            document.getElementById('blockCount').textContent = chainData.length;
            document.getElementById('difficulty').textContent = chainData.length > 0 ?
                chainData[chainData.length - 1].difficulty || 'N/A' : 'N/A';

            // Load peers
            const peersResponse = await fetch(`${this.apiBaseUrl}/peers`);
            const peersData = await peersResponse.json();
            document.getElementById('peerCount').textContent = peersData.length;

            // Load mempool
            const mempoolResponse = await fetch(`${this.apiBaseUrl}/mempool`);
            const mempoolData = await mempoolResponse.json();
            document.getElementById('mempoolCount').textContent = mempoolData.length;

            // Load recent blocks
            this.displayRecentBlocks(chainData.slice(-5));

        } catch (error) {
            console.error('Error loading overview data:', error);
            this.showNotification('Failed to load overview data', 'error');
        }
    }

    displayRecentBlocks(blocks) {
        const container = document.getElementById('recentBlocks');
        if (blocks.length === 0) {
            container.innerHTML = '<div class="empty">No blocks found</div>';
            return;
        }

        container.innerHTML = blocks.reverse().map(block => `
            <div class="block-item">
                <div>
                    <div class="block-hash">${block.hash.substring(0, 16)}...</div>
                    <div class="block-info">
                        <span><i class="fas fa-clock"></i> ${new Date(block.timestamp * 1000).toLocaleString()}</span>
                        <span><i class="fas fa-exchange-alt"></i> ${block.transactions ? block.transactions.length : 0} tx</span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async updateBalance() {
        if (!this.walletAddress) {
            document.getElementById('balance').textContent = '0.00 WWC';
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/utxo/${this.walletAddress}`);
            const utxoData = await response.json();

            let balance = 0;
            if (utxoData && Array.isArray(utxoData)) {
                balance = utxoData.reduce((sum, utxo) => sum + utxo.amount, 0);
            }

            document.getElementById('balance').textContent = `${balance.toFixed(2)} WWC`;
        } catch (error) {
            console.error('Error updating balance:', error);
            document.getElementById('balance').textContent = 'Error';
        }
    }

    async loadTransactionHistory() {
        if (!this.walletAddress) {
            document.getElementById('transactionHistory').innerHTML = '<div class="empty">Enter an address to view transactions</div>';
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/chain`);
            const chainData = await response.json();

            const transactions = [];
            chainData.forEach(block => {
                if (block.transactions) {
                    block.transactions.forEach(tx => {
                        // Check if this address is involved
                        const isSender = tx.inputs.some(input => input.address === this.walletAddress);
                        const isReceiver = tx.outputs.some(output => output.address === this.walletAddress);

                        if (isSender || isReceiver) {
                            transactions.push({
                                ...tx,
                                blockHash: block.hash,
                                timestamp: block.timestamp,
                                isSender,
                                isReceiver
                            });
                        }
                    });
                }
            });

            this.displayTransactionHistory(transactions.slice(-10));
        } catch (error) {
            console.error('Error loading transaction history:', error);
            document.getElementById('transactionHistory').innerHTML = '<div class="error">Failed to load transactions</div>';
        }
    }

    displayTransactionHistory(transactions) {
        const container = document.getElementById('transactionHistory');
        if (transactions.length === 0) {
            container.innerHTML = '<div class="empty">No transactions found</div>';
            return;
        }

        container.innerHTML = transactions.reverse().map(tx => `
            <div class="transaction-item">
                <div class="transaction-info">
                    <div class="transaction-hash">${tx.id.substring(0, 16)}...</div>
                    <div class="transaction-details">
                        ${tx.isSender ? 'Sent' : 'Received'} •
                        ${new Date(tx.timestamp * 1000).toLocaleString()}
                    </div>
                </div>
                <div class="transaction-amount">
                    ${tx.isSender ? '-' : '+'}${tx.outputs.find(o => o.address === this.walletAddress)?.amount || 0} WWC
                </div>
            </div>
        `).join('');
    }

    async loadPeers() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/peers`);
            const peers = await response.json();

            const container = document.getElementById('peersList');
            if (peers.length === 0) {
                container.innerHTML = '<div class="empty">No peers connected</div>';
                return;
            }

            container.innerHTML = peers.map(peer => `
                <div class="peer-item">
                    <div class="peer-address">${peer.host}:${peer.port}</div>
                    <div class="peer-status">Connected</div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Error loading peers:', error);
            document.getElementById('peersList').innerHTML = '<div class="error">Failed to load peers</div>';
        }
    }

    async loadMiningStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/mining/status`);
            const status = await response.json();

            const container = document.getElementById('miningStatus');
            container.innerHTML = `
                <div class="mining-metric">
                    <strong>Status:</strong> ${status.is_mining ? 'Active' : 'Inactive'}
                </div>
                <div class="mining-metric">
                    <strong>Hash Rate:</strong> ${status.hash_rate || 'N/A'} H/s
                </div>
                <div class="mining-metric">
                    <strong>Blocks Mined:</strong> ${status.blocks_mined || 0}
                </div>
            `;
        } catch (error) {
            console.error('Error loading mining status:', error);
            document.getElementById('miningStatus').innerHTML = '<div class="error">Mining status unavailable</div>';
        }
    }

    async sendTransaction(event) {
        event.preventDefault();

        const recipient = document.getElementById('recipient').value;
        const amount = parseFloat(document.getElementById('amount').value);

        if (!this.walletAddress) {
            this.showNotification('Please enter your wallet address first', 'warning');
            return;
        }

        if (!recipient || !amount || amount <= 0) {
            this.showNotification('Please enter valid recipient and amount', 'warning');
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/transaction`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    sender: this.walletAddress,
                    recipient: recipient,
                    amount: amount
                })
            });

            if (response.ok) {
                const result = await response.json();
                this.showNotification(`Transaction sent! TXID: ${result.txid}`, 'success');
                document.getElementById('sendForm').reset();
                this.updateBalance();
                this.loadTransactionHistory();
            } else {
                const error = await response.text();
                throw new Error(error);
            }
        } catch (error) {
            console.error('Error sending transaction:', error);
            this.showNotification('Failed to send transaction: ' + error.message, 'error');
        }
    }

    async addPeer(event) {
        event.preventDefault();

        const host = document.getElementById('peerHost').value;
        const port = parseInt(document.getElementById('peerPort').value);

        try {
            const response = await fetch(`${this.apiBaseUrl}/peer`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    host: host,
                    port: port
                })
            });

            if (response.ok) {
                this.showNotification(`Peer ${host}:${port} added successfully`, 'success');
                document.getElementById('peerForm').reset();
                this.loadPeers();
            } else {
                const error = await response.text();
                throw new Error(error);
            }
        } catch (error) {
            console.error('Error adding peer:', error);
            this.showNotification('Failed to add peer: ' + error.message, 'error');
        }
    }

    generateAddress() {
        // This would typically call a wallet generation endpoint
        // For now, we'll show a placeholder
        this.showNotification('Address generation requires wallet service. Use CLI to generate addresses.', 'warning');
    }

    startMining() {
        this.showNotification('Mining control requires CLI or dedicated miner service.', 'warning');
    }

    stopMining() {
        this.showNotification('Mining control requires CLI or dedicated miner service.', 'warning');
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div>${message}</div>
            <button onclick="this.parentElement.remove()" style="float: right; background: none; border: none; color: inherit; cursor: pointer;">×</button>
        `;

        document.getElementById('notifications').appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new WWCDashboard();
});

// Global functions for HTML onclick handlers
function showSection(sectionName) {
    window.dashboard.showSection(sectionName);
}

function generateAddress() {
    window.dashboard.generateAddress();
}

function sendTransaction(event) {
    window.dashboard.sendTransaction(event);
}

function addPeer(event) {
    window.dashboard.addPeer(event);
}

function startMining() {
    window.dashboard.startMining();
}

function stopMining() {
    window.dashboard.stopMining();
}