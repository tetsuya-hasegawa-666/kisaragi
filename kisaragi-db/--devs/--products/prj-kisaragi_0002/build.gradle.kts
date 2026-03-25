plugins {
    id("com.android.application") version "8.8.0" apply false
    id("org.jetbrains.kotlin.android") version "2.0.21" apply false
}

val revieworkExsamsDir = file("../../../--exsams/prj-kisaragi_0002")

layout.buildDirectory.set(revieworkExsamsDir.resolve("root-build"))

subprojects {
    layout.buildDirectory.set(revieworkExsamsDir.resolve("${project.name}-build"))
}
