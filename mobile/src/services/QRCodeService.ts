import { Share, Clipboard } from 'react-native';
import QRCode from 'react-native-qrcode-svg';

export class QRCodeService {
  private static instance: QRCodeService;
  
  private constructor() {}
  
  static getInstance(): QRCodeService {
    if (!QRCodeService.instance) {
      QRCodeService.instance = new QRCodeService();
    }
    return QRCodeService.instance;
  }
  
  static async copyToClipboard(text: string): Promise<void> {
    try {
      await Clipboard.setString(text);
    } catch (error) {
      console.error('Error copying to clipboard:', error);
      throw error;
    }
  }
  
  static async getFromClipboard(): Promise<string> {
    try {
      return await Clipboard.getString();
    } catch (error) {
      console.error('Error getting from clipboard:', error);
      return '';
    }
  }
  
  static async shareText(text: string, title?: string): Promise<void> {
    try {
      await Share.share({
        message: text,
        title: title || 'Share WorldWideCoin',
      });
    } catch (error) {
      console.error('Error sharing text:', error);
      throw error;
    }
  }
  
  static generateQRCodeSVG(value: string, size: number = 200): string {
    try {
      // This would return the SVG data for the QR code
      // In a real implementation, you would use the QRCode library to generate this
      return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
        <rect width="100%" height="100%" fill="white"/>
        <text x="50%" y="50%" text-anchor="middle" dy=".3em" font-family="monospace" font-size="8">
          QR: ${value.substring(0, 20)}...
        </text>
      </svg>`;
    } catch (error) {
      console.error('Error generating QR code:', error);
      return '';
    }
  }
  
  static parseQRCodeData(data: string): any {
    try {
      // Parse different QR code formats
      if (data.startsWith('WWC:')) {
        return {
          type: 'address',
          address: data
        };
      }
      
      if (data.startsWith('wwc://')) {
        const url = new URL(data);
        return {
          type: 'payment_request',
          address: url.pathname.substring(1),
          amount: url.searchParams.get('amount'),
          label: url.searchParams.get('label'),
          message: url.searchParams.get('message')
        };
      }
      
      // Try to parse as JSON
      try {
        const parsed = JSON.parse(data);
        return parsed;
      } catch {
        // Return as raw text
        return {
          type: 'text',
          data: data
        };
      }
    } catch (error) {
      console.error('Error parsing QR code data:', error);
      return {
        type: 'error',
        data: data
      };
    }
  }
  
  static generatePaymentURI(address: string, amount?: string, label?: string, message?: string): string {
    try {
      let uri = `wwc://${address}`;
      const params = new URLSearchParams();
      
      if (amount) params.append('amount', amount);
      if (label) params.append('label', label);
      if (message) params.append('message', message);
      
      if (params.toString()) {
        uri += `?${params.toString()}`;
      }
      
      return uri;
    } catch (error) {
      console.error('Error generating payment URI:', error);
      return `wwc://${address}`;
    }
  }
}
