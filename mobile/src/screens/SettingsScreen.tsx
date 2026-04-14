import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  Alert,
  Linking,
} from 'react-native';
import {
  Card,
  Text,
  Button,
  Switch,
  Surface,
  Divider,
  List,
  RadioButton,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialIcons';

// Import services
import { BiometricService } from '../services/BiometricService';
import { StorageService } from '../services/StorageService';
import { WalletService } from '../services/WalletService';
import { NotificationService } from '../services/NotificationService';

const SettingsScreen: React.FC = () => {
  const [biometricEnabled, setBiometricEnabled] = useState(false);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
  const [autoBackup, setAutoBackup] = useState(true);
  const [selectedCurrency, setSelectedCurrency] = useState('WWC');
  const [selectedLanguage, setSelectedLanguage] = useState('english');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const hasBiometrics = await BiometricService.isAvailable();
      setBiometricEnabled(hasBiometrics);
      
      const notifications = await StorageService.getInstance().getItem('notifications_enabled');
      setNotificationsEnabled(notifications !== 'false');
      
      const darkModeSetting = await StorageService.getInstance().getItem('dark_mode');
      setDarkMode(darkModeSetting === 'true');
      
      const backupSetting = await StorageService.getInstance().getItem('auto_backup');
      setAutoBackup(backupSetting !== 'false');
      
      const currency = await StorageService.getInstance().getItem('selected_currency');
      setSelectedCurrency(currency || 'WWC');
      
      const language = await StorageService.getInstance().getItem('selected_language');
      setSelectedLanguage(language || 'english');
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  };

  const toggleBiometric = async () => {
    try {
      if (!biometricEnabled) {
        const authenticated = await BiometricService.authenticate(
          'Enable biometric authentication'
        );
        if (authenticated) {
          setBiometricEnabled(true);
          await StorageService.getInstance().setItem('biometric_enabled', 'true');
          Alert.alert('Success', 'Biometric authentication enabled!');
        }
      } else {
        setBiometricEnabled(false);
        await StorageService.getInstance().setItem('biometric_enabled', 'false');
        Alert.alert('Success', 'Biometric authentication disabled!');
      }
    } catch (error) {
      console.error('Error toggling biometric:', error);
      Alert.alert('Error', 'Failed to toggle biometric authentication');
    }
  };

  const toggleNotifications = async () => {
    try {
      const newValue = !notificationsEnabled;
      setNotificationsEnabled(newValue);
      await StorageService.getInstance().setItem('notifications_enabled', newValue.toString());
    } catch (error) {
      console.error('Error toggling notifications:', error);
    }
  };

  const toggleDarkMode = async () => {
    try {
      const newValue = !darkMode;
      setDarkMode(newValue);
      await StorageService.getInstance().setItem('dark_mode', newValue.toString());
      Alert.alert('Theme Changed', `Dark mode ${newValue ? 'enabled' : 'disabled'}. Restart app to apply changes.`);
    } catch (error) {
      console.error('Error toggling dark mode:', error);
    }
  };

  const toggleAutoBackup = async () => {
    try {
      const newValue = !autoBackup;
      setAutoBackup(newValue);
      await StorageService.getInstance().setItem('auto_backup', newValue.toString());
    } catch (error) {
      console.error('Error toggling auto backup:', error);
    }
  };

  const handleBackupWallet = async () => {
    try {
      const backup = await WalletService.backupWallet();
      await StorageService.getInstance().setItem('wallet_backup', backup);
      Alert.alert('Backup Created', 'Your wallet has been backed up successfully!');
    } catch (error) {
      console.error('Error backing up wallet:', error);
      Alert.alert('Error', 'Failed to backup wallet');
    }
  };

  const handleRestoreWallet = async () => {
    Alert.alert(
      'Restore Wallet',
      'This will replace your current wallet. Are you sure?',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Restore', onPress: async () => {
          try {
            const backup = await StorageService.getInstance().getItem('wallet_backup');
            if (backup) {
              const success = await WalletService.restoreWallet(backup);
              if (success) {
                Alert.alert('Success', 'Wallet restored successfully!');
              } else {
                Alert.alert('Error', 'Failed to restore wallet');
              }
            } else {
              Alert.alert('Error', 'No backup found');
            }
          } catch (error) {
            console.error('Error restoring wallet:', error);
            Alert.alert('Error', 'Failed to restore wallet');
          }
        }}
      ]
    );
  };

  const handleClearData = () => {
    Alert.alert(
      'Clear All Data',
      'This will delete all your wallet data and settings. This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Clear Data', onPress: async () => {
          try {
            await StorageService.getInstance().clear();
            Alert.alert('Success', 'All data has been cleared. Please restart the app.');
          } catch (error) {
            console.error('Error clearing data:', error);
            Alert.alert('Error', 'Failed to clear data');
          }
        }}
      ]
    );
  };

  const openWebsite = () => {
    Linking.openURL('https://worldwidecoinwwc.github.io/worldwidecoin/');
  };

  const openGitHub = () => {
    Linking.openURL('https://github.com/worldwidecoinwwc/worldwidecoin');
  };

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView}>
        {/* Security Settings */}
        <Surface style={styles.section}>
          <Text style={styles.sectionTitle}>Security</Text>
          
          <List.Item
            title="Biometric Authentication"
            description="Use fingerprint or face recognition"
            left={(props) => <List.Icon {...props} icon="fingerprint" />}
            right={() => (
              <Switch
                value={biometricEnabled}
                onValueChange={toggleBiometric}
              />
            )}
          />
          
          <Divider />
          
          <List.Item
            title="Change PIN"
            description="Update your security PIN"
            left={(props) => <List.Icon {...props} icon="lock" />}
            onPress={() => Alert.alert('Coming Soon', 'PIN management will be available soon.')}
          />
          
          <Divider />
          
          <List.Item
            title="Two-Factor Authentication"
            description="Add extra security layer"
            left={(props) => <List.Icon {...props} icon="security" />}
            onPress={() => Alert.alert('Coming Soon', '2FA will be available soon.')}
          />
        </Surface>

        {/* Wallet Settings */}
        <Surface style={styles.section}>
          <Text style={styles.sectionTitle}>Wallet</Text>
          
          <List.Item
            title="Backup Wallet"
            description="Create a backup of your wallet"
            left={(props) => <List.Icon {...props} icon="backup" />}
            onPress={handleBackupWallet}
          />
          
          <Divider />
          
          <List.Item
            title="Restore Wallet"
            description="Restore from backup"
            left={(props) => <List.Icon {...props} icon="restore" />}
            onPress={handleRestoreWallet}
          />
          
          <Divider />
          
          <List.Item
            title="Auto Backup"
            description="Automatically backup wallet data"
            left={(props) => <List.Icon {...props} icon="schedule" />}
            right={() => (
              <Switch
                value={autoBackup}
                onValueChange={toggleAutoBackup}
              />
            )}
          />
        </Surface>

        {/* App Settings */}
        <Surface style={styles.section}>
          <Text style={styles.sectionTitle}>App Settings</Text>
          
          <List.Item
            title="Push Notifications"
            description="Receive transaction and mining alerts"
            left={(props) => <List.Icon {...props} icon="notifications" />}
            right={() => (
              <Switch
                value={notificationsEnabled}
                onValueChange={toggleNotifications}
              />
            )}
          />
          
          <Divider />
          
          <List.Item
            title="Dark Mode"
            description="Use dark theme"
            left={(props) => <List.Icon {...props} icon="dark-mode" />}
            right={() => (
              <Switch
                value={darkMode}
                onValueChange={toggleDarkMode}
              />
            )}
          />
          
          <Divider />
          
          <List.Item
            title="Display Currency"
            description="Choose your preferred currency"
            left={(props) => <List.Icon {...props} icon="currency-exchange" />}
            right={() => (
              <RadioButton.Group
                onValueChange={setSelectedCurrency}
                value={selectedCurrency}
              >
                <RadioButton value="WWC" />
              </RadioButton.Group>
            )}
          />
          
          <Divider />
          
          <List.Item
            title="Language"
            description="Choose app language"
            left={(props) => <List.Icon {...props} icon="translate" />}
            right={() => (
              <RadioButton.Group
                onValueChange={setSelectedLanguage}
                value={selectedLanguage}
              >
                <RadioButton value="english" />
              </RadioButton.Group>
            )}
          />
        </Surface>

        {/* About */}
        <Surface style={styles.section}>
          <Text style={styles.sectionTitle}>About</Text>
          
          <List.Item
            title="WorldWideCoin Website"
            description="Visit our official website"
            left={(props) => <List.Icon {...props} icon="language" />}
            onPress={openWebsite}
          />
          
          <Divider />
          
          <List.Item
            title="GitHub Repository"
            description="View source code and contribute"
            left={(props) => <List.Icon {...props} icon="code" />}
            onPress={openGitHub}
          />
          
          <Divider />
          
          <List.Item
            title="Version"
            description="1.0.0"
            left={(props) => <List.Icon {...props} icon="info" />}
          />
          
          <Divider />
          
          <List.Item
            title="Privacy Policy"
            description="Read our privacy policy"
            left={(props) => <List.Icon {...props} icon="privacy-tip" />}
            onPress={() => Linking.openURL('https://worldwidecoinwwc.github.io/worldwidecoin/privacy')}
          />
          
          <Divider />
          
          <List.Item
            title="Terms of Service"
            description="Read our terms of service"
            left={(props) => <List.Icon {...props} icon="description" />}
            onPress={() => Linking.openURL('https://worldwidecoinwwc.github.io/worldwidecoin/terms')}
          />
        </Surface>

        {/* Danger Zone */}
        <Surface style={styles.section}>
          <Text style={styles.sectionTitle}>Danger Zone</Text>
          
          <List.Item
            title="Clear All Data"
            description="Delete all wallet data and settings"
            left={(props) => <List.Icon {...props} icon="delete" />}
            onPress={handleClearData}
            titleStyle={{ color: '#F44336' }}
          />
        </Surface>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollView: {
    flex: 1,
  },
  section: {
    margin: 16,
    padding: 16,
    borderRadius: 8,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
});

export default SettingsScreen;
