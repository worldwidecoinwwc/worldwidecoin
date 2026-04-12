const ec = new elliptic.ec('secp256k1');

class WWCMobileWallet {
    constructor() {
        this.apiUrl = localStorage.getItem('wwc_api_url') || 'http://localhost:8001';
        this.wallet = null;
        this.init();
    }

    init() {
        this.bindElements();
        this.loadApiUrl();
        this.loadWallet();
        this.checkApi();
        this.refresh();
    }

    bindElements() {
        this.apiUrlInput = document.getElementById('apiUrlInput');
        this.setApiButton = document.getElementById('setApiButton');
        this.apiStatus = document.getElementById('apiStatus');
        this.refreshButton = document.getElementById('refreshButton');
        this.walletAddress = document.getElementById('walletAddress');
        this.walletPrivateKey = document.getElementById('walletPrivateKey');
        this.balanceValue = document.getElementById('balanceValue');
        this.generateButton = document.getElementById('generateButton');
        this.importButton = document.getElementById('importButton');
        this.backupButton = document.getElementById('backupButton');
        this.downloadBackupButton = document.getElementById('downloadBackupButton');
        this.restoreButton = document.getElementById('restoreButton');
        this.uploadBackupButton = document.getElementById('uploadBackupButton');
        this.backupFileInput = document.getElementById('backupFileInput');
        this.backupOutput = document.getElementById('backupOutput');
        this.recipientInput = document.getElementById('recipientInput');
        this.amountInput = document.getElementById('amountInput');
        this.sendButton = document.getElementById('sendButton');
        this.historyList = document.getElementById('historyList');
        this.logOutput = document.getElementById('logOutput');
        this.toast = document.getElementById('toast');

        this.setApiButton.addEventListener('click', () => this.saveApiUrl());
        this.refreshButton.addEventListener('click', () => this.refresh());
        this.generateButton.addEventListener('click', () => this.generateWallet());
        this.importButton.addEventListener('click', () => this.importWallet());
        this.backupButton.addEventListener('click', () => this.backupWallet());
        this.downloadBackupButton.addEventListener('click', () => this.downloadBackup());
        this.restoreButton.addEventListener('click', () => this.restoreWallet());
        this.uploadBackupButton.addEventListener('click', () => this.uploadBackup());
        this.backupFileInput.addEventListener('change', (event) => this.handleBackupFileUpload(event));
        this.sendButton.addEventListener('click', () => this.sendTransaction());
    }

    log(message) {
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        entry.textContent = `${new Date().toLocaleTimeString()}: ${message}`;
        this.logOutput.prepend(entry);
    }

    toastMessage(message, success = true) {
        this.toast.textContent = message;
        this.toast.classList.remove('hidden');
        this.toast.classList.add('visible');
        this.toast.style.borderColor = success ? '#22c55e' : '#f97316';
        setTimeout(() => {
            this.toast.classList.remove('visible');
            this.toast.classList.add('hidden');
        }, 4000);
    }

    loadApiUrl() {
        this.apiUrlInput.value = this.apiUrl;
        this.log(`API URL loaded: ${this.apiUrl}`);
    }

    async saveApiUrl() {
        this.apiUrl = this.apiUrlInput.value.trim() || this.apiUrl;
        localStorage.setItem('wwc_api_url', this.apiUrl);
        this.log(`API URL saved: ${this.apiUrl}`);
        await this.checkApi();
        await this.refresh();
    }

    loadWallet() {
        const storedKey = localStorage.getItem('wwc_wallet_private_key');
        if (storedKey) {
            this.wallet = this.createWalletFromPrivateKey(storedKey);
            this.log('Wallet loaded from local storage');
        } else {
            this.generateWallet();
        }
    }

    generateWallet() {
        const keyPair = ec.genKeyPair();
        const privateKey = keyPair.getPrivate('hex');
        this.wallet = this.createWalletFromPrivateKey(privateKey);
        this.saveWallet();
        this.log('Generated new wallet');
        this.renderWallet();
        this.refresh();
        this.toastMessage('New mobile wallet generated');
    }

