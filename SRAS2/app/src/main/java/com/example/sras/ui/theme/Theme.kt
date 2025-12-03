package com.example.sras.ui.theme

import androidx.compose.material3.*
import androidx.compose.runtime.Composable

@Composable
fun SrasTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = lightColorScheme(),
        typography = Typography(),
        content = content
    )
}
