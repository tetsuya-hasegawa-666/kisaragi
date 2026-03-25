package com.reviework.app

import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.abs
import kotlin.math.min

interface SessionInputReader {
    fun exists(filename: String): Boolean

    fun readText(filename: String): String?

    fun readBytes(filename: String): ByteArray? = readText(filename)?.toByteArray(Charsets.UTF_8)

    fun listChildDirectories(): List<SessionInputReader> = emptyList()
}

interface SessionOutputWriter {
    fun writeText(relativePath: String, content: String)

    fun writeBytes(relativePath: String, content: ByteArray)
}

data class SessionExportResult(
    val sessionId: String,
    val exportRelativeRoot: String,
    val rawOutputFiles: List<String>,
    val derivedOutputFiles: List<String>,
    val readyForDiagnose: Boolean,
    val missingRequiredInputs: List<String>,
    val completenessScore: Double,
    val poseCoverageRatio: Double,
    val nearestPoseDeltaNs: Long?,
    val readyForSpaceReconstruction: Boolean,
    val spaceReconstructionBlockers: List<String>,
)

class ISensoriumExtractionService {

    fun export(source: SessionInputReader, output: SessionOutputWriter): SessionExportResult {
        val parsed = parse(source)
        val exportRoot = sanitizeSegment(parsed.sessionId)

        parsed.rawFiles.forEach { filename ->
            val content = parsed.sessionSource.readBytes(filename) ?: return@forEach
            output.writeBytes("$exportRoot/isensorium/$filename", content)
        }

        output.writeText("$exportRoot/trajectreview/input_readiness.json", buildInputReadinessJson(parsed))
        output.writeText("$exportRoot/trajectreview/sensor_quality.json", buildSensorQualityJson(parsed))
        output.writeText("$exportRoot/trajectreview/frame_pose_index.csv", buildFramePoseIndexCsv(parsed))
        output.writeText("$exportRoot/trajectreview/member_identity_map.json", buildMemberIdentityMapJson(parsed))
        output.writeText("$exportRoot/trajectreview/session_package.json", buildSessionPackageJson(parsed, exportRoot))
        output.writeText("$exportRoot/trajectreview/space_handoff_manifest.json", buildSpaceHandoffManifestJson(parsed))

        return SessionExportResult(
            sessionId = parsed.sessionId,
            exportRelativeRoot = exportRoot,
            rawOutputFiles = parsed.rawFiles.map { "$exportRoot/isensorium/$it" },
            derivedOutputFiles =
                listOf(
                    "$exportRoot/trajectreview/input_readiness.json",
                    "$exportRoot/trajectreview/sensor_quality.json",
                    "$exportRoot/trajectreview/frame_pose_index.csv",
                    "$exportRoot/trajectreview/member_identity_map.json",
                    "$exportRoot/trajectreview/session_package.json",
                    "$exportRoot/trajectreview/space_handoff_manifest.json",
                ),
            readyForDiagnose = parsed.missingRequiredInputs.isEmpty(),
            missingRequiredInputs = parsed.missingRequiredInputs,
            completenessScore = parsed.completenessScore,
            poseCoverageRatio = parsed.poseCoverageRatio,
            nearestPoseDeltaNs = parsed.poseNearestDeltaNs,
            readyForSpaceReconstruction = parsed.spaceReconstructionBlockers.isEmpty(),
            spaceReconstructionBlockers = parsed.spaceReconstructionBlockers,
        )
    }

