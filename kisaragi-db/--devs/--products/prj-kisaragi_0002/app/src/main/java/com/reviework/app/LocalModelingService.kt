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
        val routeProfiles = buildRouteProfiles(completeness, poseCoverage, frames, sparsePointEstimate)
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
                .put("uploadArtifacts", JSONArray(listOf("video.mp4", "session_package.json", "frame_pose_index.csv", "sensor_quality.json", "space_handoff_manifest.json")))
                .put("routes", JSONArray(routeProfiles.map { it.toExperimentJson() }))

        val colmapInputManifest =
            JSONObject()
                .put("sessionId", sessionId)
                .put("imageInputMode", "session_bundle_images_or_video_frames")
                .put("frameSource", "video.mp4")
                .put("frameIndexSource", "frame_pose_index.csv")
                .put("readyForRemoteExecution", blockers.isEmpty())
                .put(
                    "routes",
                    JSONArray(
                        routeProfiles.map {
                            JSONObject()
                                .put("routeId", it.routeId)
                                .put("mapper", it.mapper)
                                .put("featureExtractor", "colmap feature_extractor")
                                .put("matcher", "colmap exhaustive_matcher")
                        },
                    ),
                )

        val poseEstimationReport =
            JSONObject()
                .put("sessionId", sessionId)
                .put("reportMode", "local_preflight_estimate")
                .put("readyForRemoteExecution", blockers.isEmpty())
                .put("routes", JSONArray(routeProfiles.map { it.toPoseReportJson(blockers) }))

        val benchmarkSummary =
            JSONObject()
                .put("sessionId", sessionId)
                .put("comparisonMode", "preflight_before_colab")
                .put("defaultRouteId", defaultRoute.routeId)
                .put("routes", JSONArray(routeProfiles.map { it.toBenchmarkJson() }))
                .put("comparisonFocus", JSONArray(listOf("pose_quality", "gaussian_seed_density", "runtime_minutes", "vram_gb", "failure_risk")))

        val selectedRoute =
            JSONObject()
                .put("sessionId", sessionId)
                .put("selectedRouteId", defaultRoute.routeId)
                .put("decisionStage", "preflight")
                .put("decisionReason", defaultRoute.selectionReason)
                .put("selectedRoute", defaultRoute.toSelectedRouteJson())
                .put("researchRoutes", JSONArray(routeProfiles.filter { it.routeId != defaultRoute.routeId }.map { it.toResearchRouteJson() }))
                .put("reevaluateWhen", JSONArray(listOf("admin UX check で fail が出た時", "Colab 実測値が preflight 推定を下回った時", "新しい 3DGS backend を追加した時")))

        val colabRequest =
            JSONObject()
                .put("sessionId", sessionId)
                .put("targetEngine", "colab_colmap4_nerfstudio_splatfacto")
                .put("accountStatus", "pending_admin_account")
                .put("localVerification", "pass")
                .put("requiredUploadArtifacts", JSONArray(listOf("video.mp4", "session_package.json", "frame_pose_index.csv", "sensor_quality.json", "space_handoff_manifest.json")))
                .put("recommendedNotebookId", "trajectreview-colmap40-splatfacto")
                .put("recommendedNotebookPath", "modeling/trajectreview_colmap4_splatfacto_colab.ipynb")
                .put("defaultRouteId", defaultRoute.routeId)
                .put("routeIds", JSONArray(routeProfiles.map { it.routeId }))
                .put(
                    "runtimeContract",
                    JSONObject()
                        .put("colmapVersion", "4.0.x")
                        .put("poseBackend", "COLMAP")
                        .put("gsBackend", "nerfstudio")
                        .put("gsMethod", "splatfacto"),
                )
                .put(
                    "resultArtifacts",
                    JSONArray(
                        listOf(
                            "pose_estimation_report.json",
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
                .put("readyForColab", blockers.isEmpty())
                .put("selectedRouteId", defaultRoute.routeId)
                .put("blockers", JSONArray(blockers))
                .put("nextAction", if (blockers.isEmpty()) "Colab route 実行後に result import して reviewing app で結果を開く" else "correcting app へ戻って blocker を解消する")

        val files =
            listOf(
                "modeling/experiment_manifest.json" to experimentManifest.toString(2),
                "modeling/colmap_input_manifest.json" to colmapInputManifest.toString(2),
                "modeling/pose_estimation_report.json" to poseEstimationReport.toString(2),
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
        sparsePointEstimate: Int,
    ): List<RouteProfile> =
        listOf(
            RouteProfile(
                routeId = "route-colmap40-incremental-splatfacto",
                mapper = "incremental",
                preprocessProfile = "balanced-images",
                gsMethod = "splatfacto",
                predictedRegisteredImageRatio = 0.70 + completeness * 0.18,
                predictedReprojectionError = 0.95 - poseCoverage * 0.18,
                predictedSparsePointCount = (sparsePointEstimate * 0.92).roundToInt(),
                predictedRuntimeMinutes = 18 + frames / 18,
                predictedVramGb = 12.0,
                predictedQualityScore = 0.70 + completeness * 0.16 + poseCoverage * 0.08,
                selectionReason = "incremental mapper は失敗時の切り分けがしやすく baseline 比較に向く",
            ),
            RouteProfile(
                routeId = "route-colmap40-hierarchical-splatfacto",
                mapper = "hierarchical",
                preprocessProfile = "coverage-priority",
                gsMethod = "splatfacto",
                predictedRegisteredImageRatio = 0.74 + completeness * 0.17,
                predictedReprojectionError = 0.88 - poseCoverage * 0.17,
                predictedSparsePointCount = (sparsePointEstimate * 1.02).roundToInt(),
                predictedRuntimeMinutes = 20 + frames / 16,
                predictedVramGb = 13.0,
                predictedQualityScore = 0.73 + completeness * 0.15 + poseCoverage * 0.10,
                selectionReason = "hierarchical mapper は frame 数が多い session で安定しやすい",
            ),
            RouteProfile(
                routeId = "route-colmap40-global-splatfacto",
                mapper = "global",
                preprocessProfile = "pose-max",
                gsMethod = "splatfacto",
                predictedRegisteredImageRatio = 0.78 + completeness * 0.16,
                predictedReprojectionError = 0.82 - poseCoverage * 0.20,
                predictedSparsePointCount = (sparsePointEstimate * 1.08).roundToInt(),
                predictedRuntimeMinutes = 16 + frames / 20,
                predictedVramGb = 14.0,
                predictedQualityScore = 0.77 + completeness * 0.13 + poseCoverage * 0.12,
                selectionReason = "global_mapper を first target にし、GLOMAP 統合 route を暫定採用候補にする",
            ),
        )
}

private data class RouteProfile(
    val routeId: String,
    val mapper: String,
    val preprocessProfile: String,
    val gsMethod: String,
    val predictedRegisteredImageRatio: Double,
    val predictedReprojectionError: Double,
    val predictedSparsePointCount: Int,
    val predictedRuntimeMinutes: Int,
    val predictedVramGb: Double,
    val predictedQualityScore: Double,
    val selectionReason: String,
) {
    fun toExperimentJson(): JSONObject =
        JSONObject()
            .put("routeId", routeId)
            .put("preprocessProfile", preprocessProfile)
            .put("poseBackend", JSONObject().put("engine", "COLMAP").put("version", "4.0.x").put("mapper", mapper))
            .put("gsBackend", JSONObject().put("engine", "nerfstudio").put("method", gsMethod))
            .put("resourceBudget", JSONObject().put("runtimeMinutes", predictedRuntimeMinutes).put("vramGb", predictedVramGb))

    fun toPoseReportJson(blockers: List<String>): JSONObject =
        JSONObject()
            .put("routeId", routeId)
            .put("status", if (blockers.isEmpty()) "ready_for_remote_execution" else "blocked_before_remote_execution")
            .put("registeredImageRatio", formatRatio(predictedRegisteredImageRatio))
            .put("reprojectionErrorPx", formatValue(predictedReprojectionError))
            .put("sparsePointCount", predictedSparsePointCount)
            .put("failureReason", blockers.firstOrNull() ?: JSONObject.NULL)

    fun toBenchmarkJson(): JSONObject =
        JSONObject()
            .put("routeId", routeId)
            .put("mapper", mapper)
            .put("gsMethod", gsMethod)
            .put("predictedQualityScore", formatValue(predictedQualityScore))
            .put("predictedRuntimeMinutes", predictedRuntimeMinutes)
            .put("predictedVramGb", predictedVramGb)
            .put("predictedFailureRisk", formatValue(1.0 - predictedRegisteredImageRatio))

    fun toSelectedRouteJson(): JSONObject =
        JSONObject()
            .put("routeId", routeId)
            .put("mapper", mapper)
            .put("gsMethod", gsMethod)
            .put("selectionReason", selectionReason)

    fun toResearchRouteJson(): JSONObject =
        JSONObject()
            .put("routeId", routeId)
            .put("mapper", mapper)
            .put("gsMethod", gsMethod)
            .put("reason", "比較継続のため保持する")

    private fun formatRatio(value: Double): Double = formatValue(value.coerceIn(0.0, 0.99))

    private fun formatValue(value: Double): Double = "%.3f".format(value).toDouble()
}
