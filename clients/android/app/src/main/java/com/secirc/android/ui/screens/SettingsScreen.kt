package com.secirc.android.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController

/**
 * Settings Screen - App settings and profile management
 * 
 * Displays user profile, app settings, and security options
 * Similar to WhatsApp's settings screen with profile and preferences
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    navController: NavController,
    onNavigateToLogin: () -> Unit
) {
    var showLogoutDialog by remember { mutableStateOf(false) }
    
    // Sample user data - in real app this would come from ViewModel
    val userProfile = remember {
        UserProfile(
            nickname = "Alice",
            userHash = "a1b2c3d4e5f6g7h8",
            isOnline = true,
            keyRotationCount = 5,
            lastKeyRotation = System.currentTimeMillis() - 3600000
        )
    }
    
    val settingsSections = remember {
        listOf(
            SettingsSection(
                title = "Account",
                items = listOf(
                    SettingsItem("Profile", "Manage your profile information", Icons.Default.Person),
                    SettingsItem("Privacy", "Control your privacy settings", Icons.Default.PrivacyTip),
                    SettingsItem("Security", "Manage security and encryption", Icons.Default.Security),
                    SettingsItem("Keys", "Manage your encryption keys", Icons.Default.Key)
                )
            ),
            SettingsSection(
                title = "App",
                items = listOf(
                    SettingsItem("Notifications", "Configure notification settings", Icons.Default.Notifications),
                    SettingsItem("Appearance", "Customize app appearance", Icons.Default.Palette),
                    SettingsItem("Storage", "Manage app storage and data", Icons.Default.Storage),
                    SettingsItem("About", "App information and version", Icons.Default.Info)
                )
            ),
            SettingsSection(
                title = "Network",
                items = listOf(
                    SettingsItem("Relay Servers", "Manage relay server connections", Icons.Default.Cloud),
                    SettingsItem("Discovery", "Configure server discovery", Icons.Default.Search),
                    SettingsItem("Connection", "Network connection settings", Icons.Default.Wifi)
                )
            )
        )
    }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
    ) {
        // Top App Bar
        TopAppBar(
            title = {
                Text(
                    text = "Settings",
                    style = MaterialTheme.typography.headlineMedium,
                    fontWeight = FontWeight.Bold
                )
            },
            colors = TopAppBarDefaults.topAppBarColors(
                containerColor = MaterialTheme.colorScheme.primary,
                titleContentColor = MaterialTheme.colorScheme.onPrimary
            )
        )
        
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(vertical = 16.dp)
        ) {
            // User Profile Section
            item {
                UserProfileCard(
                    userProfile = userProfile,
                    onEditProfile = { /* Navigate to edit profile */ }
                )
            }
            
            // Settings Sections
            items(settingsSections) { section ->
                SettingsSectionCard(
                    section = section,
                    onItemClick = { item ->
                        // Handle settings item click
                        when (item.title) {
                            "Profile" -> { /* Navigate to profile */ }
                            "Privacy" -> { /* Navigate to privacy */ }
                            "Security" -> { /* Navigate to security */ }
                            "Keys" -> { /* Navigate to keys */ }
                            "Notifications" -> { /* Navigate to notifications */ }
                            "Appearance" -> { /* Navigate to appearance */ }
                            "Storage" -> { /* Navigate to storage */ }
                            "About" -> { /* Navigate to about */ }
                            "Relay Servers" -> { /* Navigate to relay servers */ }
                            "Discovery" -> { /* Navigate to discovery */ }
                            "Connection" -> { /* Navigate to connection */ }
                        }
                    }
                )
            }
            
            // Logout Section
            item {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 8.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.errorContainer
                    )
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { showLogoutDialog = true }
                            .padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            imageVector = Icons.Default.ExitToApp,
                            contentDescription = "Logout",
                            tint = MaterialTheme.colorScheme.error,
                            modifier = Modifier.size(24.dp)
                        )
                        
                        Spacer(modifier = Modifier.width(16.dp))
                        
                        Text(
                            text = "Logout",
                            style = MaterialTheme.typography.titleMedium,
                            color = MaterialTheme.colorScheme.error,
                            fontWeight = FontWeight.Medium
                        )
                    }
                }
            }
        }
    }
    
    // Logout Confirmation Dialog
    if (showLogoutDialog) {
        AlertDialog(
            onDismissRequest = { showLogoutDialog = false },
            title = {
                Text("Logout")
            },
            text = {
                Text("Are you sure you want to logout? You will need to enter your password again to access your messages.")
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        showLogoutDialog = false
                        onNavigateToLogin()
                    }
                ) {
                    Text("Logout")
                }
            },
            dismissButton = {
                TextButton(
                    onClick = { showLogoutDialog = false }
                ) {
                    Text("Cancel")
                }
            }
        )
    }
}

