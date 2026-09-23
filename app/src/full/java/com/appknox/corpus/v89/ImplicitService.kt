package com.appknox.corpus.v89

import android.content.Context
import android.content.Intent

object ImplicitService {
    fun start(context: Context) {
        context.startService(Intent("com.appknox.corpus.ACTION_SYNC"))
    }
}
