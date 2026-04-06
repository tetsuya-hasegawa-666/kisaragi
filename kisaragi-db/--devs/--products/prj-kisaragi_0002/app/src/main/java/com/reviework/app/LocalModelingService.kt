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
        val depthPointEstimate = (frames * (6.0 + completeness * 8.0)).roundToInt()
        val spaceQuality = formatScore(completeness * 0.55 + poseCoverage * 0.45)
        val trajectoryQuality = formatScore((poseCoverage * 0.65) + (workerCount.coerceAtMost(3) / 3.0 * 0.35))
        val routeProfiles = buildRouteProfiles(completeness, poseCoverage, frames, depthPointEstimate)
        val defaultRoute = routeProfiles.maxByOrNull { it.predictedQualityScore } ?: routeProfiles.first()

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

        val experimentManifest =
            JSONObject()
                .put("sessionId", sessionId)
                .put("specVersion", "2026-03-26")
                .put("executionMode", "colab_preflight")
                .put("baselineRouteId", defaultRoute.routeId)
                .put("uploadArtifacts", JSONArray(listOf("video.mp4", "session_package.json", "frame_pose_index.csv", "sensor_quality.json", "space_handoff_manifest.json", "camera_calibration_summary.json", "frame_record.jsonl", "trajectreview/image")))
                .put("routes", JSONArray(routeProfiles.map { it.toExperimentJson() }))

        val da3InputManifest =
            JSONObject()
                .put("sessionId", sessionId)
                .put("imageInputMode", "session_bundle_images")
                .put("frameSource", "trajectreview/image/")
                .put("frameIndexSource", "frame_pose_index.csv")
                .put("poseSource", "frame_record.jsonl")
                .put("intrinsicsSource", "camera_calibration_summary.json")
                .put("readyForRemoteExecution", blockers.isEmpty())
                .put(
                    "routes",
                    JSONArray(
                        routeProfiles.map {
                            JSONObject()
                                .put("routeId", it.routeId)
                                .put("samplingProfile", it.samplingProfile)
                                .put("intrinsicsMode", it.intrinsicsMode)
                                .put("projectionMode", it.projectionMode)
                                .put("modelId", "depth-anything/DA3NESTED-GIANT-LARGE-1.1")
                        },
                    ),
                )

        val depthEstimationReport =
            JSONObject()
                .put("sessionId", sessionId)
                .put("reportMode", "local_preflight_estimate")
                .put("readyForRemoteExecution", blockers.isEmpty())
                .put("routes", JSONArray(routeProfiles.map { it.toDepthReportJson(blockers) }))

        val benchmarkSummary =
            JSONObject()
                .put("sessionId", sessionId)
                .put("comparisonMode", "preflight_before_colab")
                .put("defaultRouteId", defaultRoute.routeId)
                .put("routes", JSONArray(routeProfiles.map { it.toBenchmarkJson() }))
                .put("comparisonFocus", JSONArray(listOf("depth_quality", "metric_scale_confidence", "runtime_minutes", "vram_gb", "failure_risk")))

        val selectedRoute =
            JSONObject()
                .put("sessionId", sessionId)
                .put("selectedRouteId", defaultRoute.routeId)
                .put("decisionStage", "preflight")
                .put("decisionReason", defaultRoute.selectionReason)
                .put("selectedRoute", defaultRoute.toSelectedRouteJson())
                .put("researchRoutes", JSONArray(routeProfiles.filter { it.routeId != defaultRoute.routeId }.map { it.toResearchRouteJson() }))
                .put("reevaluateWhen", JSONArray(listOf("admin UX check で fail が出た時", "Colab 実測値が preflight 推定を下回った時", "新しい DA3 sampling profile を追加した時")))

        val colabRequest =
            JSONObject()
                .put("sessionId", sessionId)
                .put("targetEngine", "colab_da3nested_giant_large")
                .put("accountStatus", "pending_admin_account")
                .put("localVerification", "pass")
                .put("requiredUploadArtifacts", JSONArray(listOf("video.mp4", "session_package.json", "frame_pose_index.csv", "sensor_quality.json", "space_handoff_manifest.json", "camera_calibration_summary.json", "frame_record.jsonl", "trajectreview/image")))
                .put("recommendedNotebookId", "trajectreview-da3nested-giant-large")
                .put("recommendedNotebookPath", "colab/da3_ngl_runbook.ipynb")
                .put("defaultRouteId", defaultRoute.routeId)
                .put("routeIds", JSONArray(routeProfiles.map { it.routeId }))
                .put(
                    "runtimeContract",
                    JSONObject()
                        .put("modelId", "depth-anything/DA3NESTED-GIANT-LARGE-1.1")
                        .put("poseBackend", "ARCore_pose")
                        .put("depthBackend", "DA3NESTED-GIANT-LARGE-1.1")
                        .put("intrinsicsMode", "per_frame_or_session"),
                )
                .put(
                    "resultArtifacts",
                    JSONArray(
                        listOf(
                            "depth_estimation_report.json",
                            "benchmark_summary.json",
                            "selected_route.json",
                            "space_quality.json",
                            "trajectory_quality.json",
                            "attention_seed.json",
                        ),
                    ),
                )
                .put("nextAction", if (blockers.isEmpty()) "Colab に upload して route 比較を実行する" else "correcting app へ戻って blocker を解消する")

        val localModelSummary =
            JSONObject()
                .put("sessionId", sessionId)
                .put("executionMode", "local_sample_before_colab")
                .put("defaultRouteId", defaultRoute.routeId)
                .put("modeledFrames", frames)
                .put("workerPathCount", workerCount)
                .put("poseCoverageRatio", poseCoverage)
                .put("localSparsePointEstimate", sparsePointEstimate)
                .put("localDepthPointEstimate", depthPointEstimate)
                .put("spaceQuality", spaceQuality)
                .put("trajectoryQuality", trajectoryQuality)
                .put("weakArea", blockers.firstOrNull() ?: "Colab 送信前の軽量 sample では pose と intrinsics の整合確認が必要")
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
                .put("readyForColab", blockers.isEmpty())
                .put("selectedRouteId", defaultRoute.routeId)
                .put("blockers", JSONArray(blockers))
                .put("nextAction", if (blockers.isEmpty()) "Colab route 実行後に result import して reviewing app で結果を開く" else "correcting app へ戻って blocker を解消する")

        val files =
            listOf(
                "modeling/experiment_manifest.json" to experimentManifest.toString(2),
                "modeling/da3_input_manifest.json" to da3InputManifest.toString(2),
                "modeling/depth_estimation_report.json" to depthEstimationReport.toString(2),
                "modeling/benchmark_summary.json" to benchmarkSummary.toString(2),
                "modeling/selected_route.json" to selectedRoute.toString(2),
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

    private fun buildRouteProfiles(
        completeness: Double,
        poseCoverage: Double,
        frames: Int,
        depthPointEstimate: Int,
    ): List<RouteProfile> =
        listOf(
            RouteProfile(
                routeId = "route-da3nested-giant-large-5fps-static-intrinsics",
                samplingProfile = "5fps",
                intrinsicsMode = "session_fixed",
                projectionMode = "depth_to_world_pointcloud",
                predictedMetricScaleConfidence = 0.72 + completeness * 0.12,
                predictedDepthContinuity = 0.74 + poseCoverage * 0.14,
                predictedPointCount = (depthPointEstimate * 0.76).roundToInt(),
                predictedRuntimeMinutes = 9 + frames / 30,
                predictedVramGb = 11.0,
                predictedQualityScore = 0.72 + completeness * 0.11 + poseCoverage * 0.08,
                selectionReason = "5fps は Colab 負荷が軽く、DA3NESTED-GIANT-LARGE-1.1 の初回検証に向く",
            ),
            RouteProfile(
                routeId = "route-da3nested-giant-large-10fps-static-intrinsics",
                samplingProfile = "10fps",
                intrinsicsMode = "session_fixed",
                projectionMode = "depth_to_world_pointcloud",
                predictedMetricScaleConfidence = 0.76 + completeness * 0.11,
                predictedDepthContinuity = 0.78 + poseCoverage * 0.13,
                predictedPointCount = depthPointEstimate,
                predictedRuntimeMinutes = 12 + frames / 24,
                predictedVramGb = 13.0,
                predictedQualityScore = 0.76 + completeness * 0.12 + poseCoverage * 0.10,
                selectionReason = "10fps は review 用の空間密度と Colab 負荷のバランスがよい",
            ),
            RouteProfile(
                routeId = "route-da3nested-giant-large-10fps-per-frame-intrinsics",
                samplingProfile = "10fps",
                intrinsicsMode = "per_frame",
                projectionMode = "depth_to_world_pointcloud",
                predictedMetricScaleConfidence = 0.80 + completeness * 0.10,
                predictedDepthContinuity = 0.81 + poseCoverage * 0.12,
                predictedPointCount = (depthPointEstimate * 1.08).roundToInt(),
                predictedRuntimeMinutes = 14 + frames / 22,
                predictedVramGb = 14.0,
                predictedQualityScore = 0.80 + completeness * 0.11 + poseCoverage * 0.11,
                selectionReason = "per-frame intrinsics が使えるならこの route を暫定採用候補にする",
            ),
        )
}