    importWallet() {
        const privateKey = prompt('Paste your private key (hex string)');
        if (!privateKey) {
            return;
        }

        try {
            this.wallet = this.createWalletFromPrivateKey(privateKey.trim());
            this.saveWallet();
            this.renderWallet();
            this.refresh();
            this.toastMessage('Wallet imported successfully');
            this.log('Imported wallet from private key');
        } catch (error) {
            console.error(error);
            this.toastMessage('Invalid private key', false);
        }
    }

    createWalletFromPrivateKey(privateKey) {
        const keyPair = ec.keyFromPrivate(privateKey, 'hex');
        let publicKey = keyPair.getPublic().encode('hex', false);
        if (publicKey.startsWith('04')) {
            publicKey = publicKey.slice(2);
        }
        const address = this.computeAddress(publicKey);
        return {
            privateKey,
            publicKey,
            address,
            keyPair
        };
    }

    saveWallet() {
        localStorage.setItem('wwc_wallet_private_key', this.wallet.privateKey);
        this.renderWallet();
    }

    checkPasswordStrength(password) {
        const lengthValid = password.length >= 12;
        const upper = /[A-Z]/.test(password);
        const lower = /[a-z]/.test(password);
        const digit = /[0-9]/.test(password);
        const special = /[^A-Za-z0-9]/.test(password);

        const issues = [];
        if (!lengthValid) issues.push('at least 12 characters');
        if (!upper) issues.push('an uppercase letter');
        if (!lower) issues.push('a lowercase letter');
        if (!digit) issues.push('a number');
        if (!special) issues.push('a special character');

        return {
            valid: lengthValid && upper && lower && digit && special,
            message: issues.length ? `Use ${issues.join(', ')}` : 'Strong password'
        };
    }

    async backupWallet() {
        const password = prompt('Enter a password to encrypt your backup');
        if (!password) {
            this.toastMessage('Backup cancelled', false);
            return;
        }

        const strength = this.checkPasswordStrength(password);
        if (!strength.valid) {
            const proceed = confirm(`Weak password: ${strength.message}. Do you want to continue?`);
            if (!proceed) {
                this.toastMessage('Choose a stronger password', false);
                return;
            }
        }

        const confirmPassword = prompt('Confirm your backup password');
        if (confirmPassword !== password) {
            this.toastMessage('Passwords do not match', false);
            return;
        }

        const payload = JSON.stringify({
            private_key: this.wallet.privateKey,
            address: this.wallet.address,
            created_at: new Date().toISOString()
        });

        try {
            const backupData = await this.encryptBackup(payload, password);
            this.backupOutput.value = backupData;
            this.toastMessage('Encrypted backup generated');
            this.log('Wallet backup created');
        } catch (error) {
            console.error(error);
            this.toastMessage('Backup failed', false);
        }
    }

    async restoreWallet() {
        const backupData = this.backupOutput.value.trim();
        if (!backupData) {
            this.toastMessage('Paste backup data into the text box first', false);
            return;
        }

        const password = prompt('Enter your backup password');
        if (!password) {
            this.toastMessage('Restore cancelled', false);
            return;
        }

        try {
            const decrypted = await this.decryptBackup(backupData, password);
            const payload = JSON.parse(decrypted);
            if (!payload.private_key || !payload.address) {
                throw new Error('Invalid backup file');
            }

            this.wallet = this.createWalletFromPrivateKey(payload.private_key);
            if (this.wallet.address !== payload.address) {
                throw new Error('Backup address mismatch');
            }

            this.saveWallet();
            this.renderWallet();
            await this.refresh();
            this.toastMessage('Wallet restored successfully');
            this.log('Wallet restored from backup');
        } catch (error) {
            console.error(error);
            this.toastMessage('Restore failed: ' + (error.message || 'Invalid backup'), false);
        }
    }

