package com.reviework.app

import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.roundToInt

data class LocalModelingResult(
    val sessionId: String,
    val reviewReady: Boolean,
    val blockers: List<String>,
    val outputFiles: List<String>,
    val spaceQuality: String,
    val trajectoryQuality: String,
)

class LocalModelingService {

    fun run(source: SessionInputReader, output: SessionOutputWriter): LocalModelingResult {
        val sessionPackageText = source.readText("session_package.json")
            ?: throw IllegalArgumentException("session_package.json が見つかりません。")
        val qualityText = source.readText("sensor_quality.json")
            ?: throw IllegalArgumentException("sensor_quality.json が見つかりません。")
        val handoffText = source.readText("space_handoff_manifest.json")
            ?: throw IllegalArgumentException("space_handoff_manifest.json が見つかりません。")
        val identityText = source.readText("member_identity_map.json") ?: "{}"

        val sessionPackage = JSONObject(sessionPackageText)
        val quality = JSONObject(qualityText)
        val handoff = JSONObject(handoffText)
        val identity = JSONObject(identityText)
        val sessionId = sessionPackage.optString("sessionId").ifBlank { "unknown-session" }
        val scores = sessionPackage.optJSONObject("scores") ?: quality.optJSONObject("scores") ?: JSONObject()
        val streamCounts = sessionPackage.optJSONObject("streamCounts") ?: JSONObject()
        val members = identity.optJSONArray("members") ?: JSONArray()
        val blockers = mutableListOf<String>()

        if (!handoff.optBoolean("readyForSpaceReconstruction", false)) {
            blockers += jsonArrayToList(handoff.optJSONArray("blockers"))
        }

        val frames = streamCounts.optInt("frames", 0)
        val completeness = scores.optDouble("completenessScore", 0.0)
        val poseCoverage = scores.optDouble("poseCoverageRatio", 0.0)
        val workerCount = (members.length() - 1).coerceAtLeast(1)
        val sparsePointEstimate = (frames * (14.0 + poseCoverage * 12.0)).roundToInt()
        val gaussianSeedEstimate = (frames * (4.0 + completeness * 6.0)).roundToInt()
        val spaceQuality = formatScore(completeness * 0.55 + poseCoverage * 0.45)
        val trajectoryQuality = formatScore((poseCoverage * 0.65) + (workerCount.coerceAtMost(3) / 3.0 * 0.35))

        val attentionPoints =
            buildList {
                if (poseCoverage < 0.5) {
                    add(JSONObject().put("timeRange", "00:00-00:10").put("reason", "pose coverage が低く、Colab 実行前に補正確認が必要"))
                }
                if (completeness < 1.0) {
                    add(JSONObject().put("timeRange", "00:10-00:20").put("reason", "必須入力の欠落または stream 数不足があります"))
                }
                blockers.forEachIndexed { index, blocker ->
                    add(JSONObject().put("timeRange", "blocker-${index + 1}").put("reason", blocker))
                }
            }

        val sameTimeHighlights =
            JSONArray().apply {
                if (workerCount > 0 && frames > 0) {
                    put(JSONObject().put("timeRange", "00:05").put("description", "主カメラと worker-01 の位置比較を Colab 送信前に確認"))
                }
                if (workerCount > 1) {
                    put(JSONObject().put("timeRange", "00:12").put("description", "worker-02 を含む multi-person 区間を重点 review"))
                }
            }

        val relinkDecisions =
            JSONArray().apply {
                put(
                    JSONObject()
                        .put("workerId", "worker-01")
                        .put("visualMatchConfidence", formatDouble(poseCoverage * 0.8 + 0.1))
                        .put("timeGapSeconds", 6)
                        .put("anchorProximityMeters", formatDouble(1.2 + (1.0 - poseCoverage) * 4.0))
                        .put("mode", if (poseCoverage >= 0.55) "RELINKED" else "BRIDGED"),
                )
            }

        val colabRequest =
            JSONObject()
                .put("sessionId", sessionId)
                .put("targetEngine", "colab_3dgs")
                .put("accountStatus", "pending_admin_account")
                .put("localVerification", "pass")
                .put("requiredUploadArtifacts", JSONArray(listOf("video.mp4", "session_package.json", "frame_pose_index.csv", "sensor_quality.json")))
                .put("recommendedNotebook", "gaussian-splatting-colab")
                .put("nextAction", "Colab アカウント取得後に upload と remote 実行へ切り替える")

        val localModelSummary =
            JSONObject()
                .put("sessionId", sessionId)
                .put("executionMode", "local_sample_before_colab")
                .put("modeledFrames", frames)
                .put("workerPathCount", workerCount)
                .put("poseCoverageRatio", poseCoverage)
                .put("localSparsePointEstimate", sparsePointEstimate)
                .put("localGaussianSeedEstimate", gaussianSeedEstimate)
                .put("spaceQuality", spaceQuality)
                .put("trajectoryQuality", trajectoryQuality)
                .put("weakArea", blockers.firstOrNull() ?: "Colab 送信前の軽量 sample では局所 coverage の再確認が必要")
                .put("attentionPoints", JSONArray(attentionPoints))
                .put("sameTimeHighlights", sameTimeHighlights)
                .put("relinkDecisions", relinkDecisions)

        val reviewArtifactStub =
            JSONObject()
                .put("sessionId", sessionId)
                .put("generatedBy", "LocalModelingService")
                .put("viewerMode", "review-ready")
                .put("supports3dgsControls", false)
                .put("supportsSameTimeHighlights", true)
                .put("reviewReady", blockers.isEmpty())

        val modelingHandoff =
            JSONObject()
                .put("sessionId", sessionId)
                .put("targetStage", "Reviewing")
                .put("readyForReviewing", blockers.isEmpty())
                .put("blockers", JSONArray(blockers))
                .put("nextAction", if (blockers.isEmpty()) "reviewing app で結果を開く" else "correcting app へ戻って blocker を解消する")

        val files =
            listOf(
                "modeling/colab_job_request.json" to colabRequest.toString(2),
                "modeling/local_model_summary.json" to localModelSummary.toString(2),
                "modeling/review_artifact_stub.json" to reviewArtifactStub.toString(2),
                "modeling/modeling_handoff_manifest.json" to modelingHandoff.toString(2),
            )

        files.forEach { (relativePath, content) ->
            output.writeText(relativePath, content)
        }

        return LocalModelingResult(
            sessionId = sessionId,
            reviewReady = blockers.isEmpty(),
            blockers = blockers,
            outputFiles = files.map { it.first },
            spaceQuality = spaceQuality,
            trajectoryQuality = trajectoryQuality,
        )
    }

    private fun jsonArrayToList(source: JSONArray?): List<String> {
        if (source == null) {
            return emptyList()
        }
        return List(source.length()) { index -> source.optString(index) }.filter { it.isNotBlank() }
    }

    private fun formatScore(value: Double): String = "%.2f".format(value.coerceIn(0.0, 1.0))

    private fun formatDouble(value: Double): Double = "%.3f".format(value).toDouble()
}
