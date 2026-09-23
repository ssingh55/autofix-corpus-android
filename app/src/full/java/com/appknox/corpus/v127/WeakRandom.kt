package com.appknox.corpus.v127

import java.util.Random

object WeakRandom {
    fun otp(): Int = Random().nextInt(1_000_000)
}
