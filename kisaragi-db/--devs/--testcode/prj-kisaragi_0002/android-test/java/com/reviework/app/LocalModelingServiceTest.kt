package com.reviework.app

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class LocalModelingServiceTest {

    private val service = LocalModelingService()

    @Test
    fun runWritesColabRequestAndReviewStub() {
        val input =
            InMemorySessionInput(
                mapOf(
                    "session_package.json" to
                        """
                        {
                          "sessionId":"session-modeling",
                          "streamCounts":{"frames":120},
                          "scores":{"completenessScore":0.95,"poseCoverageRatio":0.6}
                        }
                        """.trimIndent(),
                    "sensor_quality.json" to """{"scores":{"completenessScore":0.95,"poseCoverageRatio":0.6}}""",
                    "space_handoff_manifest.json" to """{"readyForSpaceReconstruction":true,"blockers":[]}""",
                    "member_identity_map.json" to """{"members":[{"memberId":"main_capture"},{"memberId":"worker-01"}]}""",
                ),
            )
        val output = InMemorySessionOutput()

        val result = service.run(input, output)

        assertEquals("session-modeling", result.sessionId)
        assertTrue(result.reviewReady)
        assertTrue(output.files.containsKey("modeling/colab_job_request.json"))
        assertTrue(output.files.containsKey("modeling/local_model_summary.json"))
        assertTrue(output.files.containsKey("modeling/review_artifact_stub.json"))
        val colab = JSONObject(output.files.getValue("modeling/colab_job_request.json"))
        assertEquals("colab_3dgs", colab.getString("targetEngine"))
    }

    @Test
    fun runKeepsBlockerWhenSpaceHandoffIsNotReady() {
        val input =
            InMemorySessionInput(
                mapOf(
                    "session_package.json" to """{"sessionId":"blocked","streamCounts":{"frames":40},"scores":{"completenessScore":0.5,"poseCoverageRatio":0.2}}""",
                    "sensor_quality.json" to """{"scores":{"completenessScore":0.5,"poseCoverageRatio":0.2}}""",
                    "space_handoff_manifest.json" to """{"readyForSpaceReconstruction":false,"blockers":["video.mp4 が不足している"]}""",
                    "member_identity_map.json" to """{"members":[{"memberId":"main_capture"},{"memberId":"worker-01"}]}""",
                ),
            )
        val output = InMemorySessionOutput()

        val result = service.run(input, output)
        val reviewStub = JSONObject(output.files.getValue("modeling/review_artifact_stub.json"))

        assertTrue(result.blockers.contains("video.mp4 が不足している"))
        assertTrue(!result.reviewReady)
        assertTrue(!reviewStub.getBoolean("reviewReady"))
    }

    private class InMemorySessionInput(
        private val files: Map<String, String>,
    ) : SessionInputReader {
        override fun exists(filename: String): Boolean = files.containsKey(filename)

        override fun readText(filename: String): String? = files[filename]
    }

    private class InMemorySessionOutput : SessionOutputWriter {
        val files = linkedMapOf<String, String>()

        override fun writeText(relativePath: String, content: String) {
            files[relativePath] = content
        }

        override fun writeBytes(relativePath: String, content: ByteArray) {
            files[relativePath] = content.toString(Charsets.UTF_8)
        }
    }
}
