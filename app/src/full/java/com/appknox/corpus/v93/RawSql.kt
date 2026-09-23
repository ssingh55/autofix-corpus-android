package com.appknox.corpus.v93

import android.database.sqlite.SQLiteDatabase

object RawSql {
    fun find(name: String) {
        val db = SQLiteDatabase.create(null)
        db.rawQuery("SELECT * FROM users WHERE name = '" + name + "'", null).close()
    }
}
