import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  RefreshControl,
  Alert,
  Share,
} from 'react-native';
import {
  Card,
  Button,
  Text,
  FAB,
  Portal,
  Modal,
  TextInput,
  Surface,
  Divider,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { StackNavigationProp } from '@react-navigation/stack';

// Import services
import { WalletService } from '../services/WalletService';
import { TransactionService } from '../services/TransactionService';
import { QRCodeService } from '../services/QRCodeService';

type RootStackParamList = {
  Wallet: undefined;
  Send: undefined;
  Receive: undefined;
  TransactionDetail: { txId: string };
};

type WalletScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Wallet'>;

interface Props {
  navigation: WalletScreenNavigationProp;
}

const WalletScreen: React.FC<Props> = ({ navigation }) => {
  const [balance, setBalance] = useState('0.00000000');
  const [transactions, setTransactions] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [showSendModal, setShowSendModal] = useState(false);
  const [showReceiveModal, setShowReceiveModal] = useState(false);
  const [sendAddress, setSendAddress] = useState('');
  const [sendAmount, setSendAmount] = useState('');
  const [walletAddress, setWalletAddress] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadWalletData();
    const interval = setInterval(loadWalletData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadWalletData = async () => {
    try {
      setIsLoading(true);
      const [walletBalance, txHistory, address] = await Promise.all([
        WalletService.getBalance(),
        TransactionService.getTransactionHistory(),
        WalletService.getAddress(),
      ]);
      
      setBalance(walletBalance);
      setTransactions(txHistory);
      setWalletAddress(address);
    } catch (error) {
      console.error('Error loading wallet data:', error);
      Alert.alert('Error', 'Failed to load wallet data');
    } finally {
      setIsLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadWalletData();
    setRefreshing(false);
  };

  const handleSend = async () => {
    if (!sendAddress || !sendAmount) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    try {
      const result = await WalletService.sendTransaction(sendAddress, sendAmount);
      Alert.alert('Success', 'Transaction sent successfully!');
      setShowSendModal(false);
      setSendAddress('');
      setSendAmount('');
      await loadWalletData();
    } catch (error) {
      console.error('Send error:', error);
      Alert.alert('Error', 'Failed to send transaction');
    }
  };

  const handleReceive = () => {
    setShowReceiveModal(true);
  };

  const shareAddress = async () => {
    try {
      await Share.share({
        message: `My WorldWideCoin address: ${walletAddress}`,
        title: 'Share WWC Address',
      });
    } catch (error) {
      console.error('Share error:', error);
    }
  };

  const copyAddress = async () => {
    try {
      await QRCodeService.copyToClipboard(walletAddress);
      Alert.alert('Success', 'Address copied to clipboard');
    } catch (error) {
      console.error('Copy error:', error);
    }
  };

  const renderTransactionItem = (transaction: any) => {
    const isReceive = transaction.to === walletAddress;
    const amount = isReceive ? `+${transaction.value}` : `-${transaction.value}`;
    
    return (
      <Card style={styles.transactionCard} key={transaction.hash}>
        <View style={styles.transactionItem}>
          <Icon
            name={isReceive ? 'arrow-downward' : 'arrow-upward'}
            size={24}
            color={isReceive ? '#4CAF50' : '#F44336'}
          />
          <View style={styles.transactionDetails}>
            <Text style={styles.transactionType}>
              {isReceive ? 'Received' : 'Sent'}
            </Text>
            <Text style={styles.transactionAmount}>
              {amount} WWC
            </Text>
            <Text style={styles.transactionTime}>
              {new Date(transaction.timestamp).toLocaleString()}
            </Text>
          </View>
          <Icon
            name="chevron-right"
            size={20}
            color="#666"
            onPress={() => navigation.navigate('TransactionDetail', { txId: transaction.hash })}
          />
        </View>
      </Card>
    );
  };

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Balance Card */}
        <Card style={styles.balanceCard}>
          <View style={styles.balanceContent}>
            <Text style={styles.balanceLabel}>WorldWideCoin Balance</Text>
            <Text style={styles.balanceAmount}>{balance} WWC</Text>
            <View style={styles.balanceActions}>
              <Button
                mode="outlined"
                onPress={() => navigation.navigate('Receive')}
                style={styles.balanceButton}
                icon={() => <Icon name="qr-code-scanner" size={20} />}
              >
                Receive
              </Button>
              <Button
                mode="contained"
                onPress={() => navigation.navigate('Send')}
                style={styles.balanceButton}
                icon={() => <Icon name="send" size={20} />}
              >
                Send
              </Button>
            </View>
          </View>
        </Card>

        {/* Quick Actions */}
        <Surface style={styles.quickActions}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          <View style={styles.quickActionButtons}>
            <Button
              mode="outlined"
              onPress={handleReceive}
              style={styles.quickButton}
              icon={() => <Icon name="qr-code" size={20} />}
            >
              Show QR
            </Button>
            <Button
              mode="outlined"
              onPress={copyAddress}
              style={styles.quickButton}
              icon={() => <Icon name="content-copy" size={20} />}
            >
              Copy Address
            </Button>
            <Button
              mode="outlined"
              onPress={shareAddress}
              style={styles.quickButton}
              icon={() => <Icon name="share" size={20} />}
            >
              Share
            </Button>
          </View>
        </Surface>

        {/* Transactions */}
        <Surface style={styles.transactionsContainer}>
          <Text style={styles.sectionTitle}>Recent Transactions</Text>
          {transactions.length === 0 ? (
            <View style={styles.emptyState}>
              <Icon name="receipt-long" size={48} color="#ccc" />
              <Text style={styles.emptyText}>No transactions yet</Text>
              <Text style={styles.emptySubtext}>
                Your transaction history will appear here
              </Text>
            </View>
          ) : (
            transactions.map(renderTransactionItem)
          )}
        </Surface>
      </ScrollView>

      {/* FAB for quick actions */}
      <FAB
        icon={() => <Icon name="add" size={24} />}
        style={styles.fab}
        onPress={() => setShowSendModal(true)}
      />

      {/* Send Modal */}
      <Portal>
        <Modal
          visible={showSendModal}
          onDismiss={() => setShowSendModal(false)}
          contentContainerStyle={styles.modal}
        >
          <Card>
            <Card.Title title="Send WorldWideCoin" />
            <Card.Content>
              <TextInput
                label="Recipient Address"
                value={sendAddress}
                onChangeText={setSendAddress}
                mode="outlined"
                style={styles.input}
                right={
                  <TextInput.Icon
                    icon="qr-code-scanner"
                    onPress={() => {/* TODO: QR scanner */}}
                  />
                }
              />
              <TextInput
                label="Amount (WWC)"
                value={sendAmount}
                onChangeText={setSendAmount}
                mode="outlined"
                style={styles.input}
                keyboardType="numeric"
              />
            </Card.Content>
            <Card.Actions>
              <Button onPress={() => setShowSendModal(false)}>Cancel</Button>
              <Button mode="contained" onPress={handleSend}>
                Send
              </Button>
            </Card.Actions>
          </Card>
        </Modal>
      </Portal>

      {/* Receive Modal */}
      <Portal>
        <Modal
          visible={showReceiveModal}
          onDismiss={() => setShowReceiveModal(false)}
          contentContainerStyle={styles.modal}
        >
          <Card>
            <Card.Title title="Receive WorldWideCoin" />
            <Card.Content>
              <Text style={styles.addressLabel}>Your Wallet Address:</Text>
              <Text style={styles.addressText}>{walletAddress}</Text>
              <View style={styles.receiveActions}>
                <Button
                  mode="outlined"
                  onPress={copyAddress}
                  icon={() => <Icon name="content-copy" size={20} />}
                >
                  Copy
                </Button>
                <Button
                  mode="contained"
                  onPress={shareAddress}
                  icon={() => <Icon name="share" size={20} />}
                >
                  Share
                </Button>
              </View>
            </Card.Content>
            <Card.Actions>
              <Button onPress={() => setShowReceiveModal(false)}>Close</Button>
            </Card.Actions>
          </Card>
        </Modal>
      </Portal>
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
  balanceCard: {
    margin: 16,
    backgroundColor: '#F39C12',
  },
  balanceContent: {
    padding: 20,
  },
  balanceLabel: {
    color: '#fff',
    fontSize: 16,
    marginBottom: 8,
  },
  balanceAmount: {
    color: '#fff',
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 20,
  },
  balanceActions: {
    flexDirection: 'row',
    gap: 12,
  },
  balanceButton: {
    flex: 1,
  },
  quickActions: {
    margin: 16,
    padding: 16,
    borderRadius: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  quickActionButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  quickButton: {
    flex: 1,
  },
  transactionsContainer: {
    margin: 16,
    padding: 16,
    borderRadius: 8,
    marginBottom: 80,
  },
  transactionCard: {
    marginBottom: 8,
  },
  transactionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
  },
  transactionDetails: {
    flex: 1,
    marginLeft: 16,
  },
  transactionType: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  transactionAmount: {
    fontSize: 14,
    fontWeight: 'bold',
    marginTop: 4,
  },
  transactionTime: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
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
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    marginTop: 8,
    textAlign: 'center',
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
    backgroundColor: '#F39C12',
  },
  modal: {
    padding: 20,
    margin: 20,
  },
  input: {
    marginBottom: 16,
  },
  addressLabel: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  addressText: {
    fontSize: 14,
    fontFamily: 'monospace',
    backgroundColor: '#f0f0f0',
    padding: 12,
    borderRadius: 4,
    marginBottom: 16,
  },
  receiveActions: {
    flexDirection: 'row',
    gap: 12,
  },
});

export default WalletScreen;
