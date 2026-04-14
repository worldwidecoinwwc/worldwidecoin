import axios from 'axios';

const API_BASE_URL = 'https://worldwidecoinwwc.github.io/worldwidecoin/api';

export class BlockchainService {
  private static instance: BlockchainService;
  
  private constructor() {}
  
  static getInstance(): BlockchainService {
    if (!BlockchainService.instance) {
      BlockchainService.instance = new BlockchainService();
    }
    return BlockchainService.instance;
  }
  
  static async getLatestBlocks(): Promise<any[]> {
    try {
      const response = await axios.get(`${API_BASE_URL}/blocks/latest`);
      return response.data.blocks || [];
    } catch (error) {
      console.error('Error fetching latest blocks:', error);
      return [];
    }
  }
  
  static async getLatestTransactions(): Promise<any[]> {
    try {
      const response = await axios.get(`${API_BASE_URL}/transactions/latest`);
      return response.data.transactions || [];
    } catch (error) {
      console.error('Error fetching latest transactions:', error);
      return [];
    }
  }
  
  static async getNetworkStats(): Promise<any> {
    try {
      const response = await axios.get(`${API_BASE_URL}/network/stats`);
      return response.data.stats || {
        hashRate: '0 H/s',
        totalSupply: '0 WWC',
        difficulty: '0',
        activeMiners: 0
      };
    } catch (error) {
      console.error('Error fetching network stats:', error);
      return {
        hashRate: '0 H/s',
        totalSupply: '0 WWC',
        difficulty: '0',
        activeMiners: 0
      };
    }
  }
  
  static async getBlockDetails(blockHash: string): Promise<any> {
    try {
      const response = await axios.get(`${API_BASE_URL}/blocks/${blockHash}`);
      return response.data.block || null;
    } catch (error) {
      console.error('Error fetching block details:', error);
      return null;
    }
  }
  
  static async getTransactionDetails(txHash: string): Promise<any> {
    try {
      const response = await axios.get(`${API_BASE_URL}/transactions/${txHash}`);
      return response.data.transaction || null;
    } catch (error) {
      console.error('Error fetching transaction details:', error);
      return null;
    }
  }
  
  static async searchAddress(address: string): Promise<any> {
    try {
      const response = await axios.get(`${API_BASE_URL}/address/${address}`);
      return response.data || null;
    } catch (error) {
      console.error('Error searching address:', error);
      return null;
    }
  }
}
