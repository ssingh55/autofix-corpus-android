package com.appknox.corpus.v85

import android.preference.PreferenceActivity

@Suppress("DEPRECATION")
class PrefActivity : PreferenceActivity() {

    override fun isValidFragment(fragmentName: String?): Boolean {
        return false
    }
}
