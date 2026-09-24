package com.appknox.corpus.v5

import java.security.KeyStore
import java.security.cert.X509Certificate
import javax.net.ssl.TrustManagerFactory
import javax.net.ssl.X509TrustManager

class TrustAllManager : X509TrustManager {
    private val defaultTrustManager: X509TrustManager = run {
        val trustManagerFactory = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm())
        trustManagerFactory.init(null as KeyStore?)
        trustManagerFactory.trustManagers.first { it is X509TrustManager } as X509TrustManager
    }

    override fun checkClientTrusted(chain: Array<X509Certificate>?, authType: String?) {
        defaultTrustManager.checkClientTrusted(chain, authType)
    }
    override fun checkServerTrusted(chain: Array<X509Certificate>?, authType: String?) {
        defaultTrustManager.checkServerTrusted(chain, authType)
    }
    override fun getAcceptedIssuers(): Array<X509Certificate> = defaultTrustManager.acceptedIssuers
}
