package com.appknox.corpus.v88

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter

object DynamicReceiver {
    private val receiver = object : BroadcastReceiver() {
        override fun onReceive(c: Context?, i: Intent?) {}
    }

    fun register(context: Context) {
        context.registerReceiver(receiver, IntentFilter("com.appknox.corpus.PING"))
    }
}
