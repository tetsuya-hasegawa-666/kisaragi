import org.gradle.api.tasks.testing.Test

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.reviework.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.reviework.app"
        minSdk = 29
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        viewBinding = true
    }

    sourceSets {
        getByName("test") {
            java.srcDirs("../../../--testcode/prj-kisaragi_0002/android-test/java")
        }
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("androidx.constraintlayout:constraintlayout:2.2.1")

    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.6.1")
}

tasks.withType<Test>().configureEach {
    val testLogsDir = rootProject.file("../../--testlogs/prj-kisaragi_0002")
    val rawArtifactsDir = rootProject.file("../../../--exsams/prj-kisaragi_0002/android-test")
    val taskDir = name
    reports.junitXml.required.set(true)
    reports.junitXml.outputLocation.set(testLogsDir.resolve("reports/$taskDir/junit"))
    reports.html.required.set(true)
    reports.html.outputLocation.set(testLogsDir.resolve("reports/$taskDir/html"))
    binaryResultsDirectory.set(rawArtifactsDir.resolve("$taskDir/binary"))
}
