package com.appknox.corpus.v98

import android.webkit.WebSettings
import android.webkit.WebView

object PluginState {
    @Suppress("DEPRECATION")
    fun enable(web: WebView) {
        web.settings.pluginState = WebSettings.PluginState.ON
    }
}
