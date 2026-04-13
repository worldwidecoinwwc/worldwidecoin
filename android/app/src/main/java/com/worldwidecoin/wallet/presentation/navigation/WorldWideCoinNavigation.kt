package com.worldwidecoin.wallet.presentation.navigation

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AccountBalance
import androidx.compose.material.icons.filled.BarChart
import androidx.compose.material.icons.filled.Explore
import androidx.compose.material.icons.filled.Mining
import androidx.compose.material.icons.filled.QrCodeScanner
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.navigation.NavController
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.worldwidecoin.presentation.screens.wallet.WalletScreen
import com.worldwidecoin.presentation.screens.explorer.BlockchainExplorerScreen
import com.worldwidecoin.presentation.screens.mining.MiningScreen
import com.worldwidecoin.presentation.screens.settings.SettingsScreen

@Composable
fun WorldWideCoinNavigation(navController: NavController) {
    NavHost(
        navController = navController,
        startDestination = BottomNavItem.Wallet.route
    ) {
        composable(BottomNavItem.Wallet.route) {
            WalletScreen(navController)
        }
        composable(BottomNavItem.Explorer.route) {
            BlockchainExplorerScreen(navController)
        }
        composable(BottomNavItem.Mining.route) {
            MiningScreen(navController)
        }
        composable(BottomNavItem.Settings.route) {
            SettingsScreen(navController)
        }
        composable("send") {
            SendScreen(navController)
        }
        composable("receive") {
            ReceiveScreen(navController)
        }
        composable("qr_scanner") {
            // QR Scanner will be handled as a separate activity
        }
    }
}

@Composable
fun BottomNavigationBar(navController: NavController) {
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route

    NavigationBar {
        BottomNavItem.values().forEach { item ->
            NavigationBarItem(
                icon = { Icon(item.icon, contentDescription = item.title) },
                label = { Text(item.title) },
                selected = currentRoute == item.route,
                onClick = {
                    navController.navigate(item.route) {
                        popUpTo(navController.graph.findStartDestination().id) {
                            saveState = true
                        }
                        launchSingleTop = true
                        restoreState = true
                    }
                }
            )
        }
    }
}

enum class BottomNavItem(
    val title: String,
    val icon: ImageVector,
    val route: String
) {
    Wallet(
        title = "Wallet",
        icon = Icons.Filled.AccountBalance,
        route = "wallet"
    ),
    Explorer(
        title = "Explorer",
        icon = Icons.Filled.Explore,
        route = "explorer"
    ),
    Mining(
        title = "Mining",
        icon = Icons.Filled.Mining,
        route = "mining"
    ),
    Settings(
        title = "Settings",
        icon = Icons.Filled.Settings,
        route = "settings"
    )
}
