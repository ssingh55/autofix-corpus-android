package com.appknox.corpus.v7

import javax.net.ssl.SSLSocketFactory

object InsecureFactory {
    fun create(): SSLSocketFactory = SSLSocketFactory.getDefault() as SSLSocketFactory
}
