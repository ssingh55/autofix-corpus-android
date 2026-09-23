package com.appknox.corpus.v8

import org.apache.http.conn.ssl.AllowAllHostnameVerifier

object LegacyVerifier {
    @Suppress("DEPRECATION")
    fun create(): Any = AllowAllHostnameVerifier()
}
