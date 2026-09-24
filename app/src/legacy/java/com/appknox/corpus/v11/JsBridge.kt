package com.appknox.corpus.v11

import android.annotation.SuppressLint
import android.webkit.JavascriptInterface
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient

object JsBridge {
    class Bridge {
        @JavascriptInterface
        fun ping(): String = "pong"
    }

    @SuppressLint("JavascriptInterface", "AddJavascriptInterface")
    fun expose(web: WebView) {
        web.addJavascriptInterface(Bridge(), "corpusBridge")

        web.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(
                view: WebView,
                request: WebResourceRequest
            ): Boolean {
                if (request.url.scheme.equals("http")) {
                    return true
                }
                return super.shouldOverrideUrlLoading(view, request)
            }
        }
    }
}
