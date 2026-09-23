package com.appknox.corpus

import android.content.Context
import android.webkit.WebView

/** Calls every planted construct of this flavor so each stays reachable from MainActivity. */
object Corpus {
    fun runAll(context: Context) {
        com.appknox.corpus.v5.TrustAllManager()
        com.appknox.corpus.v6.AllowAllVerifier()
        com.appknox.corpus.v7.InsecureFactory.create()
        com.appknox.corpus.v8.LegacyVerifier.create()
        WebView(context).webViewClient = com.appknox.corpus.v9.ProceedingClient()
        com.appknox.corpus.v15.RawSocket.open()
        val web = WebView(context)
        com.appknox.corpus.v88.DynamicReceiver.register(context)
        com.appknox.corpus.v89.ImplicitService.start(context)
        com.appknox.corpus.v94.CorsSettings.apply(web)
    }
}
