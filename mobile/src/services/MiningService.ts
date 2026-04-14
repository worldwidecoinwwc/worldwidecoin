import { StorageService } from './StorageService';
import { NotificationService } from './NotificationService';

export class MiningService {
  private static instance: MiningService;
  private static isMiningActive = false;
  
  private constructor() {}
  
  static getInstance(): MiningService {
    if (!MiningService.instance) {
      MiningService.instance = new MiningService();
    }
    return MiningService.instance;
  }
  
  static async getMiningStatus(): Promise<any> {
    try {
      const status = await StorageService.getInstance().getItem('mining_status');
      const isMining = await StorageService.getInstance().getItem('mining_active');
      
      return {
        isMining: isMining === 'true',
        hashRate: this.generateMockHashRate(),
        blocksFound: Math.floor(Math.random() * 10),
        totalEarnings: `${(Math.random() * 100).toFixed(8)} WWC`,
        uptime: this.calculateUptime(),
        difficulty: '12345',
        poolConnections: 3,
        activeWorkers: 1
      };
    } catch (error) {
      console.error('Error getting mining status:', error);
      return {
        isMining: false,
        hashRate: '0 H/s',
        blocksFound: 0,
        totalEarnings: '0.00000000 WWC',
        uptime: '0h 0m 0s',
        difficulty: '0',
        poolConnections: 0,
        activeWorkers: 0
      };
    }
  }
  
  static async startMining(): Promise<void> {
    try {
      MiningService.isMiningActive = true;
      await StorageService.getInstance().setItem('mining_active', 'true');
      await StorageService.getInstance().setItem('mining_start_time', new Date().toISOString());
      
      await NotificationService.showNotification(
        'Mining Started',
        'WorldWideCoin mining has been started successfully!'
      );
      
      // Simulate mining process
      this.simulateMining();
    } catch (error) {
      console.error('Error starting mining:', error);
      throw error;
    }
  }
  
  static async stopMining(): Promise<void> {
    try {
      MiningService.isMiningActive = false;
      await StorageService.getInstance().setItem('mining_active', 'false');
      
      await NotificationService.showNotification(
        'Mining Stopped',
        'WorldWideCoin mining has been stopped.'
      );
    } catch (error) {
      console.error('Error stopping mining:', error);
      throw error;
    }
  }
  
  static async setAutoMining(enabled: boolean): Promise<void> {
    try {
      await StorageService.getInstance().setItem('auto_mining', enabled.toString());
    } catch (error) {
      console.error('Error setting auto mining:', error);
      throw error;
    }
  }
  
  static async setNotifications(enabled: boolean): Promise<void> {
    try {
      await StorageService.getInstance().setItem('mining_notifications', enabled.toString());
    } catch (error) {
      console.error('Error setting notifications:', error);
      throw error;
    }
  }
  
  static async getMiningSettings(): Promise<any> {
    try {
      const autoMining = await StorageService.getInstance().getItem('auto_mining');
      const notifications = await StorageService.getInstance().getItem('mining_notifications');
      
      return {
        autoMining: autoMining === 'true',
        notifications: notifications === 'true',
        maxWorkers: 4,
        cpuUsage: 75,
        memoryLimit: 2048
      };
    } catch (error) {
      console.error('Error getting mining settings:', error);
      return {
        autoMining: false,
        notifications: true,
        maxWorkers: 4,
        cpuUsage: 75,
        memoryLimit: 2048
      };
    }
  }
  
  private static generateMockHashRate(): string {
    const hashRates = ['1.2 MH/s', '2.5 MH/s', '3.8 MH/s', '4.1 MH/s', '5.6 MH/s'];
    return hashRates[Math.floor(Math.random() * hashRates.length)];
  }
  
  private static calculateUptime(): string {
    const startTime = new Date().getTime() - Math.random() * 86400000; // Random time within last 24h
    const uptime = new Date().getTime() - startTime;
    
    const hours = Math.floor(uptime / 3600000);
    const minutes = Math.floor((uptime % 3600000) / 60000);
    const seconds = Math.floor((uptime % 60000) / 1000);
    
    return `${hours}h ${minutes}m ${seconds}s`;
  }
  
  private static simulateMining(): void {
    if (!MiningService.isMiningActive) return;
    
    // Simulate finding a block occasionally
    if (Math.random() < 0.01) { // 1% chance per check
      this.simulateBlockFound();
    }
    
    // Continue simulation
    setTimeout(() => this.simulateMining(), 5000);
  }
  
  private static async simulateBlockFound(): Promise<void> {
    try {
      const blocksFound = await StorageService.getInstance().getItem('blocks_found');
      const newCount = blocksFound ? parseInt(blocksFound) + 1 : 1;
      await StorageService.getInstance().setItem('blocks_found', newCount.toString());
      
      await NotificationService.showNotification(
        'Block Found!',
        `Congratulations! Block #${newCount} has been found!`
      );
    } catch (error) {
      console.error('Error simulating block found:', error);
    }
  }
}
