import { StorageService } from './StorageService';

export class TransactionService {
  private static instance: TransactionService;
  
  private constructor() {}
  
  static getInstance(): TransactionService {
    if (!TransactionService.instance) {
      TransactionService.instance = new TransactionService();
    }
    return TransactionService.instance;
  }
  
  static async getTransactionHistory(): Promise<any[]> {
    try {
      const history = await StorageService.getInstance().getItem('transaction_history');
      return history ? JSON.parse(history) : [];
    } catch (error) {
      console.error('Error getting transaction history:', error);
      return [];
    }
  }
  
  static async addTransaction(transaction: any): Promise<void> {
    try {
      const history = await this.getTransactionHistory();
      history.unshift(transaction);
      await StorageService.getInstance().setItem('transaction_history', JSON.stringify(history));
    } catch (error) {
      console.error('Error adding transaction:', error);
      throw error;
    }
  }
  
  static async getTransactionDetails(txHash: string): Promise<any | null> {
    try {
      const history = await this.getTransactionHistory();
      return history.find(tx => tx.hash === txHash) || null;
    } catch (error) {
      console.error('Error getting transaction details:', error);
      return null;
    }
  }
  
  static async updateTransactionStatus(txHash: string, status: string, confirmations?: number): Promise<void> {
    try {
      const history = await this.getTransactionHistory();
      const txIndex = history.findIndex(tx => tx.hash === txHash);
      
      if (txIndex !== -1) {
        history[txIndex].status = status;
        if (confirmations !== undefined) {
          history[txIndex].confirmations = confirmations;
        }
        await StorageService.getInstance().setItem('transaction_history', JSON.stringify(history));
      }
    } catch (error) {
      console.error('Error updating transaction status:', error);
      throw error;
    }
  }
  
  static async clearTransactionHistory(): Promise<void> {
    try {
      await StorageService.getInstance().removeItem('transaction_history');
    } catch (error) {
      console.error('Error clearing transaction history:', error);
      throw error;
    }
  }
  
  static async exportTransactions(): Promise<string> {
    try {
      const history = await this.getTransactionHistory();
      return JSON.stringify(history, null, 2);
    } catch (error) {
      console.error('Error exporting transactions:', error);
      throw error;
    }
  }
  
  static generateMockTransactions(): any[] {
    return [
      {
        hash: 'tx_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p',
        from: 'WWC:1A2b3c4d5e6f7c8b9a8e7d1234567890abcdef',
        to: 'WWC:9Z8y7x6w5v4u3t2s1r0q9p8o7n6m5l4k3j2i1h',
        value: '10.50000000',
        timestamp: new Date(Date.now() - 86400000).toISOString(),
        status: 'confirmed',
        confirmations: 12
      },
      {
        hash: 'tx_2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r',
        from: 'WWC:9Z8y7x6w5v4u3t2s1r0q9p8o7n6m5l4k3j2i1h',
        to: 'WWC:1A2b3c4d5e6f7c8b9a8e7d1234567890abcdef',
        value: '5.25000000',
        timestamp: new Date(Date.now() - 172800000).toISOString(),
        status: 'confirmed',
        confirmations: 24
      },
      {
        hash: 'tx_3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s',
        from: 'WWC:1A2b3c4d5e6f7c8b9a8e7d1234567890abcdef',
        to: 'WWC:8X7w6v5u4t3s2r1q0p9o8n7m6l5k4j3i2h1g',
        value: '2.75000000',
        timestamp: new Date(Date.now() - 259200000).toISOString(),
        status: 'confirmed',
        confirmations: 36
      }
    ];
  }
}
