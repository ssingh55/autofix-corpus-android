package com.appknox.corpus.v6

import javax.net.ssl.HostnameVerifier
import javax.net.ssl.SSLSession

class AllowAllVerifier : HostnameVerifier {
    override fun verify(hostname: String?, session: SSLSession?): Boolean = true
}
