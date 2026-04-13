package com.worldwidecoin.wallet.presentation.screens.wallet

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowDownward
import androidx.compose.material.icons.filled.ArrowUpward
import androidx.compose.material.icons.filled.QrCodeScanner
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavController
import com.worldwidecoin.wallet.presentation.components.BalanceCard
import com.worldwidecoin.wallet.presentation.components.TransactionItem
import com.worldwidecoin.wallet.presentation.components.WelcomeCard

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WalletScreen(
    navController: NavController,
    viewModel: WalletViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // Welcome Card for new users
        if (uiState.isNewWallet) {
            WelcomeCard(
                onCreateWallet = viewModel::createNewWallet,
                onImportWallet = { navController.navigate("import_wallet") }
            )
            Spacer(modifier = Modifier.height(16.dp))
        }

        // Balance Card
        BalanceCard(
            balance = uiState.balance,
            isLoading = uiState.isLoading,
            onRefresh = viewModel::refreshBalance
        )

        Spacer(modifier = Modifier.height(24.dp))

        // Action Buttons
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Button(
                onClick = { navController.navigate("receive") },
                modifier = Modifier.weight(1f),
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.primary
                )
            ) {
                Icon(Icons.Default.ArrowDownward, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("Receive")
            }

            Button(
                onClick = { navController.navigate("send") },
                modifier = Modifier.weight(1f),
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.secondary
                )
            ) {
                Icon(Icons.Default.ArrowUpward, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("Send")
            }

            OutlinedButton(
                onClick = { navController.navigate("qr_scanner") },
                modifier = Modifier.weight(1f)
            ) {
                Icon(Icons.Default.QrCodeScanner, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("Scan")
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Recent Transactions
        Text(
            text = "Recent Transactions",
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold
        )

        Spacer(modifier = Modifier.height(16.dp))

        if (uiState.transactions.isEmpty()) {
            Box(
                modifier = Modifier.fillMaxWidth(),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "No transactions yet",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    style = MaterialTheme.typography.bodyLarge
                )
            }
        } else {
            LazyColumn(
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(uiState.transactions) { transaction ->
                    TransactionItem(
                        transaction = transaction,
                        onClick = { 
                            // Navigate to transaction details
                        }
                    )
                }
            }
        }
    }
}
