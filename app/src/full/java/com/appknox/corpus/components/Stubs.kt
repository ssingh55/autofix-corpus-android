package com.appknox.corpus.components

import android.app.Activity
import android.app.Service
import android.content.BroadcastReceiver
import android.content.ContentProvider
import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.database.Cursor
import android.net.Uri
import android.os.IBinder

/** Empty components that exist only to be declared in the manifest. */
class V1OpenService : Service() { override fun onBind(intent: Intent?): IBinder? = null }
class V38Activity : Activity()
class V39Receiver : BroadcastReceiver() { override fun onReceive(c: Context?, i: Intent?) {} }
class V40Service : Service() { override fun onBind(intent: Intent?): IBinder? = null }
class V42Activity : Activity()
class V43Receiver : BroadcastReceiver() { override fun onReceive(c: Context?, i: Intent?) {} }
class V44Service : Service() { override fun onBind(intent: Intent?): IBinder? = null }
class V84ShareActivity : Activity()
class V34BrowsableActivity : Activity()

/** A provider that answers nothing; subclassed by plants that need a real provider class. */
open class EmptyProvider : ContentProvider() {
    override fun onCreate() = true
    override fun query(u: Uri, p: Array<String>?, s: String?, a: Array<String>?, o: String?): Cursor? = null
    override fun getType(u: Uri): String? = null
    override fun insert(u: Uri, v: ContentValues?): Uri? = null
    override fun delete(u: Uri, s: String?, a: Array<String>?) = 0
    override fun update(u: Uri, v: ContentValues?, s: String?, a: Array<String>?) = 0
}
class V2GrantProvider : EmptyProvider()
class V41Provider : EmptyProvider()
class V45Provider : EmptyProvider()