private data class RouteProfile(
    val routeId: String,
    val samplingProfile: String,
    val intrinsicsMode: String,
    val projectionMode: String,
    val predictedMetricScaleConfidence: Double,
    val predictedDepthContinuity: Double,
    val predictedPointCount: Int,
    val predictedRuntimeMinutes: Int,
    val predictedVramGb: Double,
    val predictedQualityScore: Double,
    val selectionReason: String,
) {
    fun toExperimentJson(): JSONObject =
        JSONObject()
            .put("routeId", routeId)
            .put("samplingProfile", samplingProfile)
            .put("poseBackend", JSONObject().put("engine", "ARCore").put("mode", "recorded_pose"))
            .put("depthBackend", JSONObject().put("engine", "DA3NESTED-GIANT-LARGE-1.1").put("intrinsicsMode", intrinsicsMode))
            .put("projectionMode", projectionMode)
            .put("resourceBudget", JSONObject().put("runtimeMinutes", predictedRuntimeMinutes).put("vramGb", predictedVramGb))

    fun toDepthReportJson(blockers: List<String>): JSONObject =
        JSONObject()
            .put("routeId", routeId)
            .put("status", if (blockers.isEmpty()) "ready_for_remote_execution" else "blocked_before_remote_execution")
            .put("metricScaleConfidence", formatRatio(predictedMetricScaleConfidence))
            .put("depthContinuity", formatValue(predictedDepthContinuity))
            .put("pointCountEstimate", predictedPointCount)
            .put("failureReason", blockers.firstOrNull() ?: JSONObject.NULL)

    fun toBenchmarkJson(): JSONObject =
        JSONObject()
            .put("routeId", routeId)
            .put("samplingProfile", samplingProfile)
            .put("intrinsicsMode", intrinsicsMode)
            .put("projectionMode", projectionMode)
            .put("predictedQualityScore", formatValue(predictedQualityScore))
            .put("predictedRuntimeMinutes", predictedRuntimeMinutes)
            .put("predictedVramGb", predictedVramGb)
            .put("predictedFailureRisk", formatValue(1.0 - predictedMetricScaleConfidence))

    fun toSelectedRouteJson(): JSONObject =
        JSONObject()
            .put("routeId", routeId)
            .put("samplingProfile", samplingProfile)
            .put("intrinsicsMode", intrinsicsMode)
            .put("projectionMode", projectionMode)
            .put("selectionReason", selectionReason)

    fun toResearchRouteJson(): JSONObject =
        JSONObject()
            .put("routeId", routeId)
            .put("samplingProfile", samplingProfile)
            .put("intrinsicsMode", intrinsicsMode)
            .put("reason", "比較継続のため保持する")

    private fun formatRatio(value: Double): Double = formatValue(value.coerceIn(0.0, 0.99))

    private fun formatValue(value: Double): Double = "%.3f".format(value).toDouble()
}
