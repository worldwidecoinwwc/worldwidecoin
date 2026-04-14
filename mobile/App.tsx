import React, { useEffect, useState } from 'react';
import {
  SafeAreaView,
  StatusBar,
  StyleSheet,
  View,
  Alert,
  Platform,
} from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Provider as PaperProvider } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialIcons';

// Import screens
import WalletScreen from './src/screens/WalletScreen';
import ExplorerScreen from './src/screens/ExplorerScreen';
import MiningScreen from './src/screens/MiningScreen';
import SettingsScreen from './src/screens/SettingsScreen';

// Import services
import { BiometricService } from './src/services/BiometricService';
import { StorageService } from './src/services/StorageService';
import { NotificationService } from './src/services/NotificationService';

// Import theme
import { AppTheme } from './src/theme/AppTheme';

const Tab = createBottomTabNavigator();

const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      // Initialize services
      await StorageService.initialize();
      await NotificationService.initialize();
      
      // Check biometric authentication
      const hasBiometrics = await BiometricService.isAvailable();
      if (hasBiometrics) {
        const isAuthenticated = await BiometricService.authenticate(
          'Authenticate to access WorldWideCoin Wallet'
        );
        setIsAuthenticated(isAuthenticated);
      } else {
        // Fallback to PIN authentication
        setIsAuthenticated(true); // For demo, implement PIN logic
      }
    } catch (error) {
      console.error('App initialization error:', error);
      Alert.alert('Error', 'Failed to initialize app. Please restart.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <SafeAreaView style={styles.loadingContainer}>
        <StatusBar barStyle="light-content" backgroundColor="#F39C12" />
        <View style={styles.loadingContent}>
          <Icon name="account_balance" size={80} color="#F39C12" />
          <Icon name="hourglass-empty" size={40} color="#666" />
        </View>
      </SafeAreaView>
    );
  }

  if (!isAuthenticated) {
    return (
      <SafeAreaView style={styles.loadingContainer}>
        <StatusBar barStyle="light-content" backgroundColor="#F39C12" />
        <View style={styles.loadingContent}>
          <Icon name="security" size={80} color="#F39C12" />
          <Icon name="lock" size={40} color="#666" />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <PaperProvider theme={AppTheme}>
      <NavigationContainer>
        <SafeAreaView style={styles.container}>
          <StatusBar barStyle="light-content" backgroundColor="#F39C12" />
          <Tab.Navigator
            screenOptions={({ route }) => ({
              tabBarIcon: ({ focused, color, size }) => {
                let iconName: string;

                switch (route.name) {
                  case 'Wallet':
                    iconName = 'account_balance_wallet';
                    break;
                  case 'Explorer':
                    iconName = 'explore';
                    break;
                  case 'Mining':
                    iconName = 'trending_up';
                    break;
                  case 'Settings':
                    iconName = 'settings';
                    break;
                  default:
                    iconName = 'help';
                }

                return <Icon name={iconName} size={size} color={color} />;
              },
              tabBarActiveTintColor: '#F39C12',
              tabBarInactiveTintColor: 'gray',
              headerStyle: {
                backgroundColor: '#F39C12',
              },
              headerTintColor: '#fff',
              headerTitleStyle: {
                fontWeight: 'bold',
              },
            })}
          >
            <Tab.Screen
              name="Wallet"
              component={WalletScreen}
              options={{ title: 'WorldWideCoin' }}
            />
            <Tab.Screen
              name="Explorer"
              component={ExplorerScreen}
              options={{ title: 'Blockchain' }}
            />
            <Tab.Screen
              name="Mining"
              component={MiningScreen}
              options={{ title: 'Mining' }}
            />
            <Tab.Screen
              name="Settings"
              component={SettingsScreen}
              options={{ title: 'Settings' }}
            />
          </Tab.Navigator>
        </SafeAreaView>
      </NavigationContainer>
    </PaperProvider>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingContent: {
    justifyContent: 'center',
    alignItems: 'center',
    gap: 20,
  },
});

export default App;
