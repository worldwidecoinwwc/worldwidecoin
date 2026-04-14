import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  RefreshControl,
  Alert,
} from 'react-native';
import {
  Card,
  Text,
  Button,
  Surface,
  Divider,
  Switch,
  ProgressBar,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialIcons';

// Import services
import { MiningService } from '../services/MiningService';

const MiningScreen: React.FC = () => {
  const [miningStatus, setMiningStatus] = useState({
    isMining: false,
    hashRate: '0 H/s',
    blocksFound: 0,
    totalEarnings: '0.00000000 WWC',
    uptime: '0h 0m 0s',
    difficulty: '0',
    poolConnections: 0,
    activeWorkers: 0
  });
  const [refreshing, setRefreshing] = useState(false);
  const [autoMining, setAutoMining] = useState(false);
  const [notifications, setNotifications] = useState(true);

  useEffect(() => {
    loadMiningData();
    const interval = setInterval(loadMiningData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const loadMiningData = async () => {
    try {
      const data = await MiningService.getMiningStatus();
      setMiningStatus(data);
    } catch (error) {
      console.error('Error loading mining data:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadMiningData();
    setRefreshing(false);
  };

  const toggleMining = async () => {
    try {
      if (miningStatus.isMining) {
        await MiningService.stopMining();
        Alert.alert('Mining Stopped', 'WorldWideCoin mining has been stopped.');
      } else {
        await MiningService.startMining();
        Alert.alert('Mining Started', 'WorldWideCoin mining has been started.');
      }
      await loadMiningData();
    } catch (error) {
      console.error('Error toggling mining:', error);
      Alert.alert('Error', 'Failed to toggle mining status');
    }
  };

  const toggleAutoMining = () => {
    setAutoMining(!autoMining);
    MiningService.setAutoMining(!autoMining);
  };

  const toggleNotifications = () => {
    setNotifications(!notifications);
    MiningService.setNotifications(!notifications);
  };

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Mining Status Card */}
        <Card style={styles.statusCard}>
          <View style={styles.statusContent}>
            <View style={styles.statusHeader}>
              <Icon 
                name={miningStatus.isMining ? "trending_up" : "pause"} 
                size={32} 
                color={miningStatus.isMining ? "#4CAF50" : "#F44336"} 
              />
              <Text style={styles.statusTitle}>
                Mining Status: {miningStatus.isMining ? 'Active' : 'Stopped'}
              </Text>
            </View>
            
            <Button
              mode={miningStatus.isMining ? "outlined" : "contained"}
              onPress={toggleMining}
              style={styles.miningButton}
              icon={() => (
                <Icon 
                  name={miningStatus.isMining ? "stop" : "play_arrow"} 
                  size={20} 
                />
              )}
            >
              {miningStatus.isMining ? 'Stop Mining' : 'Start Mining'}
            </Button>
          </View>
        </Card>

        {/* Mining Statistics */}
        <Surface style={styles.statsContainer}>
          <Text style={styles.sectionTitle}>Mining Statistics</Text>
          
          <View style={styles.statsGrid}>
            <Card style={styles.statCard}>
              <View style={styles.statContent}>
                <Icon name="speed" size={24} color="#F39C12" />
                <Text style={styles.statValue}>{miningStatus.hashRate}</Text>
                <Text style={styles.statLabel}>Hash Rate</Text>
              </View>
            </Card>
            
            <Card style={styles.statCard}>
              <View style={styles.statContent}>
                <Icon name="block" size={24} color="#4CAF50" />
                <Text style={styles.statValue}>{miningStatus.blocksFound}</Text>
                <Text style={styles.statLabel}>Blocks Found</Text>
              </View>
            </Card>
            
            <Card style={styles.statCard}>
              <View style={styles.statContent}>
                <Icon name="account_balance_wallet" size={24} color="#3498DB" />
                <Text style={styles.statValue}>{miningStatus.totalEarnings}</Text>
                <Text style={styles.statLabel}>Total Earnings</Text>
              </View>
            </Card>
            
            <Card style={styles.statCard}>
              <View style={styles.statContent}>
                <Icon name="schedule" size={24} color="#9C27B0" />
                <Text style={styles.statValue}>{miningStatus.uptime}</Text>
                <Text style={styles.statLabel}>Uptime</Text>
              </View>
            </Card>
          </View>
        </Surface>

        {/* Mining Configuration */}
        <Surface style={styles.configContainer}>
          <Text style={styles.sectionTitle}>Mining Configuration</Text>
          
          <View style={styles.configItem}>
            <View style={styles.configContent}>
              <Text style={styles.configLabel}>Auto Mining</Text>
              <Text style={styles.configDescription}>
                Automatically start mining when app opens
              </Text>
            </View>
            <Switch
              value={autoMining}
              onValueChange={toggleAutoMining}
            />
          </View>
          
          <Divider style={styles.divider} />
          
          <View style={styles.configItem}>
            <View style={styles.configContent}>
              <Text style={styles.configLabel}>Mining Notifications</Text>
              <Text style={styles.configDescription}>
                Get notified when blocks are found
              </Text>
            </View>
            <Switch
              value={notifications}
              onValueChange={toggleNotifications}
            />
          </View>
          
          <Divider style={styles.divider} />
          
          <View style={styles.configItem}>
            <View style={styles.configContent}>
              <Text style={styles.configLabel}>Network Difficulty</Text>
              <Text style={styles.configValue}>{miningStatus.difficulty}</Text>
            </View>
          </View>
          
          <Divider style={styles.divider} />
          
          <View style={styles.configItem}>
            <View style={styles.configContent}>
              <Text style={styles.configLabel}>Pool Connections</Text>
              <Text style={styles.configValue}>{miningStatus.poolConnections}</Text>
            </View>
          </View>
          
          <Divider style={styles.divider} />
          
          <View style={styles.configItem}>
            <View style={styles.configContent}>
              <Text style={styles.configLabel}>Active Workers</Text>
              <Text style={styles.configValue}>{miningStatus.activeWorkers}</Text>
            </View>
          </View>
        </Surface>

        {/* Mining Performance */}
        <Surface style={styles.performanceContainer}>
          <Text style={styles.sectionTitle}>Performance Metrics</Text>
          
          <View style={styles.performanceItem}>
            <Text style={styles.performanceLabel}>CPU Usage</Text>
            <ProgressBar
              progress={0.75}
              color="#F39C12"
              style={styles.progressBar}
            />
            <Text style={styles.performanceValue}>75%</Text>
          </View>
          
          <View style={styles.performanceItem}>
            <Text style={styles.performanceLabel}>Memory Usage</Text>
            <ProgressBar
              progress={0.45}
              color="#3498DB"
              style={styles.progressBar}
            />
            <Text style={styles.performanceValue}>45%</Text>
          </View>
          
          <View style={styles.performanceItem}>
            <Text style={styles.performanceLabel}>Network Latency</Text>
            <ProgressBar
              progress={0.15}
              color="#4CAF50"
              style={styles.progressBar}
            />
            <Text style={styles.performanceValue}>15ms</Text>
          </View>
        </Surface>

        {/* Mining Actions */}
        <Surface style={styles.actionsContainer}>
          <Text style={styles.sectionTitle}>Mining Actions</Text>
          
          <View style={styles.actionButtons}>
            <Button
              mode="outlined"
              onPress={() => {/* TODO: View mining logs */}}
              style={styles.actionButton}
              icon={() => <Icon name="list" size={20} />}
            >
              View Logs
            </Button>
            
            <Button
              mode="outlined"
              onPress={() => {/* TODO: Configure mining settings */}}
              style={styles.actionButton}
              icon={() => <Icon name="settings" size={20} />}
            >
              Settings
            </Button>
            
            <Button
              mode="outlined"
              onPress={() => {/* TODO: View mining statistics */}}
              style={styles.actionButton}
              icon={() => <Icon name="bar-chart" size={20} />}
            >
              Statistics
            </Button>
          </View>
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
  statusCard: {
    margin: 16,
    backgroundColor: '#F39C12',
  },
  statusContent: {
    padding: 20,
  },
  statusHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  statusTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    marginLeft: 12,
  },
  miningButton: {
    backgroundColor: '#fff',
  },
  statsContainer: {
    margin: 16,
    padding: 16,
    borderRadius: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  statCard: {
    flex: 1,
    minWidth: '45%',
  },
  statContent: {
    padding: 16,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 16,
    fontWeight: 'bold',
    marginTop: 8,
    textAlign: 'center',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
    textAlign: 'center',
  },
  configContainer: {
    margin: 16,
    padding: 16,
    borderRadius: 8,
  },
  configItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
  },
  configContent: {
    flex: 1,
  },
  configLabel: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  configDescription: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  configValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#F39C12',
  },
  divider: {
    marginVertical: 8,
  },
  performanceContainer: {
    margin: 16,
    padding: 16,
    borderRadius: 8,
  },
  performanceItem: {
    marginBottom: 16,
  },
  performanceLabel: {
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  progressBar: {
    height: 8,
    borderRadius: 4,
    marginBottom: 4,
  },
  performanceValue: {
    fontSize: 12,
    color: '#666',
    textAlign: 'right',
  },
  actionsContainer: {
    margin: 16,
    padding: 16,
    borderRadius: 8,
    marginBottom: 80,
  },
  actionButtons: {
    gap: 12,
  },
  actionButton: {
    flex: 1,
  },
});

export default MiningScreen;