    async encryptBackup(text, password) {
        const salt = crypto.getRandomValues(new Uint8Array(16));
        const iv = crypto.getRandomValues(new Uint8Array(12));
        const key = await this.deriveKey(password, salt);
        const encoded = new TextEncoder().encode(text);
        const encrypted = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, encoded);
        return JSON.stringify({
            version: 1,
            cipher: 'AES-GCM',
            salt: this.arrayBufferToBase64(salt),
            iv: this.arrayBufferToBase64(iv),
            data: this.arrayBufferToBase64(encrypted)
        });
    }

    async decryptBackup(data, password) {
        const parsed = JSON.parse(data);
        if (!parsed.salt || !parsed.iv || !parsed.data) {
            throw new Error('Backup file is not valid');
        }

        const salt = this.base64ToArrayBuffer(parsed.salt);
        const iv = this.base64ToArrayBuffer(parsed.iv);
        const encrypted = this.base64ToArrayBuffer(parsed.data);
        const key = await this.deriveKey(password, salt);
        const decrypted = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, key, encrypted);
        return new TextDecoder().decode(decrypted);
    }

    async downloadBackup() {
        if (!this.backupOutput.value.trim()) {
            await this.backupWallet();
        }

        const backupData = this.backupOutput.value.trim();
        if (!backupData) {
            this.toastMessage('No backup available to download', false);
            return;
        }

        const filename = `wwc-backup-${this.wallet.address.slice(0, 8)}.json`;
        const blob = new Blob([backupData], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);

        this.toastMessage('Backup file downloaded');
        this.log('Downloaded encrypted backup file');
    }

    uploadBackup() {
        this.backupFileInput.value = '';
        this.backupFileInput.click();
    }

    handleBackupFileUpload(event) {
        const file = event.target.files[0];
        if (!file) {
            return;
        }

        const reader = new FileReader();
        reader.onload = () => {
            this.backupOutput.value = reader.result;
            this.toastMessage('Backup file loaded. Click Restore to continue.');
            this.log('Encrypted backup file loaded');
        };

        reader.onerror = () => {
            this.toastMessage('Failed to read backup file', false);
        };

        reader.readAsText(file);
    }

    async deriveKey(password, salt) {
        const encoder = new TextEncoder();
        const baseKey = await crypto.subtle.importKey(
            'raw',
            encoder.encode(password),
            { name: 'PBKDF2' },
            false,
            ['deriveKey']
        );
        return crypto.subtle.deriveKey(
            {
                name: 'PBKDF2',
                salt,
                iterations: 200000,
                hash: 'SHA-256'
            },
            baseKey,
            { name: 'AES-GCM', length: 256 },
            false,
            ['encrypt', 'decrypt']
        );
    }

    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }

    base64ToArrayBuffer(base64) {
        const binary = atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return bytes.buffer;
    }

    hexToBytes(hex) {
        const bytes = [];
        for (let c = 0; c < hex.length; c += 2) {
            bytes.push(parseInt(hex.substr(c, 2), 16));
        }
        return bytes;
    }

    renderWallet() {
        this.walletAddress.value = this.wallet.address;
        this.walletPrivateKey.value = this.wallet.privateKey;
    }

    async checkApi() {
        try {
            const response = await fetch(`${this.apiUrl}/health`);
            if (!response.ok) throw new Error('API not ready');
            this.apiStatus.textContent = 'Online';
            this.apiStatus.style.color = '#34d399';
            this.log('Connected to API');
            return true;
        } catch (error) {
            this.apiStatus.textContent = 'Offline';
            this.apiStatus.style.color = '#f97316';
            this.log('Unable to reach API');
            return false;
        }
    }

    async refresh() {
        if (!(await this.checkApi())) return;
        await Promise.all([
            this.refreshBalance(),
            this.refreshHistory()
        ]);
    }

    async refreshBalance() {
        try {
            const address = this.wallet.address;
            const response = await fetch(`${this.apiUrl}/utxo/${address}`);
            if (!response.ok) throw new Error('Balance fetch failed');

            const data = await response.json();
            const balance = Number(data.balance || 0).toFixed(2);
            this.balanceValue.textContent = `${balance} WWC`;
            this.log(`Balance updated: ${balance}`);
        } catch (error) {
            console.error(error);
            this.balanceValue.textContent = 'Error';
            this.toastMessage('Failed to refresh balance', false);
        }
    }

    async refreshHistory() {
        try {
            const address = this.wallet.address;
            const response = await fetch(`${this.apiUrl}/history/${address}`);
            if (!response.ok) throw new Error('History fetch failed');

            const data = await response.json();
            const transactions = (data.transactions || []).slice(-10).reverse();

            this.renderHistory(transactions);
            this.log('Transaction history updated');
        } catch (error) {
            console.error(error);
            this.historyList.innerHTML = '<div class="empty-state">Unable to load history.</div>';
            this.toastMessage('Failed to refresh history', false);
        }
    }

    calculateTransactionAmount(tx, address) {
        const received = tx.outputs
            .filter(out => out.address === address)
            .reduce((sum, out) => sum + Number(out.amount || 0), 0);
        const sent = tx.inputs
            .filter(inp => inp.address === address)
            .reduce((sum, inp) => sum + Number(inp.amount || 0), 0);
        return (received - sent).toFixed(2);
    }

    renderHistory(transactions) {
        if (!transactions.length) {
            this.historyList.innerHTML = '<div class="empty-state">No recent transactions.</div>';
            return;
        }

        this.historyList.innerHTML = transactions.map(tx => `
            <div class="history-item">
                <strong>${tx.type} ${tx.amount} WWC</strong>
                <span>Counterparty: ${tx.counterparty || 'N/A'}</span>
                <span>${new Date(tx.timestamp * 1000).toLocaleString()}</span>
                <span>ID: ${tx.id.slice(0, 20)}...</span>
            </div>
        `).join('');
    }

    async sendTransaction() {
        try {
            const recipient = this.recipientInput.value.trim();
            const amount = parseFloat(this.amountInput.value);

            if (!recipient || !amount || amount <= 0) {
                this.toastMessage('Enter a valid recipient and amount', false);
                return;
            }

            const utxoResponse = await fetch(`${this.apiUrl}/utxo/${this.wallet.address}`);
            if (!utxoResponse.ok) throw new Error('UTXO lookup failed');

            const utxoData = await utxoResponse.json();
            const utxos = utxoData.utxos || [];

            const { selected, total } = this.selectUtxos(utxos, amount);
            if (!selected.length) {
                this.toastMessage('Insufficient balance', false);
                return;
            }

            const outputs = [{ address: recipient, amount }];
            if (total > amount) {
                outputs.push({ address: this.wallet.address, amount: Number((total - amount).toFixed(8)) });
            }

            const txData = { inputs: selected, outputs };
            const signature = await this.signTransaction(txData);
            const payload = {
                ...txData,
                signature,
                public_key: this.wallet.publicKey
            };

            const response = await fetch(`${this.apiUrl}/tx`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const body = await response.json();
            if (!response.ok) {
                throw new Error(body.error || 'Transaction failed');
            }

            this.recipientInput.value = '';
            this.amountInput.value = '';
            this.toastMessage('Transaction broadcasted successfully');
            this.log(`Transaction sent: ${body.txid}`);
            await this.refresh();
        } catch (error) {
            console.error(error);
            this.toastMessage(error.message || 'Send failed', false);
            this.log(`Send failed: ${error.message}`);
        }
    }

    selectUtxos(utxos, amount) {
        let total = 0;
        const selected = [];
        for (const utxo of utxos) {
            selected.push({ txid: utxo.txid, index: utxo.vout, amount: Number(utxo.amount) });
            total += Number(utxo.amount);
            if (total >= amount) break;
        }
        return { selected, total };
    }

    signTransaction(txData) {
        const message = this.canonicalize(txData);
        const hashHex = sha256(message);
        const sig = this.wallet.keyPair.sign(hashHex, 'hex', { canonical: true });
        return sig.toDER('hex');
    }

    canonicalize(value) {
        if (Array.isArray(value)) {
            return '[' + value.map(item => this.canonicalize(item)).join(',') + ']';
        }

        if (value && typeof value === 'object') {
            const keys = Object.keys(value).sort();
            return '{' + keys.map(key => `${JSON.stringify(key)}:${this.canonicalize(value[key])}`).join(',') + '}';
        }

        return JSON.stringify(value);
    }

    sha256(message) {
        return sha256(message);
    }

    computeAddress(publicKeyHex) {
        return sha256(this.hexToBytes(publicKeyHex));
    }

    hexToBytes(hex) {
        const bytes = [];
        for (let c = 0; c < hex.length; c += 2) {
            bytes.push(parseInt(hex.substr(c, 2), 16));
        }
        return bytes;
    }
}

window.addEventListener('DOMContentLoaded', () => {
    window.wwcWallet = new WWCMobileWallet();
});