    private fun parse(source: SessionInputReader): ParsedSession {
        val resolvedSource = resolveSessionRoot(source)
        val manifestSelection =
            loadFirstText(
                resolvedSource,
                listOf("session_manifest.json", "manifest.json"),
            ) ?: throw IllegalArgumentException("manifest file が見つかりません。")
        val manifestText = manifestSelection.second
        val manifest = JSONObject(manifestText)
        val sessionId = manifest.optString("sessionId").ifBlank { "unknown-session" }
        val timebase = manifest.optJSONObject("timebase") ?: JSONObject()

        val frameSelection = loadFirstAvailable(resolvedSource, listOf("video_frame_timestamps.csv", "frames.csv"))
        val imuSelection = loadFirstAvailable(resolvedSource, listOf("imu.csv"))
        val gnssSelection = loadFirstAvailable(resolvedSource, listOf("gnss.csv"))
        val btSelection = loadFirstAvailable(resolvedSource, listOf("bt.jsonl", "ble_scan.jsonl", "bt_events.csv", "bt.csv"))
        val poseSelection = loadFirstAvailable(resolvedSource, listOf("poses.jsonl", "arcore_pose.jsonl", "arcore_pose.csv"))
        val trackingSelection = loadFirstAvailable(resolvedSource, listOf("arcore_tracking.csv"))
        val qualitySelection = loadFirstAvailable(resolvedSource, listOf("quality_flags.csv", "frame_quality.csv"))
        val videoPresent = resolvedSource.exists("video.mp4")
        val videoEventsPresent = resolvedSource.exists("video_events.jsonl")
        val frameRows = frameSelection?.rows ?: emptyList()
        val imuRows = imuSelection?.rows ?: emptyList()
        val gnssRows = gnssSelection?.rows ?: emptyList()
        val btRows = btSelection?.rows ?: emptyList()
        val poseRows = poseSelection?.rows ?: emptyList()

        val requiredInputs =
            linkedMapOf(
                "session_manifest" to true,
                "video" to videoPresent,
                "frames" to frameRows.isNotEmpty(),
                "imu" to imuRows.isNotEmpty(),
                "bt" to btRows.isNotEmpty(),
            )
        val optionalInputs =
            linkedMapOf(
                "poses" to poseRows.isNotEmpty(),
                "gnss" to gnssRows.isNotEmpty(),
                "video_events" to videoEventsPresent,
            )
        val missingRequiredInputs = requiredInputs.filterValues { !it }.keys.toList()

        val rawFiles =
            buildList {
                add(manifestSelection.first)
                frameSelection?.filename?.let { add(it) }
                imuSelection?.filename?.let { add(it) }
                gnssSelection?.filename?.let { add(it) }
                btSelection?.filename?.let { add(it) }
                poseSelection?.filename?.let { add(it) }
                trackingSelection?.filename?.let { add(it) }
                qualitySelection?.filename?.let { add(it) }
                if (videoPresent) {
                    add("video.mp4")
                }
                if (videoEventsPresent) {
                    add("video_events.jsonl")
                }
            }

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
                "imuNearestDeltaNs" to nearestDelta(frameRows, imuRows, candidateKeys = listOf("elapsed_realtime_ns", "timestamp_ns")),
                "gnssNearestDeltaNs" to nearestDelta(frameRows, gnssRows, candidateKeys = listOf("elapsed_realtime_ns", "timestamp_ns")),
                "btNearestDeltaNs" to nearestDelta(frameRows, btRows, candidateKeys = listOf("elapsedRealtimeNanos", "timestamp_ns")),
                "poseNearestDeltaNs" to nearestDelta(frameRows, poseRows, candidateKeys = listOf("elapsedRealtimeNanos", "timestamp_ns")),
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
        val spaceReconstructionBlockers =
            buildList {
                if (!videoPresent) add("video.mp4 が不足している")
                if (frameRows.isEmpty()) add("frame timeline が不足している")
                if (imuRows.isEmpty()) add("imu.csv が不足している")
                if (!timebase.has("sessionStartElapsedRealtimeNanos")) add("sessionStartElapsedRealtimeNanos が不足している")
            }

        return ParsedSession(
            sessionSource = resolvedSource,
            sessionId = sessionId,
            manifest = manifest,
            manifestFilename = manifestSelection.first,
            timebase = timebase,
            rawFiles = rawFiles,
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
            spaceReconstructionBlockers = spaceReconstructionBlockers,
        )
    }

