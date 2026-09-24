package com.appknox.corpus.v94

import android.webkit.WebView

object CorsSettings {
    @Suppress("DEPRECATION")
    fun apply(web: WebView) {
        web.settings.allowUniversalAccessFromFileURLs = false
    }
}
