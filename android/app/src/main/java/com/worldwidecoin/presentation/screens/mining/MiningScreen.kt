package com.worldwidecoin.presentation.screens.mining

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController

@Composable
fun MiningScreen(
    navController: NavController
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        Text(
            text = "Mining Dashboard",
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Card(
            modifier = Modifier.fillMaxWidth(),
            elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
        ) {
            Column(
                modifier = Modifier.padding(16.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            text = "Mining Status",
                            style = MaterialTheme.typography.titleMedium
                        )
                        Text(
                            text = "Stopped",
                            color = MaterialTheme.colorScheme.error
                        )
                    }
                    
                    Button(
                        onClick = { /* TODO: Start mining */ },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text("Start Mining")
                    }
                }
                
                Spacer(modifier = Modifier.height(16.dp))
                
                Text(
                    text = "Mining Statistics",
                    style = MaterialTheme.typography.titleMedium
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                Text(
                    text = "Hash Rate: 0 H/s",
                    style = MaterialTheme.typography.bodyMedium
                )
                
                Text(
                    text = "Blocks Mined: 0",
                    style = MaterialTheme.typography.bodyMedium
                )
            }
        }
    }
}
