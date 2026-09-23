package com.appknox.corpus

import android.app.Activity
import android.os.Bundle

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Plants must be reachable in the dex but never run on a device.
        if (intent.getBooleanExtra("corpus_run", false)) {
            Corpus.runAll(this)
        }
    }
}
