package com.secirc.android.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController

/**
 * Main Screen with Bottom Navigation
 * 
 * Provides navigation between Chats, Groups, Contacts, and Settings screens
 * Similar to WhatsApp's main interface with bottom navigation tabs
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(
    onNavigateToLogin: () -> Unit
) {
    val navController = rememberNavController()
    
    Scaffold(
        bottomBar = {
            BottomNavigationBar(navController = navController)
        }
    ) { paddingValues ->
        NavHost(
            navController = navController,
            startDestination = "chats",
            modifier = Modifier.padding(paddingValues)
        ) {
            composable("chats") {
                ChatsScreen(navController = navController)
            }
            composable("groups") {
                GroupsScreen(navController = navController)
            }
            composable("contacts") {
                ContactsScreen(navController = navController)
            }
            composable("settings") {
                SettingsScreen(
                    navController = navController,
                    onNavigateToLogin = onNavigateToLogin
                )
            }
        }
    }
}

@Composable
fun BottomNavigationBar(navController: NavController) {
    val items = listOf(
        BottomNavItem("chats", "Chats", Icons.Default.Chat),
        BottomNavItem("groups", "Groups", Icons.Default.Group),
        BottomNavItem("contacts", "Contacts", Icons.Default.Contacts),
        BottomNavItem("settings", "Settings", Icons.Default.Settings)
    )
    
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route
    
    NavigationBar {
        items.forEach { item ->
            NavigationBarItem(
                icon = { Icon(item.icon, contentDescription = item.title) },
                label = { Text(item.title) },
                selected = currentRoute == item.route,
                onClick = {
                    navController.navigate(item.route) {
                        popUpTo(navController.graph.startDestinationId) {
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

data class BottomNavItem(
    val route: String,
    val title: String,
    val icon: ImageVector
)
