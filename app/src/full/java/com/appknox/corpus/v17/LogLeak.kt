package com.appknox.corpus.v17

import android.util.Log

object LogLeak {
    fun leak() {
        Log.d("CorpusV17", "user session token refreshed")
    }
}
