package com.appknox.corpus.v127

import java.security.SecureRandom

object WeakRandom {
    fun otp(): Int = SecureRandom().nextInt(1_000_000)
}
