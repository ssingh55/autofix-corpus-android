package com.appknox.corpus.v15

import java.net.Socket

object RawSocket {
    fun open(): Socket = Socket("corpus.example.com", 80)
}
