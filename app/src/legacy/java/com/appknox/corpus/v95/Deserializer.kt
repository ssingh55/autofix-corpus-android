package com.appknox.corpus.v95

import java.io.ByteArrayInputStream
import java.io.ObjectInputStream

object Deserializer {
    fun read(bytes: ByteArray): Any? = ObjectInputStream(ByteArrayInputStream(bytes)).readObject()
}
