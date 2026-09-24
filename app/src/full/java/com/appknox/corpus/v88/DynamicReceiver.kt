package com.appknox.corpus.v88

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import androidx.core.content.ContextCompat

object DynamicReceiver {
    private val receiver = object : BroadcastReceiver() {
        override fun onReceive(c: Context?, i: Intent?) {}
    }

    fun register(context: Context) {
        ContextCompat.registerReceiver(
            context,
            receiver,
            IntentFilter("com.appknox.corpus.PING"),
            ContextCompat.RECEIVER_NOT_EXPORTED
        )
    }
}
