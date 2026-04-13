package com.worldwidecoin.wallet.presentation.screens.explorer

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavController
import com.worldwidecoin.wallet.presentation.components.BlockItem
import com.worldwidecoin.wallet.presentation.components.NetworkStatsCard
import com.worldwidecoin.wallet.presentation.components.SearchBar

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BlockchainExplorerScreen(
    navController: NavController,
    viewModel: BlockchainExplorerViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    var searchQuery by remember { mutableStateOf("") }
    var selectedTab by remember { mutableStateOf(ExplorerTab.Blocks) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // Search Bar
        SearchBar(
            query = searchQuery,
            onQueryChange = { searchQuery = it },
            onSearch = { viewModel.search(it) },
            placeholder = "Search block height, hash, or transaction..."
        )

        Spacer(modifier = Modifier.height(16.dp))

        // Tab Selection
        TabRow(selectedTabIndex = selectedTab.ordinal) {
            ExplorerTab.values().forEach { tab ->
                Tab(
                    selected = selectedTab == tab,
                    onClick = { 
                        selectedTab = tab
                        viewModel.loadTabData(tab)
                    },
                    text = { Text(tab.title) }
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Refresh Button
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = when (selectedTab) {
                    ExplorerTab.Blocks -> "Latest Blocks"
                    ExplorerTab.Transactions -> "Latest Transactions"
                    ExplorerTab.Network -> "Network Statistics"
                },
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold
            )

            IconButton(
                onClick = { viewModel.refreshCurrentTab() }
            ) {
                Icon(Icons.Default.Refresh, contentDescription = "Refresh")
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Content
        when (selectedTab) {
            ExplorerTab.Blocks -> {
                if (uiState.blocks.isEmpty()) {
                    Box(
                        modifier = Modifier.fillMaxWidth(),
                        contentAlignment = Alignment.Center
                    ) {
                        if (uiState.isLoading) {
                            CircularProgressIndicator()
                        } else {
                            Text("No blocks found")
                        }
                    }
                } else {
                    LazyColumn(
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        items(uiState.blocks) { block ->
                            BlockItem(
                                block = block,
                                onClick = { 
                                    // Navigate to block details
                                }
                            )
                        }
                    }
                }
            }

            ExplorerTab.Transactions -> {
                if (uiState.transactions.isEmpty()) {
                    Box(
                        modifier = Modifier.fillMaxWidth(),
                        contentAlignment = Alignment.Center
                    ) {
                        if (uiState.isLoading) {
                            CircularProgressIndicator()
                        } else {
                            Text("No transactions found")
                        }
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

            ExplorerTab.Network -> {
                NetworkStatsCard(
                    stats = uiState.networkStats,
                    isLoading = uiState.isLoading
                )
            }
        }

        // Error handling
        uiState.error?.let { error ->
            Spacer(modifier = Modifier.height(16.dp))
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.errorContainer
                )
            ) {
                Text(
                    text = error,
                    modifier = Modifier.padding(16.dp),
                    color = MaterialTheme.colorScheme.onErrorContainer
                )
            }
        }
    }
}

enum class ExplorerTab(val title: String) {
    Blocks("Blocks"),
    Transactions("Transactions"),
    Network("Network")
}
