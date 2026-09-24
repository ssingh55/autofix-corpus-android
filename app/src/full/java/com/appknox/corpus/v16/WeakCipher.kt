package com.appknox.corpus.v16

import javax.crypto.Cipher

object WeakCipher {
    fun create(): Cipher = Cipher.getInstance("AES/GCM/NoPadding")
}
