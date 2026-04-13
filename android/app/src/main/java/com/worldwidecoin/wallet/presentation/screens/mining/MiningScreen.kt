package com.worldwidecoin.wallet.presentation.screens.mining

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavController
import com.worldwidecoin.wallet.presentation.components.MiningStatsCard
import com.worldwidecoin.wallet.presentation.components.MiningStatusCard

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MiningScreen(
    navController: NavController,
    viewModel: MiningViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // Mining Status Card
        MiningStatusCard(
            isMining = uiState.isMining,
            hashRate = uiState.hashRate,
            blocksMined = uiState.blocksMined,
            onStartMining = viewModel::startMining,
            onStopMining = viewModel::stopMining,
            isLoading = uiState.isLoading
        )

        Spacer(modifier = Modifier.height(24.dp))

        // Mining Statistics
        Text(
            text = "Mining Statistics",
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold
        )

        Spacer(modifier = Modifier.height(16.dp))

        LazyColumn(
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            item {
                MiningStatsCard(
                    title = "Current Session",
                    stats = mapOf(
                        "Hash Rate" to "${uiState.hashRate} H/s",
                        "Blocks Found" to uiState.blocksMined.toString(),
                        "Mining Time" to uiState.miningTime,
                        "Efficiency" to "${uiState.efficiency}%"
                    )
                )
            }

            item {
                MiningStatsCard(
                    title = "Lifetime Earnings",
                    stats = mapOf(
                        "Total Blocks" to uiState.totalBlocksMined.toString(),
                        "Total WWC" to "${uiState.totalEarnings} WWC",
                        "First Block" to uiState.firstBlockTime,
                        "Average Rate" to "${uiState.averageHashRate} H/s"
                    )
                )
            }

            item {
                MiningStatsCard(
                    title = "Network Information",
                    stats = mapOf(
                        "Network Difficulty" to uiState.networkDifficulty,
                        "Block Reward" to "${uiState.blockReward} WWC",
                        "Network Hash Rate" to uiState.networkHashRate,
                        "Next Difficulty" to uiState.nextDifficulty
                    )
                )
            }

            if (uiState.recentBlocks.isNotEmpty()) {
                item {
                    Text(
                        text = "Recent Blocks",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(vertical = 8.dp)
                    )
                }

                items(uiState.recentBlocks) { block ->
                    Card(
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(
                            modifier = Modifier.padding(16.dp)
                        ) {
                            Text(
                                text = "Block #${block.height}",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold
                            )
                            Text(
                                text = "Hash: ${block.hash.take(16)}...",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            Text(
                                text = "Reward: ${block.reward} WWC",
                                style = MaterialTheme.typography.bodySmall
                            )
                        }
                    }
                }
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
