package com.reviework.app

import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.roundToInt

class WorkflowBundleService {

    fun loadSnapshot(source: SessionInputReader): ReviewContractSnapshot {
        val sessionPackage = source.readText("session_package.json")?.let(::JSONObject)
        val quality = source.readText("sensor_quality.json")?.let(::JSONObject)
        val handoff = source.readText("space_handoff_manifest.json")?.let(::JSONObject)
        val identityMap = source.readText("member_identity_map.json")?.let(::JSONObject)
        val localModel = source.readText("local_model_summary.json")?.let(::JSONObject)
        val reviewArtifact = source.readText("review_artifact_stub.json")?.let(::JSONObject)

        if (sessionPackage == null && localModel == null) {
            throw IllegalArgumentException("trajectreview bundle が見つかりません。")
        }

        val streamCounts = sessionPackage?.optJSONObject("streamCounts") ?: JSONObject()
        val scores = sessionPackage?.optJSONObject("scores") ?: quality?.optJSONObject("scores") ?: JSONObject()
        val requiredInputs = sessionPackage?.optJSONObject("requiredInputs") ?: JSONObject()
        val optionalInputs = sessionPackage?.optJSONObject("optionalInputs") ?: JSONObject()
        val qualityFlags = quality?.optJSONObject("qualityFlags") ?: JSONObject()
        val blockers = jsonArrayToList(handoff?.optJSONArray("blockers"))
        val members = identityMap?.optJSONArray("members")
        val memberCount = (members?.length() ?: 1).coerceAtLeast(1)
        val workerCount = (memberCount - 1).coerceAtLeast(1)
        val frames = streamCounts.optInt("frames", localModel?.optInt("modeledFrames") ?: 0)
        val completeness = scores.optDouble("completenessScore", 0.0)
        val poseCoverage = scores.optDouble("poseCoverageRatio", localModel?.optDouble("poseCoverageRatio", 0.0) ?: 0.0)
        val tracking =
            when {
                qualityFlags.optBoolean("hasPoseTimeline") && poseCoverage >= 0.75 -> "good"
                poseCoverage >= 0.35 -> "partial"
                else -> "limited"
            }
        val workerVisibility =
            when {
                workerCount >= 2 && poseCoverage >= 0.5 -> WorkerVisibility.SUFFICIENT
                workerCount >= 1 -> WorkerVisibility.PARTIAL
                else -> WorkerVisibility.INSUFFICIENT
            }
        val defaultAttentionPoints =
            buildList {
                if (poseCoverage < 0.5) {
                    add(AttentionPoint("00:00-00:08", "pose coverage が低いため再拘束確認が必要"))
                }
                blockers.forEachIndexed { index, blocker ->
                    add(AttentionPoint("blocker-${index + 1}", blocker))
                }
            }
        val defaultHighlights =
            if (workerCount > 0 && frames > 0) {
                listOf(TimelineHighlight("00:05", "主カメラと worker-01 の同時刻比較を確認"))
            } else {
                emptyList()
            }

        return ReviewContractSnapshot(
            intake =
                SessionIntakeReport(
                    frames = frames,
                    usableFrames = (frames * completeness).roundToInt(),
                    tracking = tracking,
                    mainVideoReady = requiredInputs.optBoolean("video", false),
                    mainImuReady = requiredInputs.optBoolean("imu", false),
                    workerImuDeviceCount = workerCount,
                    workerVisibility = workerVisibility,
                    optionalPoseReady = optionalInputs.optBoolean("poses", false),
                    optionalGnssReady = optionalInputs.optBoolean("gnss", false),
                ),
            space =
                SpaceReviewSummary(
                    coordinateSystem = sessionPackage?.optJSONObject("timebase")?.let { "elapsedRealtimeNanos" } ?: "unknown",
                    mainCameraPathReady = poseCoverage > 0.0,
                    colmapReadyForDensification = handoff?.optBoolean("readyForSpaceReconstruction", false) ?: false,
                    spaceQuality =
                        localModel?.optString("spaceQuality")?.ifBlank { null }
                            ?: formatScore(completeness * 0.6 + poseCoverage * 0.4),
                    weakArea =
                        localModel?.optString("weakArea")?.ifBlank { null }
                            ?: blockers.firstOrNull(),
                ),
            trajectory =
                TrajectoryReviewSummary(
                    workerPathCount = localModel?.optInt("workerPathCount") ?: workerCount,
                    trajectoryQuality =
                        localModel?.optString("trajectoryQuality")?.ifBlank { null }
                            ?: formatScore((completeness + poseCoverage) / 2.0),
                    relinkDecisions = loadRelinkDecisions(localModel?.optJSONArray("relinkDecisions")),
                    attentionPoints = loadAttentionPoints(localModel?.optJSONArray("attentionPoints"), defaultAttentionPoints),
                    sameTimeHighlights = loadHighlights(localModel?.optJSONArray("sameTimeHighlights"), defaultHighlights),
                ),
            artifact =
                ReviewArtifactSummary(
                    generatedBy = reviewArtifact?.optString("generatedBy").orEmpty().ifBlank { "InputPackaging" },
                    viewerMode = reviewArtifact?.optString("viewerMode").orEmpty().ifBlank { "status-only" },
                    supports3dgsControls = reviewArtifact?.optBoolean("supports3dgsControls") ?: false,
                    supportsSameTimeHighlights = reviewArtifact?.optBoolean("supportsSameTimeHighlights")
                        ?: (localModel != null),
                ),
        )
    }

    private fun loadAttentionPoints(source: JSONArray?, fallback: List<AttentionPoint>): List<AttentionPoint> {
        if (source == null || source.length() == 0) {
            return fallback
        }
        return List(source.length()) { index ->
            val item = source.getJSONObject(index)
            AttentionPoint(
                timeRange = item.optString("timeRange", "unknown"),
                reason = item.optString("reason", "理由なし"),
            )
        }
    }

    private fun loadHighlights(source: JSONArray?, fallback: List<TimelineHighlight>): List<TimelineHighlight> {
        if (source == null || source.length() == 0) {
            return fallback
        }
        return List(source.length()) { index ->
            val item = source.getJSONObject(index)
            TimelineHighlight(
                timeRange = item.optString("timeRange", "unknown"),
                description = item.optString("description", "説明なし"),
            )
        }
    }

    private fun loadRelinkDecisions(source: JSONArray?): List<RelinkDecision> {
        if (source == null || source.length() == 0) {
            return listOf(RelinkDecision("worker-01", 0.40, 6, 2.0, RelinkMode.RELINKED))
        }
        return List(source.length()) { index ->
            val item = source.getJSONObject(index)
            RelinkDecision(
                workerId = item.optString("workerId", "worker-${index + 1}"),
                visualMatchConfidence = item.optDouble("visualMatchConfidence", 0.0),
                timeGapSeconds = item.optInt("timeGapSeconds", 0),
                anchorProximityMeters = item.optDouble("anchorProximityMeters", 0.0),
                mode =
                    when (item.optString("mode").uppercase()) {
                        "OBSERVED" -> RelinkMode.OBSERVED
                        "BRIDGED" -> RelinkMode.BRIDGED
                        "LOST" -> RelinkMode.LOST
                        else -> RelinkMode.RELINKED
                    },
            )
        }
    }

    private fun jsonArrayToList(source: JSONArray?): List<String> {
        if (source == null) {
            return emptyList()
        }
        return List(source.length()) { index -> source.optString(index) }.filter { it.isNotBlank() }
    }

    private fun formatScore(value: Double): String = "%.2f".format(value.coerceIn(0.0, 1.0))
}
