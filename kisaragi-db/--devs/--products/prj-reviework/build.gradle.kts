plugins {
    id("com.android.application") version "8.8.0" apply false
    id("org.jetbrains.kotlin.android") version "2.0.21" apply false
}

val revieworkTrialDataDir = file("../../../--trial-data/prj-reviework")

layout.buildDirectory.set(revieworkTrialDataDir.resolve("root-build"))

subprojects {
    layout.buildDirectory.set(revieworkTrialDataDir.resolve("${project.name}-build"))
}