    private fun buildInputReadinessJson(parsed: ParsedSession): String =
        JSONObject()
            .put("sessionId", parsed.sessionId)
            .put("requiredInputs", JSONObject(parsed.requiredInputs))
            .put("optionalInputs", JSONObject(parsed.optionalInputs))
            .put("missingRequiredInputs", JSONArray(parsed.missingRequiredInputs))
            .put("readyForDiagnose", parsed.missingRequiredInputs.isEmpty())
            .put("nextAction", if (parsed.missingRequiredInputs.isEmpty()) "処理を開始" else "入力条件を見直す")
            .toString(2)

    private fun buildSensorQualityJson(parsed: ParsedSession): String =
        JSONObject()
            .put("sessionId", parsed.sessionId)
            .put("timebase", parsed.timebase)
            .put("streamCounts", JSONObject(parsed.streamCounts))
            .put("collectorStatus", parsed.manifest.optJSONObject("collectorStatus") ?: JSONObject())
            .put(
                "nearestDeltaNs",
                JSONObject().apply {
                    parsed.nearestDeltas.forEach { (key, value) -> put(key, value) }
                },
            )
            .put(
                "scores",
                JSONObject()
                    .put("completenessScore", parsed.completenessScore)
                    .put("poseCoverageRatio", parsed.poseCoverageRatio),
            )
            .put("qualityFlags", JSONObject(parsed.qualityFlags))
            .toString(2)

