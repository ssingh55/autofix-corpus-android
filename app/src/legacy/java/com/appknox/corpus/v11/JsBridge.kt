package com.appknox.corpus.v11

import android.annotation.SuppressLint
import android.webkit.WebView

object JsBridge {
    class Bridge { fun ping(): String = "pong" }

    @SuppressLint("JavascriptInterface", "AddJavascriptInterface")
    fun expose(web: WebView) {
        web.addJavascriptInterface(Bridge(), "corpusBridge")
    }
}
