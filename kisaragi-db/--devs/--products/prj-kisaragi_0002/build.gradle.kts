plugins {
    id("com.android.application") version "8.8.0" apply false
    id("org.jetbrains.kotlin.android") version "2.0.21" apply false
}

val trajectreviewExsamsDir = file("../../../--exsams/prj-kisaragi_0002")

layout.buildDirectory.set(trajectreviewExsamsDir.resolve("root-build"))

subprojects {
    layout.buildDirectory.set(trajectreviewExsamsDir.resolve("${project.name}-build"))
}