    private fun buildFramePoseIndexCsv(parsed: ParsedSession): String {
        val rows = mutableListOf("frame_id,frame_elapsed_realtime_ns,pose_elapsed_realtime_ns,delta_ns,pose_source")
        parsed.frameRows.forEachIndexed { index, row ->
            val frameTime = longValue(row, listOf("elapsed_realtime_ns")) ?: return@forEachIndexed
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
        val mainMemberId = firstNonBlank(parsed.manifest.optString("memberId"), "main_capture")

        devices.put(
            JSONObject()
                .put("deviceId", rootDeviceId)
                .put("role", "main_capture")
                .put("deviceModel", parsed.manifest.optString("deviceModel")),
        )
        members.put(
            JSONObject()
                .put("memberId", mainMemberId)
                .put("deviceId", rootDeviceId)
                .put("role", "main_capture"),
        )

        parsed.manifest.optJSONArray("members")?.let { manifestMembers ->
            for (index in 0 until manifestMembers.length()) {
                val member = manifestMembers.optJSONObject(index) ?: continue
                members.put(
                    JSONObject()
                        .put("memberId", member.optString("memberId", "member-$index"))
                        .put("deviceId", member.optString("deviceId", rootDeviceId))
                        .put("role", member.optString("role", "worker")),
                )
            }
        }

        val btGrouped = linkedMapOf<String, MutableSet<String>>()
        parsed.btRows.forEach { row ->
            val subjectId =
                firstNonBlank(
                    row["memberId"],
                    row["deviceId"],
                    row["sourceDeviceId"],
                    "unknown",
                ) ?: "unknown"
            val btValue =
                firstNonBlank(
                    row["btAddress"],
                    row["bluetoothAddress"],
                    row["deviceAddress"],
                    row["remoteAddress"],
                    row["beaconId"],
                )
            if (btValue != null) {
                btGrouped.getOrPut(subjectId) { linkedSetOf() }.add(btValue)
            }
        }
        btGrouped.forEach { (memberId, ids) ->
            btIdentities.put(
                JSONObject()
                    .put("memberId", memberId)
                    .put("btIdentifiers", JSONArray(ids.toList())),
            )
        }

        return JSONObject()
            .put("sessionId", parsed.sessionId)
            .put("devices", devices)
            .put("members", members)
            .put("btIdentity", btIdentities)
            .toString(2)
    }

    private fun buildSessionPackageJson(parsed: ParsedSession, exportRoot: String): String =
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
            .put(
                "nearestDeltaNs",
                JSONObject().apply {
                    parsed.nearestDeltas.forEach { (key, value) -> put(key, value) }
                },
            )
            .put(
                "sourceFiles",
                JSONObject()
                    .put("manifest", parsed.manifestFilename)
                    .put("video", if (parsed.rawFiles.contains("video.mp4")) "video.mp4" else JSONObject.NULL)
                    .put("frames", parsed.frameFilename ?: JSONObject.NULL)
                    .put("imu", if (parsed.rawFiles.contains("imu.csv")) "imu.csv" else JSONObject.NULL)
                    .put("gnss", parsed.gnssFilename ?: JSONObject.NULL)
                    .put("bt", parsed.btFilename ?: JSONObject.NULL)
                    .put("poses", parsed.poseFilename ?: JSONObject.NULL)
                    .put("videoEvents", if (parsed.rawFiles.contains("video_events.jsonl")) "video_events.jsonl" else JSONObject.NULL),
            )
            .put("rawBundleRoot", "$exportRoot/isensorium")
            .put("derivedBundleRoot", "$exportRoot/trajectreview")
            .toString(2)

    private fun buildSpaceHandoffManifestJson(parsed: ParsedSession): String =
        JSONObject()
            .put("sessionId", parsed.sessionId)
            .put("targetStage", "SpaceReconstruction")
            .put("readyForSpaceReconstruction", parsed.spaceReconstructionBlockers.isEmpty())
            .put("blockers", JSONArray(parsed.spaceReconstructionBlockers))
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
            .put("recommendedNextAction", if (parsed.spaceReconstructionBlockers.isEmpty()) "空間再構成を開始" else "入力条件を見直す")
            .toString(2)

    private fun loadFirstAvailable(source: SessionInputReader, candidates: List<String>): SourceSelection? {
        candidates.forEach { filename ->
            val text = source.readText(filename) ?: return@forEach
            if (text.isBlank()) return@forEach
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

    private fun loadFirstText(source: SessionInputReader, candidates: List<String>): Pair<String, String>? {
        candidates.forEach { filename ->
            val text = source.readText(filename) ?: return@forEach
            if (text.isNotBlank()) {
                return filename to text
            }
        }
        return null
    }

    private fun resolveSessionRoot(source: SessionInputReader): SessionInputReader {
        if (source.exists("session_manifest.json") || source.exists("manifest.json")) {
            return source
        }
        return source.listChildDirectories().firstOrNull { child ->
            child.exists("session_manifest.json") || child.exists("manifest.json")
        } ?: source
    }

    private fun parseCsv(text: String?): List<Map<String, String>> {
        if (text.isNullOrBlank()) {
            return emptyList()
        }
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
        sensorKey: String? = null,
        candidateKeys: List<String> = if (sensorKey == null) emptyList() else listOf(sensorKey),
    ): Long? {
        if (frameRows.isEmpty() || sensorRows.isEmpty()) {
            return null
        }
        val sensorValues =
            sensorRows.mapNotNull { row -> longValue(row, candidateKeys) }.sorted()
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

    private fun sanitizeSegment(raw: String): String =
        raw.replace(Regex("[^A-Za-z0-9._-]"), "_").ifBlank { "session-export" }

    private data class SourceSelection(
        val filename: String,
        val rows: List<Map<String, String>>,
    )

    private data class ParsedSession(
        val sessionSource: SessionInputReader,
        val sessionId: String,
        val manifest: JSONObject,
        val manifestFilename: String,
        val timebase: JSONObject,
        val rawFiles: List<String>,
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
    ) {
        val poseNearestDeltaNs: Long?
            get() = nearestDeltas["poseNearestDeltaNs"]
    }
}
