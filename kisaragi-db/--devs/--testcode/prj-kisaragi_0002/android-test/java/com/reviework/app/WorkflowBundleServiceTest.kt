package com.reviework.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class WorkflowBundleServiceTest {

    private val service = WorkflowBundleService()

    @Test
    fun loadSnapshotBuildsReviewStateFromExtractedBundle() {
        val input =
            InMemorySessionInput(
                mapOf(
                    "session_package.json" to
                        """
                        {
                          "sessionId":"session-actual",
                          "requiredInputs":{"video":true,"imu":true,"bt":true},
                          "optionalInputs":{"poses":true,"gnss":false},
                          "streamCounts":{"frames":120,"imu":360,"bt":24},
                          "scores":{"completenessScore":1.0,"poseCoverageRatio":0.68},
                          "timebase":{"sessionStartElapsedRealtimeNanos":100}
                        }
                        """.trimIndent(),
                    "sensor_quality.json" to
                        """
                        {
                          "qualityFlags":{"hasPoseTimeline":true}
                        }
                        """.trimIndent(),
                    "space_handoff_manifest.json" to
                        """
                        {
                          "readyForSpaceReconstruction":true,
                          "blockers":[]
                        }
                        """.trimIndent(),
                    "member_identity_map.json" to
                        """
                        {
                          "members":[
                            {"memberId":"main_capture"},
                            {"memberId":"worker-01"},
                            {"memberId":"worker-02"}
                          ]
                        }
                        """.trimIndent(),
                ),
            )

        val snapshot = service.loadSnapshot(input)

        assertEquals(120, snapshot.intake.frames)
        assertEquals(2, snapshot.trajectory.workerPathCount)
        assertTrue(snapshot.space.colmapReadyForDensification)
        assertTrue(snapshot.trajectory.sameTimeHighlights.isNotEmpty())
    }

    @Test
    fun loadSnapshotUsesModelingOutputWhenPresent() {
        val input =
            InMemorySessionInput(
                mapOf(
                    "session_package.json" to
                        """
                        {
                          "sessionId":"session-modeled",
                          "requiredInputs":{"video":true,"imu":true,"bt":true},
                          "optionalInputs":{"poses":true,"gnss":false},
                          "streamCounts":{"frames":80},
                          "scores":{"completenessScore":0.9,"poseCoverageRatio":0.4}
                        }
                        """.trimIndent(),
                    "sensor_quality.json" to """{"qualityFlags":{"hasPoseTimeline":true}}""",
                    "space_handoff_manifest.json" to """{"readyForSpaceReconstruction":true,"blockers":[]}""",
                    "local_model_summary.json" to
                        """
                        {
                          "spaceQuality":"0.88",
                          "trajectoryQuality":"0.77",
                          "workerPathCount":1,
                          "weakArea":"補正対象 corridor",
                          "attentionPoints":[{"timeRange":"00:10","reason":"補正確認"}],
                          "sameTimeHighlights":[{"timeRange":"00:12","description":"同時刻比較"}],
                          "relinkDecisions":[{"workerId":"worker-01","visualMatchConfidence":0.7,"timeGapSeconds":4,"anchorProximityMeters":1.2,"mode":"OBSERVED"}]
                        }
                        """.trimIndent(),
                    "review_artifact_stub.json" to
                        """
                        {
                          "generatedBy":"LocalModelingService",
                          "viewerMode":"review-ready",
                          "supports3dgsControls":false,
                          "supportsSameTimeHighlights":true
                        }
                        """.trimIndent(),
                ),
            )

        val snapshot = service.loadSnapshot(input)

        assertEquals("0.88", snapshot.space.spaceQuality)
        assertEquals("0.77", snapshot.trajectory.trajectoryQuality)
        assertEquals("LocalModelingService", snapshot.artifact.generatedBy)
        assertEquals("補正対象 corridor", snapshot.space.weakArea)
    }

    private class InMemorySessionInput(
        private val files: Map<String, String>,
    ) : SessionInputReader {
        override fun exists(filename: String): Boolean = files.containsKey(filename)

        override fun readText(filename: String): String? = files[filename]
    }
}
