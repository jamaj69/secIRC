package com.secirc.android.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// secIRC Color Palette
val SecIRCBlue = Color(0xFF1E88E5)
val SecIRCBlueDark = Color(0xFF1565C0)
val SecIRCGreen = Color(0xFF4CAF50)
val SecIRCGreenDark = Color(0xFF388E3C)
val SecIRCGray = Color(0xFF757575)
val SecIRCGrayLight = Color(0xFFE0E0E0)
val SecIRCGrayDark = Color(0xFF424242)
val SecIRCRed = Color(0xFFE53935)
val SecIRCWhite = Color(0xFFFFFFFF)
val SecIRCBlack = Color(0xFF000000)

// Light Theme Colors
private val LightColorScheme = lightColorScheme(
    primary = SecIRCBlue,
    onPrimary = SecIRCWhite,
    primaryContainer = SecIRCBlue.copy(alpha = 0.1f),
    onPrimaryContainer = SecIRCBlueDark,
    secondary = SecIRCGray,
    onSecondary = SecIRCWhite,
    secondaryContainer = SecIRCGrayLight,
    onSecondaryContainer = SecIRCGrayDark,
    tertiary = SecIRCGreen,
    onTertiary = SecIRCWhite,
    tertiaryContainer = SecIRCGreen.copy(alpha = 0.1f),
    onTertiaryContainer = SecIRCGreenDark,
    error = SecIRCRed,
    onError = SecIRCWhite,
    errorContainer = SecIRCRed.copy(alpha = 0.1f),
    onErrorContainer = SecIRCRed,
    background = SecIRCWhite,
    onBackground = SecIRCBlack,
    surface = SecIRCWhite,
    onSurface = SecIRCBlack,
    surfaceVariant = SecIRCGrayLight,
    onSurfaceVariant = SecIRCGrayDark,
    outline = SecIRCGray,
    outlineVariant = SecIRCGrayLight,
    scrim = SecIRCBlack.copy(alpha = 0.5f)
)

// Dark Theme Colors
private val DarkColorScheme = darkColorScheme(
    primary = SecIRCBlue,
    onPrimary = SecIRCBlack,
    primaryContainer = SecIRCBlueDark,
    onPrimaryContainer = SecIRCBlue.copy(alpha = 0.8f),
    secondary = SecIRCGray,
    onSecondary = SecIRCBlack,
    secondaryContainer = SecIRCGrayDark,
    onSecondaryContainer = SecIRCGrayLight,
    tertiary = SecIRCGreen,
    onTertiary = SecIRCBlack,
    tertiaryContainer = SecIRCGreenDark,
    onTertiaryContainer = SecIRCGreen.copy(alpha = 0.8f),
    error = SecIRCRed,
    onError = SecIRCBlack,
    errorContainer = SecIRCRed.copy(alpha = 0.3f),
    onErrorContainer = SecIRCRed.copy(alpha = 0.8f),
    background = SecIRCBlack,
    onBackground = SecIRCWhite,
    surface = SecIRCGrayDark,
    onSurface = SecIRCWhite,
    surfaceVariant = SecIRCGrayDark,
    onSurfaceVariant = SecIRCGrayLight,
    outline = SecIRCGray,
    outlineVariant = SecIRCGrayDark,
    scrim = SecIRCBlack.copy(alpha = 0.7f)
)

@Composable
fun SecIRCTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) {
        DarkColorScheme
    } else {
        LightColorScheme
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = SecIRCTypography,
        content = content
    )
}
