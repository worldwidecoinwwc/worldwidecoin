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
  Searchbar,
  Surface,
  Divider,
  Chip,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialIcons';

// Import services
import { BlockchainService } from '../services/BlockchainService';

const ExplorerScreen: React.FC = () => {
  const [blocks, setBlocks] = useState<any[]>([]);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [networkStats, setNetworkStats] = useState<any>({});
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'blocks' | 'transactions' | 'stats'>('blocks');

  useEffect(() => {
    loadBlockchainData();
    const interval = setInterval(loadBlockchainData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadBlockchainData = async () => {
    try {
      const [latestBlocks, latestTxs, stats] = await Promise.all([
        BlockchainService.getLatestBlocks(),
        BlockchainService.getLatestTransactions(),
        BlockchainService.getNetworkStats(),
      ]);
      
      setBlocks(latestBlocks);
      setTransactions(latestTxs);
      setNetworkStats(stats);
    } catch (error) {
      console.error('Error loading blockchain data:', error);
      Alert.alert('Error', 'Failed to load blockchain data');
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadBlockchainData();
    setRefreshing(false);
  };

  const renderBlockItem = (block: any) => (
    <Card style={styles.itemCard} key={block.hash}>
      <View style={styles.itemContent}>
        <View style={styles.itemHeader}>
          <Icon name="block" size={24} color="#F39C12" />
          <Text style={styles.itemTitle}>Block #{block.height}</Text>
        </View>
        <Text style={styles.itemSubtext}>
          Hash: {block.hash.substring(0, 16)}...
        </Text>
        <Text style={styles.itemSubtext}>
          Time: {new Date(block.timestamp).toLocaleString()}
        </Text>
        <Text style={styles.itemSubtext}>
          Transactions: {block.transactionCount}
        </Text>
        <View style={styles.itemActions}>
          <Chip icon={() => <Icon name="visibility" size={16} />}>
            View Details
          </Chip>
        </View>
      </View>
    </Card>
  );

  const renderTransactionItem = (tx: any) => (
    <Card style={styles.itemCard} key={tx.hash}>
      <View style={styles.itemContent}>
        <View style={styles.itemHeader}>
          <Icon name="swap_horiz" size={24} color="#3498DB" />
          <Text style={styles.itemTitle}>Transaction</Text>
        </View>
        <Text style={styles.itemSubtext}>
          Hash: {tx.hash.substring(0, 16)}...
        </Text>
        <Text style={styles.itemSubtext}>
          From: {tx.from.substring(0, 16)}...
        </Text>
        <Text style={styles.itemSubtext}>
          To: {tx.to.substring(0, 16)}...
        </Text>
        <Text style={styles.itemSubtext}>
          Amount: {tx.value} WWC
        </Text>
        <View style={styles.itemActions}>
          <Chip icon={() => <Icon name="visibility" size={16} />}>
            View Details
          </Chip>
        </View>
      </View>
    </Card>
  );

  const renderNetworkStats = () => (
    <View style={styles.statsContainer}>
      <Card style={styles.statCard}>
        <View style={styles.statContent}>
          <Icon name="trending_up" size={32} color="#4CAF50" />
          <Text style={styles.statValue}>{networkStats.hashRate}</Text>
          <Text style={styles.statLabel}>Network Hash Rate</Text>
        </View>
      </Card>
      
      <Card style={styles.statCard}>
        <View style={styles.statContent}>
          <Icon name="account_balance" size={32} color="#F39C12" />
          <Text style={styles.statValue}>{networkStats.totalSupply}</Text>
          <Text style={styles.statLabel}>Total Supply</Text>
        </View>
      </Card>
      
      <Card style={styles.statCard}>
        <View style={styles.statContent}>
          <Icon name="memory" size={32} color="#3498DB" />
          <Text style={styles.statValue}>{networkStats.difficulty}</Text>
          <Text style={styles.statLabel}>Mining Difficulty</Text>
        </View>
      </Card>
      
      <Card style={styles.statCard}>
        <View style={styles.statContent}>
          <Icon name="people" size={32} color="#9C27B0" />
          <Text style={styles.statValue}>{networkStats.activeMiners}</Text>
          <Text style={styles.statLabel}>Active Miners</Text>
        </View>
      </Card>
    </View>
  );

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Search Bar */}
        <View style={styles.searchContainer}>
          <Searchbar
            placeholder="Search blocks, transactions, addresses..."
            onChangeText={setSearchQuery}
            value={searchQuery}
            style={styles.searchBar}
          />
        </View>

        {/* Tab Navigation */}
        <View style={styles.tabContainer}>
          <Button
            mode={activeTab === 'blocks' ? 'contained' : 'outlined'}
            onPress={() => setActiveTab('blocks')}
            style={styles.tabButton}
          >
            Blocks
          </Button>
          <Button
            mode={activeTab === 'transactions' ? 'contained' : 'outlined'}
            onPress={() => setActiveTab('transactions')}
            style={styles.tabButton}
          >
            Transactions
          </Button>
          <Button
            mode={activeTab === 'stats' ? 'contained' : 'outlined'}
            onPress={() => setActiveTab('stats')}
            style={styles.tabButton}
          >
            Network
          </Button>
        </View>

        {/* Content based on active tab */}
        {activeTab === 'blocks' && (
          <View style={styles.contentContainer}>
            <Text style={styles.sectionTitle}>Latest Blocks</Text>
            {blocks.length === 0 ? (
              <View style={styles.emptyState}>
                <Icon name="block" size={48} color="#ccc" />
                <Text style={styles.emptyText}>No blocks available</Text>
              </View>
            ) : (
              blocks.map(renderBlockItem)
            )}
          </View>
        )}

        {activeTab === 'transactions' && (
          <View style={styles.contentContainer}>
            <Text style={styles.sectionTitle}>Latest Transactions</Text>
            {transactions.length === 0 ? (
              <View style={styles.emptyState}>
                <Icon name="swap_horiz" size={48} color="#ccc" />
                <Text style={styles.emptyText}>No transactions available</Text>
              </View>
            ) : (
              transactions.map(renderTransactionItem)
            )}
          </View>
        )}

        {activeTab === 'stats' && (
          <View style={styles.contentContainer}>
            <Text style={styles.sectionTitle}>Network Statistics</Text>
            {renderNetworkStats()}
          </View>
        )}
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
  searchContainer: {
    padding: 16,
  },
  searchBar: {
    elevation: 2,
  },
  tabContainer: {
    flexDirection: 'row',
    padding: 16,
    gap: 8,
  },
  tabButton: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  itemCard: {
    marginBottom: 12,
  },
  itemContent: {
    padding: 16,
  },
  itemHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  itemTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 12,
  },
  itemSubtext: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  itemActions: {
    marginTop: 12,
  },
  statsContainer: {
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
    fontSize: 20,
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
  emptyState: {
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: 'bold',
    marginTop: 16,
    color: '#666',
  },
});

export default ExplorerScreen;
