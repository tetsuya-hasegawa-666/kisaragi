package com.isensorium.app

import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import kotlin.math.abs
import kotlin.math.min

data class CorrectingDataCheckResult(
    val sessionId: String,
    val derivedDir: File,
    val readyForDiagnose: Boolean,
    val readyForSpaceReconstruction: Boolean,
    val allowModelingProceed: Boolean,
    val missingRequiredInputs: List<String>,
    val completenessScore: Double,
    val poseCoverageRatio: Double,
    val blockers: List<String>,
    val recommendedCorrections: List<String>,
)

class CorrectingDataCheckService {

    fun run(sessionDir: File): CorrectingDataCheckResult {
        val parsed = parse(sessionDir)
        val derivedDir = File(sessionDir, "trajectreview").apply { mkdirs() }

        File(derivedDir, "input_readiness.json").writeText(buildInputReadinessJson(parsed))
        File(derivedDir, "sensor_quality.json").writeText(buildSensorQualityJson(parsed))
        File(derivedDir, "frame_pose_index.csv").writeText(buildFramePoseIndexCsv(parsed))
        File(derivedDir, "member_identity_map.json").writeText(buildMemberIdentityMapJson(parsed))
        File(derivedDir, "session_package.json").writeText(buildSessionPackageJson(parsed))
        File(derivedDir, "space_handoff_manifest.json").writeText(buildSpaceHandoffManifestJson(parsed))

        return CorrectingDataCheckResult(
            sessionId = parsed.sessionId,
            derivedDir = derivedDir,
            readyForDiagnose = parsed.missingRequiredInputs.isEmpty(),
            readyForSpaceReconstruction = parsed.spaceReconstructionBlockers.isEmpty(),
            allowModelingProceed = true,
            missingRequiredInputs = parsed.missingRequiredInputs,
            completenessScore = parsed.completenessScore,
            poseCoverageRatio = parsed.poseCoverageRatio,
            blockers = parsed.spaceReconstructionBlockers,
            recommendedCorrections = parsed.recommendedCorrections,
        )
    }

