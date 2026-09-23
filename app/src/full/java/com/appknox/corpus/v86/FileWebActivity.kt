package com.appknox.corpus.v86

import android.app.Activity
import android.os.Bundle
import android.webkit.WebView

class FileWebActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val web = WebView(this)
        web.settings.allowFileAccess = true
        setContentView(web)
    }
}
