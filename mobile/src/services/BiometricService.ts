import ReactNativeBiometrics from 'react-native-biometrics';

export class BiometricService {
  private static instance: BiometricService;
  
  private constructor() {}
  
  static getInstance(): BiometricService {
    if (!BiometricService.instance) {
      BiometricService.instance = new BiometricService();
    }
    return BiometricService.instance;
  }
  
  static async isAvailable(): Promise<boolean> {
    try {
      const { available, biometryType } = await ReactNativeBiometrics.isSensorAvailable();
      return available;
    } catch (error) {
      console.error('Biometric availability check error:', error);
      return false;
    }
  }
  
  static async authenticate(reason: string): Promise<boolean> {
    try {
      const { success } = await ReactNativeBiometrics.simplePrompt({
        promptMessage: reason,
        cancelButtonText: 'Cancel',
      });
      return success;
    } catch (error) {
      console.error('Biometric authentication error:', error);
      return false;
    }
  }
  
  static async createKeys(): Promise<boolean> {
    try {
      const { publicKey } = await ReactNativeBiometrics.createKeys();
      return !!publicKey;
    } catch (error) {
      console.error('Biometric key creation error:', error);
      return false;
    }
  }
  
  static async deleteKeys(): Promise<boolean> {
    try {
      await ReactNativeBiometrics.deleteKeys();
      return true;
    } catch (error) {
      console.error('Biometric key deletion error:', error);
      return false;
    }
  }
}
