package com.isensorium.app

enum class RecordingMode(val modeId: String) {
    STANDARD_HANDHELD("standard_handheld"),
    POCKET_RECORDING("pocket_recording"),
    ;

    companion object {
        fun fromModeId(value: String?): RecordingMode =
            entries.firstOrNull { it.modeId.equals(value, ignoreCase = true) } ?: STANDARD_HANDHELD
    }
}
