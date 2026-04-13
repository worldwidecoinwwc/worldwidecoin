package com.worldwidecoin.wallet.presentation.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext

private val DarkColorScheme = darkColorScheme(
    primary = Color(0xFFF39C12),
    onPrimary = Color(0xFF000000),
    primaryContainer = Color(0xFFE67E22),
    onPrimaryContainer = Color(0xFF000000),
    secondary = Color(0xFF3498DB),
    onSecondary = Color(0xFFFFFFFF),
    secondaryContainer = Color(0xFF2980B9),
    onSecondaryContainer = Color(0xFFFFFFFF),
    tertiary = Color(0xFF27AE60),
    onTertiary = Color(0xFFFFFFFF),
    tertiaryContainer = Color(0xFF229954),
    onTertiaryContainer = Color(0xFFFFFFFF),
    background = Color(0xFF1A1A1A),
    onBackground = Color(0xFFE0E0E0),
    surface = Color(0xFF2D2D2D),
    onSurface = Color(0xFFE0E0E0),
    surfaceVariant = Color(0xFF404040),
    onSurfaceVariant = Color(0xFFB0B0B0),
    error = Color(0xFFE74C3C),
    onError = Color(0xFFFFFFFF),
    errorContainer = Color(0xFFC0392B),
    onErrorContainer = Color(0xFFFFFFFF),
    outline = Color(0xFF666666),
    outlineVariant = Color(0xFF444444)
)

private val LightColorScheme = lightColorScheme(
    primary = Color(0xFFF39C12),
    onPrimary = Color(0xFFFFFFFF),
    primaryContainer = Color(0xFFF39C12),
    onPrimaryContainer = Color(0xFF000000),
    secondary = Color(0xFF3498DB),
    onSecondary = Color(0xFFFFFFFF),
    secondaryContainer = Color(0xFF3498DB),
    onSecondaryContainer = Color(0xFFFFFFFF),
    tertiary = Color(0xFF27AE60),
    onTertiary = Color(0xFFFFFFFF),
    tertiaryContainer = Color(0xFF27AE60),
    onTertiaryContainer = Color(0xFFFFFFFF),
    background = Color(0xFFF8F9FA),
    onBackground = Color(0xFF333333),
    surface = Color(0xFFFFFFFF),
    onSurface = Color(0xFF333333),
    surfaceVariant = Color(0xFFF0F0F0),
    onSurfaceVariant = Color(0xFF666666),
    error = Color(0xFFE74C3C),
    onError = Color(0xFFFFFFFF),
    errorContainer = Color(0xFFE74C3C),
    onErrorContainer = Color(0xFFFFFFFF),
    outline = Color(0xFFDDDDDD),
    outlineVariant = Color(0xFFBBBBBB)
)

@Composable
fun WorldWideCoinTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    // Dynamic color is available on Android 12+
    dynamicColor: Boolean = false,
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }

        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
