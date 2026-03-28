package com.isensorium.app

import org.junit.Assert.assertEquals
import org.junit.Test

class RecordingModeTest {

    @Test
    fun fromModeIdFallsBackToStandardMode() {
        assertEquals(RecordingMode.STANDARD_HANDHELD, RecordingMode.fromModeId("unknown_mode"))
    }

    @Test
    fun fromModeIdResolvesPocketMode() {
        assertEquals(RecordingMode.POCKET_RECORDING, RecordingMode.fromModeId("pocket_recording"))
    }
}