    private fun parse(sessionDir: File): ParsedSession {
        require(sessionDir.isDirectory) { "session directory が見つかりません。" }

        val manifestFile = firstExistingFile(sessionDir, listOf("session_manifest.json", "manifest.json"))
            ?: throw IllegalArgumentException("manifest file が見つかりません。")
        val manifest = JSONObject(manifestFile.readText())
        val sessionId = manifest.optString("sessionId").ifBlank { sessionDir.name }
        val timebase = manifest.optJSONObject("timebase") ?: JSONObject()

        val frameSelection = loadFirstAvailable(sessionDir, listOf("video_frame_timestamps.csv", "frames.csv"))
        val imuSelection = loadFirstAvailable(sessionDir, listOf("imu.csv"))
        val gnssSelection = loadFirstAvailable(sessionDir, listOf("gnss.csv"))
        val btSelection = loadFirstAvailable(sessionDir, listOf("bt.jsonl", "ble_scan.jsonl", "bt_events.csv", "bt.csv"))
        val poseSelection = loadFirstAvailable(sessionDir, listOf("poses.jsonl", "arcore_pose.jsonl", "arcore_pose.csv"))
        val videoFile = File(sessionDir, "video.mp4").takeIf { it.exists() }
        val videoEventsFile = File(sessionDir, "video_events.jsonl").takeIf { it.exists() }

        val frameRows = frameSelection?.rows ?: emptyList()
        val imuRows = imuSelection?.rows ?: emptyList()
        val gnssRows = gnssSelection?.rows ?: emptyList()
        val btRows = btSelection?.rows ?: emptyList()
        val poseRows = poseSelection?.rows ?: emptyList()

        val requiredInputs =
            linkedMapOf(
                "session_manifest" to true,
                "video" to (videoFile != null),
                "frames" to frameRows.isNotEmpty(),
                "imu" to imuRows.isNotEmpty(),
                "bt" to btRows.isNotEmpty(),
            )
        val optionalInputs =
            linkedMapOf(
                "poses" to poseRows.isNotEmpty(),
                "gnss" to gnssRows.isNotEmpty(),
                "video_events" to (videoEventsFile != null),
            )
        val missingRequiredInputs = requiredInputs.filterValues { !it }.keys.toList()

        val streamCounts =
            linkedMapOf(
                "frames" to frameRows.size,
                "imu" to imuRows.size,
                "gnss" to gnssRows.size,
                "bt" to btRows.size,
                "poses" to poseRows.size,
            )
        val nearestDeltas =
            linkedMapOf(
                "imuNearestDeltaNs" to nearestDelta(frameRows, imuRows, listOf("elapsed_realtime_ns", "timestamp_ns")),
                "gnssNearestDeltaNs" to nearestDelta(frameRows, gnssRows, listOf("elapsed_realtime_ns", "timestamp_ns")),
                "btNearestDeltaNs" to nearestDelta(frameRows, btRows, listOf("elapsedRealtimeNanos", "timestamp_ns")),
                "poseNearestDeltaNs" to nearestDelta(frameRows, poseRows, listOf("elapsedRealtimeNanos", "timestamp_ns")),
            )
        val completenessScore = requiredInputs.values.count { it }.toDouble() / requiredInputs.size.toDouble()
        val poseCoverageRatio = if (frameRows.isEmpty()) 0.0 else min(1.0, poseRows.size.toDouble() / frameRows.size.toDouble())
        val qualityFlags =
            linkedMapOf(
                "hasMonotonicSessionBase" to timebase.has("sessionStartElapsedRealtimeNanos"),
                "hasWallClockBase" to timebase.has("sessionStartWallTimeMs"),
                "hasVideoFrameTimeline" to frameRows.isNotEmpty(),
                "hasImuTimeline" to imuRows.isNotEmpty(),
                "hasGnssTimeline" to gnssRows.isNotEmpty(),
                "hasBtTimeline" to btRows.isNotEmpty(),
                "hasPoseTimeline" to poseRows.isNotEmpty(),
                "hasCollectorStatus" to manifest.has("collectorStatus"),
            )

        val blockers =
            buildList {
                if (videoFile == null) add("video.mp4 が不足しています")
                if (frameRows.isEmpty()) add("video_frame_timestamps.csv が不足しています")
                if (imuRows.isEmpty()) add("imu.csv が不足しています")
                if (btRows.isEmpty()) add("人物側の BLE 記録が不足しています")
                if (!timebase.has("sessionStartElapsedRealtimeNanos")) add("sessionStartElapsedRealtimeNanos が不足しています")
            }
        val recommendedCorrections =
            buildList {
                missingRequiredInputs.forEach { key ->
                    when (key) {
                        "video" -> add("主カメラ動画が不足しています。現場撮影データ保存をやり直してください。")
                        "frames" -> add("frame timeline が不足しています。録画開始後すぐに終了せず、数秒以上記録してください。")
                        "imu" -> add("IMU 記録が不足しています。端末を保持したまま再撮影してください。")
                        "bt" -> add("人物端末の BLE 記録が不足しています。BLE を有効にして再取得してください。")
                    }
                }
                if (poseCoverageRatio < 0.50) {
                    add("ARCore pose coverage が低いです。主対象が見える状態でゆっくり再撮影してください。")
                }
                if (completenessScore < 1.0 && noneMatches(this, "不足しています")) {
                    add("必須入力の不足を解消してから再度 data-check を実行してください。")
                }
                if (isEmpty()) {
                    add("この session は correcting を通過し、次段の modeling へ進めます。")
                }
            }

        return ParsedSession(
            sessionDir = sessionDir,
            sessionId = sessionId,
            manifest = manifest,
            manifestFilename = manifestFile.name,
            timebase = timebase,
            frameFilename = frameSelection?.filename,
            gnssFilename = gnssSelection?.filename,
            btFilename = btSelection?.filename,
            poseFilename = poseSelection?.filename,
            frameRows = frameRows,
            btRows = btRows,
            poseRows = poseRows,
            requiredInputs = requiredInputs,
            optionalInputs = optionalInputs,
            missingRequiredInputs = missingRequiredInputs,
            streamCounts = streamCounts,
            nearestDeltas = nearestDeltas,
            completenessScore = completenessScore,
            poseCoverageRatio = poseCoverageRatio,
            qualityFlags = qualityFlags,
            spaceReconstructionBlockers = blockers,
            recommendedCorrections = recommendedCorrections,
        )
    }

