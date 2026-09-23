package com.appknox.corpus

import android.content.Context
import android.webkit.WebView

/** Calls every planted construct of this flavor so each stays reachable from MainActivity. */
object Corpus {
    fun runAll(context: Context) {
        com.appknox.corpus.v11.JsBridge.expose(WebView(context))
        com.appknox.corpus.v82.ContactsDump.count(context)
        com.appknox.corpus.v95.Deserializer.read(ByteArray(0))
    }
}
