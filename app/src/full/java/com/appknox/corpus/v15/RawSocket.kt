package com.appknox.corpus.v15

import java.net.Socket

object RawSocket {
    // The port goes through a string on purpose: Sherlock's const-register regex expects
    // androguard-3 output ("#+80") and never reads a plain const under androguard 4, but it
    // back-fills a move-result register from the preceding const-string.
    fun open(): Socket = Socket("corpus.example.com", "80".toInt())
}