    private fun buildInputReadinessJson(parsed: ParsedSession): String =
        JSONObject()
            .put("sessionId", parsed.sessionId)
            .put("requiredInputs", JSONObject(parsed.requiredInputs))
            .put("optionalInputs", JSONObject(parsed.optionalInputs))
            .put("missingRequiredInputs", JSONArray(parsed.missingRequiredInputs))
            .put("readyForDiagnose", parsed.missingRequiredInputs.isEmpty())
            .put(
                "nextAction",
                if (parsed.missingRequiredInputs.isEmpty()) "data-check を確認する" else "現場撮影条件を修正する",
            )
            .toString(2)

    private fun buildSensorQualityJson(parsed: ParsedSession): String =
        JSONObject()
            .put("sessionId", parsed.sessionId)
            .put("timebase", parsed.timebase)
            .put("streamCounts", JSONObject(parsed.streamCounts))
            .put("collectorStatus", parsed.manifest.optJSONObject("collectorStatus") ?: JSONObject())
            .put("nearestDeltaNs", JSONObject().apply { parsed.nearestDeltas.forEach { (k, v) -> put(k, v) } })
            .put(
                "scores",
                JSONObject()
                    .put("completenessScore", parsed.completenessScore)
                    .put("poseCoverageRatio", parsed.poseCoverageRatio),
            )
            .put("qualityFlags", JSONObject(parsed.qualityFlags))
            .put("recommendedCorrections", JSONArray(parsed.recommendedCorrections))
            .toString(2)

    private fun buildFramePoseIndexCsv(parsed: ParsedSession): String {
        val rows = mutableListOf("frame_id,frame_elapsed_realtime_ns,pose_elapsed_realtime_ns,delta_ns,pose_source")
        parsed.frameRows.forEachIndexed { index, row ->
            val frameTime = longValue(row, listOf("elapsed_realtime_ns", "timestamp_ns")) ?: return@forEachIndexed
            val nearestPose = nearestRow(frameTime, parsed.poseRows, listOf("elapsedRealtimeNanos", "timestamp_ns"))
            val poseTime = nearestPose?.let { longValue(it, listOf("elapsedRealtimeNanos", "timestamp_ns")) }
            val delta = if (poseTime == null) "" else abs(frameTime - poseTime).toString()
            rows +=
                listOf(
                    row["frame_id"]?.ifBlank { null }
                        ?: row["camera_sensor_timestamp_ns"]?.ifBlank { null }
                        ?: row["timestamp_ns"]?.ifBlank { null }
                        ?: index.toString(),
                    frameTime.toString(),
                    poseTime?.toString() ?: "",
                    delta,
                    if (poseTime == null) "" else "nearest_pose",
                ).joinToString(",")
        }
        return rows.joinToString("\n", postfix = "\n")
    }

    private fun buildMemberIdentityMapJson(parsed: ParsedSession): String {
        val devices = JSONArray()
        val members = JSONArray()
        val btIdentities = JSONArray()

        val rootDeviceId =
            firstNonBlank(
                parsed.manifest.optString("deviceId"),
                parsed.manifest.optString("collectorDeviceId"),
                parsed.manifest.optString("deviceModel"),
            ) ?: "main-device"
        val mainMemberId = firstNonBlank(parsed.manifest.optString("memberId"), "main_capture") ?: "main_capture"

        devices.put(JSONObject().put("deviceId", rootDeviceId).put("role", "main_capture"))
        members.put(JSONObject().put("memberId", mainMemberId).put("deviceId", rootDeviceId).put("role", "main_capture"))

        val btGrouped = linkedMapOf<String, MutableSet<String>>()
        parsed.btRows.forEach { row ->
            val subjectId = firstNonBlank(row["memberId"], row["deviceId"], row["sourceDeviceId"], "unknown") ?: "unknown"
            val btValue =
                firstNonBlank(
                    row["btAddress"],
                    row["bluetoothAddress"],
                    row["deviceAddress"],
                    row["remoteAddress"],
                    row["address"],
                    row["beaconId"],
                )
            if (btValue != null) {
                btGrouped.getOrPut(subjectId) { linkedSetOf() }.add(btValue)
            }
        }
        btGrouped.forEach { (memberId, ids) ->
            btIdentities.put(JSONObject().put("memberId", memberId).put("btIdentifiers", JSONArray(ids.toList())))
        }

        return JSONObject()
            .put("sessionId", parsed.sessionId)
            .put("devices", devices)
            .put("members", members)
            .put("btIdentity", btIdentities)
            .toString(2)
    }

