package com.appknox.corpus.v128

import android.app.Activity
import android.content.Intent
import android.os.Bundle

class RedirectActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        @Suppress("DEPRECATION")
        val next = intent.getParcelableExtra<Intent>("next")
        startActivity(next)
    }
}
