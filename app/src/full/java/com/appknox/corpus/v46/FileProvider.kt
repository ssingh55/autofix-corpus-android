package com.appknox.corpus.v46

import android.net.Uri
import android.os.ParcelFileDescriptor
import com.appknox.corpus.components.EmptyProvider
import java.io.File

class FileProvider : EmptyProvider() {
    override fun openFile(uri: Uri, mode: String): ParcelFileDescriptor? {
        val file = File(context!!.filesDir, uri.lastPathSegment!!)
        return ParcelFileDescriptor.open(file, ParcelFileDescriptor.MODE_READ_ONLY)
    }
}
