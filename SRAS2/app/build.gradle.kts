plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
}

android {
    namespace = "com.example.sras"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.example.sras"
        minSdk = 28
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }

    kotlinOptions {
        jvmTarget = "11"
    }

    composeOptions {
        kotlinCompilerExtensionVersion = "1.6.0"
    }

    buildFeatures {
        compose = true
        viewBinding = true

    }

    packagingOptions {
        resources {
            excludes.addAll(
                listOf(
                    "META-INF/DEPENDENCIES",
                    "META-INF/LICENSE",
                    "META-INF/LICENSE.txt",
                    "META-INF/NOTICE",
                    "META-INF/NOTICE.txt"
                )
            )
        }
    }
}


dependencies {
    implementation(libs.androidx.material.icons.extended)
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.ui)
    implementation(libs.androidx.ui.graphics)
    implementation(libs.androidx.ui.tooling.preview)
    implementation(libs.androidx.material3)
    implementation(libs.androidx.runner)
    implementation(libs.androidx.espresso.core)
    implementation(libs.androidx.appcompat)
    implementation(libs.play.services.tasks)
    implementation(libs.firebase.crashlytics.buildtools)
    implementation(libs.play.services.tflite.gpu)
    implementation(libs.material)
    implementation(libs.androidx.navigation.fragment.ktx)
    implementation(libs.androidx.navigation.ui.ktx)

    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.ui.test.junit4)
    debugImplementation(libs.androidx.ui.tooling)
    debugImplementation(libs.androidx.ui.test.manifest)

    // Jetpack Compose
    implementation(libs.androidx.activity.compose.v182)
    implementation(libs.ui)
    implementation(libs.material3)
    implementation(libs.ui.tooling.preview)

    // Navigation
    implementation(libs.androidx.navigation.compose)

    // Lifecycle
    implementation(libs.androidx.lifecycle.runtime.ktx.v262)
    implementation(libs.androidx.lifecycle.viewmodel.compose)

    // CameraX (single, consistent version)
    implementation(libs.androidx.camera.core.v133)
    implementation(libs.androidx.camera.camera2.v133)
    implementation(libs.androidx.camera.lifecycle.v133)
    implementation(libs.androidx.camera.view.v133)

    // TensorFlow Lite
    implementation(libs.tensorflow.lite.support)
    implementation (libs.tensorflow.lite.gpu)
    implementation(libs.tensorflow.lite.v2161)
    implementation(libs.okhttp.logging)


    // Coil
    implementation(libs.coil.compose)

    implementation (libs.glide)
    implementation(libs.okhttp3.integration)
    implementation(libs.mpandroidchart.v310)

    // Retrofit & Gson
    implementation(libs.retrofit)
    implementation(libs.converter.gson)
    implementation(libs.okhttp)

    implementation (libs.androidx.core.ktx.v1120) // or latest version
    implementation (libs.androidx.cardview)





}
