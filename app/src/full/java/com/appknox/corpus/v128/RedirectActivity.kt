package com.appknox.corpus.v128

import android.app.Activity
import android.content.ComponentName
import android.content.Intent
import android.os.Build
import android.os.Bundle

class RedirectActivity : Activity() {
    companion object {
        private val ALLOWED_COMPONENTS: Set<ComponentName> = setOf()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val next: Intent? = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            intent.getParcelableExtra("next", Intent::class.java)
        } else {
            @Suppress("DEPRECATION")
            intent.getParcelableExtra("next")
        }

        if (next != null) {
            val resolvedComponent = next.resolveActivity(packageManager)
            if (resolvedComponent != null && ALLOWED_COMPONENTS.contains(resolvedComponent)) {
                startActivity(next)
            }
        }
    }
}
