package com.appknox.corpus.v7

import android.net.SSLCertificateSocketFactory
import javax.net.ssl.SSLSocketFactory

object InsecureFactory {
    @Suppress("DEPRECATION")
    fun create(): SSLSocketFactory = SSLCertificateSocketFactory.getInsecure(0, null)
}
