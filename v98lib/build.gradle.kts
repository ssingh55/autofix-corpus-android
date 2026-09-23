plugins {
    id("com.android.library")
    id("org.jetbrains.kotlin.android")
}
android {
    namespace = "com.appknox.corpus.v98"
    compileSdk = 25
    defaultConfig { minSdk = 16 }
    // compileSdk < 30 rejects Java 9+ source; setPluginState needs API 25.
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }
    kotlinOptions { jvmTarget = "1.8" }
    lint { abortOnError = false }
}