    private fun buildSessionPackageJson(parsed: ParsedSession): String =
        JSONObject()
            .put("sessionId", parsed.sessionId)
            .put("status", parsed.manifest.optString("status"))
            .put("deviceModel", parsed.manifest.optString("deviceModel"))
            .put(
                "sessionMode",
                firstNonBlank(
                    parsed.manifest.optString("sessionMode"),
                    parsed.manifest.optString("recordingMode"),
                    parsed.manifest.optJSONObject("recordingConfig")?.optString("recordingMode"),
                ) ?: "review",
            )
            .put("timebase", parsed.timebase)
            .put("requiredInputs", JSONObject(parsed.requiredInputs))
            .put("optionalInputs", JSONObject(parsed.optionalInputs))
            .put("streamCounts", JSONObject(parsed.streamCounts))
            .put("collectorStatus", parsed.manifest.optJSONObject("collectorStatus") ?: JSONObject())
            .put(
                "scores",
                JSONObject()
                    .put("completenessScore", parsed.completenessScore)
                    .put("poseCoverageRatio", parsed.poseCoverageRatio),
            )
            .put("nearestDeltaNs", JSONObject().apply { parsed.nearestDeltas.forEach { (k, v) -> put(k, v) } })
            .put(
                "sourceFiles",
                JSONObject()
                    .put("manifest", parsed.manifestFilename)
                    .put("video", if (File(parsed.sessionDir, "video.mp4").exists()) "video.mp4" else JSONObject.NULL)
                    .put("frames", parsed.frameFilename ?: JSONObject.NULL)
                    .put("imu", if (File(parsed.sessionDir, "imu.csv").exists()) "imu.csv" else JSONObject.NULL)
                    .put("gnss", parsed.gnssFilename ?: JSONObject.NULL)
                    .put("bt", parsed.btFilename ?: JSONObject.NULL)
                    .put("poses", parsed.poseFilename ?: JSONObject.NULL)
                    .put("videoEvents", if (File(parsed.sessionDir, "video_events.jsonl").exists()) "video_events.jsonl" else JSONObject.NULL),
            )
            .put("rawBundleRoot", parsed.sessionDir.absolutePath)
            .put("derivedBundleRoot", File(parsed.sessionDir, "trajectreview").absolutePath)
            .toString(2)

    private fun buildSpaceHandoffManifestJson(parsed: ParsedSession): String =
        JSONObject()
            .put("sessionId", parsed.sessionId)
            .put("targetStage", "SpaceReconstruction")
            .put("readyForSpaceReconstruction", parsed.spaceReconstructionBlockers.isEmpty())
            .put("allowModelingProceed", true)
            .put("blockers", JSONArray(parsed.spaceReconstructionBlockers))
            .put("recommendedCorrections", JSONArray(parsed.recommendedCorrections))
            .put(
                "consumedArtifacts",
                JSONArray(
                    listOf(
                        "session_package.json",
                        "input_readiness.json",
                        "sensor_quality.json",
                        "frame_pose_index.csv",
                    ),
                ),
            )
            .put(
                "recommendedNextAction",
                if (parsed.spaceReconstructionBlockers.isEmpty()) {
                    "modeling へ進める"
                } else {
                    "warning を確認したうえで modeling へ進める"
                },
            )
            .toString(2)

