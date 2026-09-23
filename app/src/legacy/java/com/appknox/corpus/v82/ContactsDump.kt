package com.appknox.corpus.v82

import android.content.Context
import android.provider.ContactsContract

object ContactsDump {
    fun count(context: Context): Int {
        val cursor = context.contentResolver.query(
            ContactsContract.Contacts.CONTENT_URI, null, null, null, null)
        val n = cursor?.count ?: 0
        cursor?.close()
        return n
    }
}
