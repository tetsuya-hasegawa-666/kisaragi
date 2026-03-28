package com.isensorium.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class MainScreenControllerTest {

    private val controller = MainScreenController()

    @Test
    fun buildRecordingConfigCarriesPocketMode() {
        val config =
            controller.buildRecordingConfig(
                MainScreenFormState(
                    videoFrameLogIntervalMs = 120L,
                    imuIntervalMs = 25L,
                    gnssIntervalMs = 900L,
                    bleIntervalMs = 1800L,
                    arCoreIntervalMs = 2200L,
                    bleEnabled = false,
                    arCoreEnabled = true,
                    recordingMode = RecordingMode.POCKET_RECORDING,
                ),
            )

        assertEquals(RecordingMode.POCKET_RECORDING, config.recordingMode)
        assertEquals(250L, config.videoFrameLogIntervalMs)
        assertEquals(5000L, config.arCoreIntervalMs)
        assertEquals(false, config.bleEnabled)
    }

    @Test
    fun resolveRecordingConfigBuildsPocketModeGuidance() {
        val resolution =
            controller.resolveRecordingConfig(
                MainScreenFormState(
                    videoFrameLogIntervalMs = 100L,
                    imuIntervalMs = 20L,
                    gnssIntervalMs = 1000L,
                    bleIntervalMs = 1500L,
                    arCoreIntervalMs = 2000L,
                    bleEnabled = true,
                    arCoreEnabled = true,
                    recordingMode = RecordingMode.POCKET_RECORDING,
                ),
            )

        assertEquals(250L, resolution.config.videoFrameLogIntervalMs)
        assertEquals(5000L, resolution.config.bleIntervalMs)
        assertEquals(5000L, resolution.config.arCoreIntervalMs)
        assertNotNull(resolution.issue)
        assertTrue(resolution.issue!!.message.contains("ポケット収納計測"))
    }

    @Test
    fun resolveRecordingConfigKeepsStandardModeUntouched() {
        val resolution =
            controller.resolveRecordingConfig(
                MainScreenFormState(
                    videoFrameLogIntervalMs = 100L,
                    imuIntervalMs = 20L,
                    gnssIntervalMs = 1000L,
                    bleIntervalMs = 2000L,
                    arCoreIntervalMs = 2000L,
                    bleEnabled = true,
                    arCoreEnabled = true,
                    recordingMode = RecordingMode.STANDARD_HANDHELD,
                ),
            )

        assertEquals(100L, resolution.config.videoFrameLogIntervalMs)
        assertEquals(2000L, resolution.config.bleIntervalMs)
        assertEquals(2000L, resolution.config.arCoreIntervalMs)
        assertNull(resolution.issue)
    }

    @Test
    fun buildModeSummaryShowsPocketModeInJapanese() {
        val summary =
            controller.buildModeSummary(
                RecordingConfig(
                    bleEnabled = false,
                    arCoreEnabled = false,
                    recordingMode = RecordingMode.POCKET_RECORDING,
                ),
                routeId = CameraStackRoute.CORECAMERA_SHARED_CAMERA_TRIAL.routeId,
            )

        assertTrue(summary.contains("ポケット収納計測"))
        assertTrue(summary.contains(CameraStackRoute.CORECAMERA_SHARED_CAMERA_TRIAL.routeId))
    }

    @Test
    fun buildSessionPresentationIncludesRecordingMode() {
        val session =
            RecordingSession(
                sessionId = "session-20260317-001",
                sessionDir = File("build/test-session"),
                manifestFile = File("build/test-session/session_manifest.json"),
                videoFile = File("build/test-session/video.mp4"),
                imuFile = File("build/test-session/imu.csv"),
                gnssFile = File("build/test-session/gnss.csv"),
                bleFile = File("build/test-session/ble_scan.jsonl"),
                arCoreFile = File("build/test-session/arcore_pose.jsonl"),
                frameTimestampsFile = File("build/test-session/video_frame_timestamps.csv"),
                videoEventsFile = File("build/test-session/video_events.jsonl"),
                timebase = SessionTimebase(1000L, 2000L),
                adapterMetadata =
                    SessionAdapterMetadata(
                        adapterSeamId = "shared-camera-session-adapter",
                        requestedRoute = CameraStackRoute.CORECAMERA_SHARED_CAMERA_TRIAL.routeId,
                        activeRoute = CameraStackRoute.CORECAMERA_SHARED_CAMERA_TRIAL.routeId,
                        cutoverGateStatus = "READY_FOR_RUNTIME_WIRING",
                        rollbackAnchorTag = "tag",
                        rollbackAnchorCommit = "commit",
                        preservedOperations = listOf("startSession"),
                    ),
                recordingConfig = RecordingConfig(recordingMode = RecordingMode.POCKET_RECORDING),
            )

        val presentation = controller.buildSessionPresentation(session, sessionElapsedSec = 2.5)

        assertTrue(presentation.summaryText.contains("pocket_recording"))
        assertTrue(presentation.summaryText.contains("ポケット収納計測"))
    }
}