    private fun loadFirstAvailable(sessionDir: File, candidates: List<String>): SourceSelection? {
        candidates.forEach { filename ->
            val file = File(sessionDir, filename)
            if (!file.exists() || file.length() == 0L) {
                return@forEach
            }
            val text = file.readText()
            val rows =
                if (filename.endsWith(".csv")) {
                    parseCsv(text)
                } else {
                    parseJsonl(text)
                }
            if (rows.isNotEmpty()) {
                return SourceSelection(filename, rows)
            }
        }
        return null
    }

    private fun firstExistingFile(sessionDir: File, candidates: List<String>): File? =
        candidates.firstNotNullOfOrNull { filename ->
            File(sessionDir, filename).takeIf { it.exists() }
        }

    private fun parseCsv(text: String): List<Map<String, String>> {
        val lines = text.lineSequence().filter { it.isNotBlank() }.toList()
        if (lines.isEmpty()) {
            return emptyList()
        }
        val headers = lines.first().split(",").map { it.trim() }
        return lines.drop(1).map { line ->
            val values = line.split(",")
            headers.mapIndexed { index, header -> header to values.getOrElse(index) { "" }.trim() }.toMap()
        }
    }

    private fun parseJsonl(text: String): List<Map<String, String>> =
        text.lineSequence()
            .filter { it.isNotBlank() }
            .map { line ->
                val json = JSONObject(line)
                json.keys().asSequence().associateWith { key -> json.opt(key)?.toString() ?: "" }
            }
            .toList()

    private fun nearestDelta(
        frameRows: List<Map<String, String>>,
        sensorRows: List<Map<String, String>>,
        candidateKeys: List<String>,
    ): Long? {
        if (frameRows.isEmpty() || sensorRows.isEmpty()) {
            return null
        }
        val sensorValues = sensorRows.mapNotNull { row -> longValue(row, candidateKeys) }.sorted()
        if (sensorValues.isEmpty()) {
            return null
        }
        var nearest: Long? = null
        frameRows.take(60).forEach { row ->
            val frameValue = longValue(row, listOf("elapsed_realtime_ns", "timestamp_ns")) ?: return@forEach
            val candidate = sensorValues.minOf { value -> abs(frameValue - value) }
            nearest = if (nearest == null) candidate else min(nearest ?: candidate, candidate)
        }
        return nearest
    }

    private fun nearestRow(
        targetValue: Long,
        rows: List<Map<String, String>>,
        candidateKeys: List<String>,
    ): Map<String, String>? =
        rows.minByOrNull { row ->
            val value = longValue(row, candidateKeys) ?: Long.MAX_VALUE
            abs(targetValue - value)
        }

    private fun longValue(row: Map<String, String>, candidateKeys: List<String>): Long? {
        candidateKeys.forEach { key ->
            val raw = row[key]
            if (!raw.isNullOrBlank()) {
                return raw.toDoubleOrNull()?.toLong()
            }
        }
        return null
    }

    private fun firstNonBlank(vararg values: String?): String? =
        values.firstOrNull { !it.isNullOrBlank() }

    private fun noneMatches(items: List<String>, pattern: String): Boolean =
        items.none { it.contains(pattern) }

    private data class SourceSelection(
        val filename: String,
        val rows: List<Map<String, String>>,
    )

    private data class ParsedSession(
        val sessionDir: File,
        val sessionId: String,
        val manifest: JSONObject,
        val manifestFilename: String,
        val timebase: JSONObject,
        val frameFilename: String?,
        val gnssFilename: String?,
        val btFilename: String?,
        val poseFilename: String?,
        val frameRows: List<Map<String, String>>,
        val btRows: List<Map<String, String>>,
        val poseRows: List<Map<String, String>>,
        val requiredInputs: Map<String, Boolean>,
        val optionalInputs: Map<String, Boolean>,
        val missingRequiredInputs: List<String>,
        val streamCounts: Map<String, Int>,
        val nearestDeltas: Map<String, Long?>,
        val completenessScore: Double,
        val poseCoverageRatio: Double,
        val qualityFlags: Map<String, Boolean>,
        val spaceReconstructionBlockers: List<String>,
        val recommendedCorrections: List<String>,
    )
}
