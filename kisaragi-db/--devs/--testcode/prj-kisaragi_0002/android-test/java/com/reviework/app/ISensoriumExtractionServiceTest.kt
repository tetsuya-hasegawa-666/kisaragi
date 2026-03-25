package com.reviework.app

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ISensoriumExtractionServiceTest {

    private val service = ISensoriumExtractionService()

    @Test
    fun exportCopiesRawInputsAndDerivedOutputs() {
        val source =
            InMemorySessionInput(
                mapOf(
                    "session_manifest.json" to
                        """
                        {
                          "sessionId":"session-001",
                          "status":"complete",
                          "deviceModel":"SO-53B",
                          "collectorStatus":{"arcore":"ok"},
                          "timebase":{
                            "sessionStartWallTimeMs":1000,
                            "sessionStartElapsedRealtimeNanos":2000
                          }
                        }
                        """.trimIndent(),
                    "video.mp4" to "video-binary",
                    "video_frame_timestamps.csv" to
                        "frame_id,elapsed_realtime_ns,camera_sensor_timestamp_ns\n0,2001,1\n1,2009,2\n",
                    "imu.csv" to
                        "sensor_type,event_timestamp_ns,elapsed_realtime_ns,wall_time_ms,x,y,z,accuracy\naccel,2002,2002,1002,0,0,0,3\n",
                    "ble_scan.jsonl" to """{"elapsedRealtimeNanos":2004,"deviceAddress":"AA:BB:CC:DD","memberId":"worker-01"}""",
                    "arcore_pose.jsonl" to """{"elapsedRealtimeNanos":2005}""",
                    "video_events.jsonl" to """{"elapsedRealtimeNanos":2006,"type":"recording_finalize"}""",
                ),
            )
        val output = InMemorySessionOutput()

        val result = service.export(source, output)

        assertEquals("session-001", result.sessionId)
        assertTrue(output.files.containsKey("session-001/isensorium/session_manifest.json"))
        assertTrue(output.binaryFiles.containsKey("session-001/isensorium/video.mp4"))
        assertTrue(output.files.containsKey("session-001/isensorium/ble_scan.jsonl"))
        assertTrue(output.files.containsKey("session-001/trajectreview/input_readiness.json"))
        assertTrue(output.files.containsKey("session-001/trajectreview/sensor_quality.json"))
        assertTrue(output.files.containsKey("session-001/trajectreview/session_package.json"))
        assertTrue(output.files.containsKey("session-001/trajectreview/space_handoff_manifest.json"))

        val readiness = JSONObject(output.files.getValue("session-001/trajectreview/input_readiness.json"))
        assertTrue(readiness.getBoolean("readyForDiagnose"))

        val quality = JSONObject(output.files.getValue("session-001/trajectreview/sensor_quality.json"))
        assertTrue(quality.getJSONObject("nearestDeltaNs").getLong("poseNearestDeltaNs") >= 0L)
        val sessionPackage = JSONObject(output.files.getValue("session-001/trajectreview/session_package.json"))
        val handoff = JSONObject(output.files.getValue("session-001/trajectreview/space_handoff_manifest.json"))
        assertEquals("video.mp4", sessionPackage.getJSONObject("sourceFiles").getString("video"))
        assertTrue(handoff.getBoolean("readyForSpaceReconstruction"))
        assertTrue(result.readyForSpaceReconstruction)
    }

    @Test
    fun exportBuildsLegacyAliasIndexAndIdentityMap() {
        val source =
            InMemorySessionInput(
                mapOf(
                    "session_manifest.json" to
                        """
                        {
                          "sessionId":"legacy-session",
                          "deviceModel":"SO-53B",
                          "deviceId":"main-device",
                          "members":[{"memberId":"worker-01","deviceId":"worker-device","role":"worker"}],
                          "timebase":{
                            "sessionStartWallTimeMs":1000,
                            "sessionStartElapsedRealtimeNanos":2000
                          }
                        }
                        """.trimIndent(),
                    "video.mp4" to "video-binary",
                    "video_frame_timestamps.csv" to
                        "frame_id,elapsed_realtime_ns,camera_sensor_timestamp_ns\n0,2001,1\n",
                    "imu.csv" to
                        "sensor_type,event_timestamp_ns,elapsed_realtime_ns,wall_time_ms,x,y,z,accuracy\naccel,2002,2002,1002,0,0,0,3\n",
                    "bt_events.csv" to "timestamp_ns,deviceAddress,memberId\n2004,AA:BB:CC:DD,worker-01\n",
                    "arcore_pose.csv" to "timestamp_ns,tx,ty,tz\n2005,0,0,0\n",
                ),
            )
        val output = InMemorySessionOutput()

        service.export(source, output)

        val framePoseIndex = output.files.getValue("legacy-session/trajectreview/frame_pose_index.csv")
        val identityMap = JSONObject(output.files.getValue("legacy-session/trajectreview/member_identity_map.json"))

        assertTrue(framePoseIndex.contains("frame_id,frame_elapsed_realtime_ns,pose_elapsed_realtime_ns"))
        assertTrue(framePoseIndex.contains("2005"))
        assertEquals("worker-01", identityMap.getJSONArray("members").getJSONObject(1).getString("memberId"))
        assertEquals(
            "AA:BB:CC:DD",
            identityMap.getJSONArray("btIdentity").getJSONObject(0).getJSONArray("btIdentifiers").getString(0),
        )
    }

    @Test
    fun exportAcceptsManifestFramesAndBtCsvAliases() {
        val source =
            InMemorySessionInput(
                mapOf(
                    "manifest.json" to
                        """
                        {
                          "sessionId":"legacy-csv-session",
                          "deviceModel":"SO-53B",
                          "timebase":{
                            "sessionStartWallTimeMs":1000,
                            "sessionStartElapsedRealtimeNanos":2000
                          }
                        }
                        """.trimIndent(),
                    "video.mp4" to "video-binary",
                    "frames.csv" to "frame_id,timestamp_ns\n0,2001\n",
                    "imu.csv" to
                        "sensor_type,event_timestamp_ns,elapsed_realtime_ns,wall_time_ms,x,y,z,accuracy\naccel,2002,2002,1002,0,0,0,3\n",
                    "bt.csv" to "timestamp_ns,deviceAddress\n2004,AA:BB:CC:DD\n",
                    "arcore_pose.csv" to "timestamp_ns,tx,ty,tz\n2005,0,0,0\n",
                ),
            )
        val output = InMemorySessionOutput()

        val result = service.export(source, output)

        assertEquals("legacy-csv-session", result.sessionId)
        assertTrue(output.files.containsKey("legacy-csv-session/isensorium/manifest.json"))
        assertTrue(output.files.containsKey("legacy-csv-session/isensorium/frames.csv"))
        assertTrue(output.files.containsKey("legacy-csv-session/isensorium/bt.csv"))
        assertTrue(result.readyForDiagnose)
    }

    @Test
    fun exportAcceptsParentDirectoryContainingSessionFolder() {
        val child =
            InMemorySessionInput(
                mapOf(
                    "manifest.json" to
                        """
                        {
                          "sessionId":"nested-session",
                          "deviceModel":"SO-53B",
                          "timebase":{
                            "sessionStartWallTimeMs":1000,
                            "sessionStartElapsedRealtimeNanos":2000
                          }
                        }
                        """.trimIndent(),
                    "video.mp4" to "video-binary",
                    "frames.csv" to "frame_id,timestamp_ns\n0,2001\n",
                    "imu.csv" to
                        "sensor_type,event_timestamp_ns,elapsed_realtime_ns,wall_time_ms,x,y,z,accuracy\naccel,2002,2002,1002,0,0,0,3\n",
                    "bt.csv" to "timestamp_ns,deviceAddress\n2004,AA:BB:CC:DD\n",
                ),
            )
        val source =
            InMemorySessionInput(
                files = emptyMap(),
                children = listOf(child),
            )
        val output = InMemorySessionOutput()

        val result = service.export(source, output)

        assertEquals("nested-session", result.sessionId)
        assertTrue(output.files.containsKey("nested-session/isensorium/manifest.json"))
        assertTrue(result.readyForDiagnose)
    }

    private class InMemorySessionInput(
        private val files: Map<String, String>,
        private val children: List<InMemorySessionInput> = emptyList(),
    ) : SessionInputReader {
        override fun exists(filename: String): Boolean = files.containsKey(filename)

        override fun readText(filename: String): String? = files[filename]

        override fun readBytes(filename: String): ByteArray? = files[filename]?.toByteArray(Charsets.UTF_8)

        override fun listChildDirectories(): List<SessionInputReader> = children
    }

    private class InMemorySessionOutput : SessionOutputWriter {
        val files = linkedMapOf<String, String>()
        val binaryFiles = linkedMapOf<String, ByteArray>()

        override fun writeText(relativePath: String, content: String) {
            files[relativePath] = content
        }

        override fun writeBytes(relativePath: String, content: ByteArray) {
            val text = content.toString(Charsets.UTF_8)
            if (relativePath.endsWith(".mp4")) {
                binaryFiles[relativePath] = content
            } else {
                files[relativePath] = text
            }
        }
    }
}
