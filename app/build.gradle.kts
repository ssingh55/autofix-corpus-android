plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.appknox.corpus"
    compileSdk = 34
    // id 8 needs org.apache.http.conn.ssl.AllowAllHostnameVerifier on the compile classpath.
    useLibrary("org.apache.http.legacy")

    defaultConfig {
        applicationId = "com.appknox.corpus"
        versionCode = 1
        versionName = "1.0"
    }

    flavorDimensions += "sdk"
    productFlavors {
        create("full") { dimension = "sdk"; minSdk = 24; targetSdk = 34 }
        // ids 11 (min+target <= 16), 95 (min < 21) and 82 (no crypto anywhere in the APK).
        create("legacy") { dimension = "sdk"; minSdk = 16; targetSdk = 16 }
    }

    signingConfigs {
        getByName("debug") {
            // id 117 (Janus) fires only on a v1-signed APK with minSdk < 27.
            enableV1Signing = true
            enableV2Signing = true
        }
    }

    buildTypes {
        release {
            // id 104 (obfuscation) must fire, and ids 121/122 need resource names intact.
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("debug")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }

    // The ONLY build-file deviation: id 3 hardcodes debuggable, and targetSdk 16 trips lint.
    lint {
        abortOnError = false
        disable += "HardcodedDebugMode"
    }
}

dependencies {
    "fullImplementation"(project(":v98lib"))
    // Real apps ship androidx.core, and autofix emits ContextCompat calls (id 88). Full only:
    // legacy keeps minSdk 16 and id 82 needs no crypto anywhere in its APK.
    "fullImplementation"("androidx.core:core-ktx:1.13.1")
}