@Composable
fun UserProfileCard(
    userProfile: UserProfile,
    onEditProfile: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Avatar
            Box(
                modifier = Modifier
                    .size(80.dp)
                    .clip(CircleShape)
                    .background(MaterialTheme.colorScheme.primary),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Default.Person,
                    contentDescription = "Profile Avatar",
                    tint = MaterialTheme.colorScheme.onPrimary,
                    modifier = Modifier.size(40.dp)
                )
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // User Info
            Text(
                text = userProfile.nickname,
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold
            )
            
            Spacer(modifier = Modifier.height(4.dp))
            
            Text(
                text = "Hash: ${userProfile.userHash.take(8)}...",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // Status
            Row(
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(8.dp)
                        .clip(CircleShape)
                        .background(
                            if (userProfile.isOnline) 
                                MaterialTheme.colorScheme.tertiary 
                            else 
                                MaterialTheme.colorScheme.onSurfaceVariant
                        )
                )
                
                Spacer(modifier = Modifier.width(8.dp))
                
                Text(
                    text = if (userProfile.isOnline) "Online" else "Offline",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Edit Profile Button
            OutlinedButton(
                onClick = onEditProfile,
                modifier = Modifier.fillMaxWidth()
            ) {
                Icon(
                    imageVector = Icons.Default.Edit,
                    contentDescription = "Edit Profile",
                    modifier = Modifier.size(18.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text("Edit Profile")
            }
        }
    }
}

@Composable
fun SettingsSectionCard(
    section: SettingsSection,
    onItemClick: (SettingsItem) -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Text(
                text = section.title,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Medium,
                color = MaterialTheme.colorScheme.primary,
                modifier = Modifier.padding(bottom = 12.dp)
            )
            
            section.items.forEach { item ->
                SettingsItemRow(
                    item = item,
                    onClick = { onItemClick(item) }
                )
                
                if (item != section.items.last()) {
                    Divider(
                        modifier = Modifier.padding(vertical = 8.dp),
                        color = MaterialTheme.colorScheme.outlineVariant
                    )
                }
            }
        }
    }
}

@Composable
fun SettingsItemRow(
    item: SettingsItem,
    onClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() }
            .padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            imageVector = item.icon,
            contentDescription = item.title,
            tint = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.size(24.dp)
        )
        
        Spacer(modifier = Modifier.width(16.dp))
        
        Column(
            modifier = Modifier.weight(1f)
        ) {
            Text(
                text = item.title,
                style = MaterialTheme.typography.bodyLarge,
                fontWeight = FontWeight.Medium
            )
            
            if (item.description.isNotEmpty()) {
                Text(
                    text = item.description,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
            }
        }
        
        Icon(
            imageVector = Icons.Default.ChevronRight,
            contentDescription = "Navigate",
            tint = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.size(20.dp)
        )
    }
}

data class UserProfile(
    val nickname: String,
    val userHash: String,
    val isOnline: Boolean,
    val keyRotationCount: Int,
    val lastKeyRotation: Long
)

data class SettingsSection(
    val title: String,
    val items: List<SettingsItem>
)

data class SettingsItem(
    val title: String,
    val description: String,
    val icon: androidx.compose.ui.graphics.vector.ImageVector
)
