package com.isensorium.app

import android.graphics.Bitmap
import android.media.MediaMetadataRetriever
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
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
    val imageIntrinsicsCoverageRatio: Double,
    val lensDistortionCoverageRatio: Double,
    val calibrationFrameCount: Int,
    val blockers: List<String>,
    val recommendedCorrections: List<String>,
)

class CorrectingDataCheckService {

    fun run(sessionDir: File): CorrectingDataCheckResult {
        val parsed = parse(sessionDir)
        val derivedDir = File(sessionDir, ARTIFACT_DERIVED_DIR).apply { mkdirs() }
        val imagesDir = File(derivedDir, ARTIFACT_IMAGES_DIR).apply { mkdirs() }
        extractImages(parsed, imagesDir)
        val validatedParsed =
            parsed.copy(
                spaceReconstructionBlockers =
                    buildList {
                        addAll(parsed.spaceReconstructionBlockers)
                        if ((imagesDir.listFiles()?.count { it.isFile } ?: 0) == 0) {
                            add("images/ が不足しています")
                        }
                    }.distinct(),
                warnings =
                    buildList {
                        addAll(parsed.warnings)
                        if ((imagesDir.listFiles()?.count { it.isFile } ?: 0) < parsed.frameRows.size && parsed.frameRows.isNotEmpty()) {
                            add("images/ の一部 frame 抽出に失敗しています")
                        }
                    }.distinct(),
            )

        File(derivedDir, ARTIFACT_INPUT_READINESS).writeText(buildInputReadinessJson(validatedParsed))
        File(derivedDir, ARTIFACT_SENSOR_QUALITY).writeText(buildSensorQualityJson(validatedParsed))
        File(derivedDir, ARTIFACT_FRAME_POSE_INDEX).writeText(buildFramePoseIndexCsv(validatedParsed, imagesDir))
        File(derivedDir, ARTIFACT_CAMERA_CALIBRATION_SUMMARY).writeText(buildCameraCalibrationSummaryJson(validatedParsed))
        File(derivedDir, ARTIFACT_MEMBER_IDENTITY_MAP).writeText(buildMemberIdentityMapJson(validatedParsed))
        File(derivedDir, ARTIFACT_SESSION_PACKAGE).writeText(buildSessionPackageJson(validatedParsed, imagesDir))
        File(derivedDir, ARTIFACT_SPACE_HANDOFF_MANIFEST).writeText(buildSpaceHandoffManifestJson(validatedParsed, imagesDir))

        return CorrectingDataCheckResult(
            sessionId = validatedParsed.sessionId,
            derivedDir = derivedDir,
            readyForDiagnose = validatedParsed.missingRequiredInputs.isEmpty(),
            readyForSpaceReconstruction = validatedParsed.spaceReconstructionBlockers.isEmpty(),
            allowModelingProceed = true,
            missingRequiredInputs = validatedParsed.missingRequiredInputs,
            completenessScore = validatedParsed.completenessScore,
            poseCoverageRatio = validatedParsed.poseCoverageRatio,
            imageIntrinsicsCoverageRatio = validatedParsed.imageIntrinsicsCoverageRatio,
            lensDistortionCoverageRatio = validatedParsed.lensDistortionCoverageRatio,
            calibrationFrameCount = validatedParsed.calibrationFrameCount,
            blockers = validatedParsed.spaceReconstructionBlockers,
            recommendedCorrections = validatedParsed.recommendedCorrections,
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
        val arCoreEnabled = manifest.optJSONObject("recordingConfig")?.optBoolean("arCoreEnabled", true)
            ?: manifest.optBoolean("arCoreEnabled", true)
        val configuredArCoreIntervalMs =
            manifest.optJSONObject("recordingConfig")?.optLong("arCoreIntervalMs", 2000L)
                ?: manifest.optLong("arCoreIntervalMs", 2000L)
        val poseCoverageRatio =
            computePoseCoverageRatio(
                frameRows = frameRows,
                poseRows = poseRows,
                arCoreEnabled = arCoreEnabled,
                configuredArCoreIntervalMs = configuredArCoreIntervalMs,
            )
        val calibrationFrameCount =
            poseRows.count {
                longValue(it, listOf("frameTimestampNs", "captureTimestampNs", "timestamp_ns")) != null &&
                    hasAnyValue(it, listOf("imageIntrinsics.fx", "imageFocalLength", "imagePrincipalPoint", "imageDimensions")) &&
                    hasAnyValue(it, listOf("textureIntrinsics.fx", "textureFocalLength", "texturePrincipalPoint", "textureDimensions"))
            }
        val validPoseCount = poseRows.count { hasAnyValue(it, listOf("pose.tx", "translation", "rotationQuaternion")) }
        val imageIntrinsicsCount = poseRows.count { hasAnyValue(it, listOf("imageIntrinsics.fx", "imageFocalLength", "imagePrincipalPoint", "imageDimensions")) }
        val textureIntrinsicsCount = poseRows.count { hasAnyValue(it, listOf("textureIntrinsics.fx", "textureFocalLength", "texturePrincipalPoint", "textureDimensions")) }
        val lensDistortionCount = poseRows.count { hasAnyValue(it, listOf("lensDistortion.coefficients", "lensDistortion")) }
        val imageIntrinsicsCoverageRatio =
            if (poseRows.isEmpty()) 0.0 else min(1.0, imageIntrinsicsCount.toDouble() / poseRows.size.toDouble())
        val textureIntrinsicsCoverageRatio =
            if (poseRows.isEmpty()) 0.0 else min(1.0, textureIntrinsicsCount.toDouble() / poseRows.size.toDouble())
        val lensDistortionCoverageRatio =
            if (poseRows.isEmpty()) 0.0 else min(1.0, lensDistortionCount.toDouble() / poseRows.size.toDouble())
        val timestampStartNs =
            poseRows.mapNotNull { longValue(it, listOf("frameTimestampNs", "captureTimestampNs", "timestamp_ns")) }.minOrNull()
        val timestampEndNs =
            poseRows.mapNotNull { longValue(it, listOf("frameTimestampNs", "captureTimestampNs", "timestamp_ns")) }.maxOrNull()
        val intrinsicsChangedDuringRecording =
            poseRows
                .mapNotNull { buildIntrinsicsSignature(it) }
                .distinct()
                .size > 1
        val intrinsicsModeCandidate =
            when {
                imageIntrinsicsCount == 0 -> "unknown"
                intrinsicsChangedDuringRecording -> "per_frame"
                else -> "session_fixed"
            }
        val legacySessionWithoutCalibration =
            poseRows.isNotEmpty() && imageIntrinsicsCount == 0 && textureIntrinsicsCount == 0 && lensDistortionCount == 0
        val qualityFlags =
            linkedMapOf(
                "hasMonotonicSessionBase" to timebase.has("sessionStartElapsedRealtimeNanos"),
                "hasWallClockBase" to timebase.has("sessionStartWallTimeMs"),
                "hasVideoFrameTimeline" to frameRows.isNotEmpty(),
                "hasImuTimeline" to imuRows.isNotEmpty(),
                "hasGnssTimeline" to gnssRows.isNotEmpty(),
                "hasBtTimeline" to btRows.isNotEmpty(),
                "hasPoseTimeline" to poseRows.isNotEmpty(),
                "hasImageIntrinsicsTimeline" to (imageIntrinsicsCount > 0),
                "hasTextureIntrinsicsTimeline" to (textureIntrinsicsCount > 0),
                "hasLensDistortionTimeline" to (lensDistortionCount > 0),
                "hasCollectorStatus" to manifest.has("collectorStatus"),
            )

        val warnings =
            buildList {
                if (imageIntrinsicsCoverageRatio < 1.0) add("imageIntrinsicsCoverageRatio が 1.0 未満です")
                if (textureIntrinsicsCoverageRatio < 1.0) add("textureIntrinsicsCoverageRatio が 1.0 未満です")
                if (lensDistortionCoverageRatio < 1.0) add("lensDistortionCoverageRatio が 1.0 未満です")
                if (poseRows.any { row -> stringValue(row, listOf("trackingState")) !in listOf(null, "", "TRACKING") }) {
                    add("trackingState が TRACKING 以外の frame を含みます")
                }
                if ((nearestDeltas["poseNearestDeltaNs"] ?: 0L) > 150_000_000L) {
                    add("time_delta_ms が大きい frame が混在します")
                }
            }
        val blockers =
            buildList {
                if (videoFile == null) add("video.mp4 が不足しています")
                if (frameRows.isEmpty()) add("video_frame_timestamps.csv が不足しています")
                if (imuRows.isEmpty()) add("imu.csv が不足しています")
                if (btRows.isEmpty()) add("人物側の BLE 記録が不足しています")
                if (!timebase.has("sessionStartElapsedRealtimeNanos")) add("sessionStartElapsedRealtimeNanos が不足しています")
                if (poseRows.isEmpty()) add("arcore_pose.jsonl が不足しています")
                if (validPoseCount == 0) add("pose がほぼ 0 件です")
                if (imageIntrinsicsCount == 0) add("intrinsics がほぼ 0 件です")
                if (legacySessionWithoutCalibration) add("legacy_session_without_calibration")
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
                if (arCoreEnabled && poseCoverageRatio < 0.70) {
                    add("ARCore pose coverage が低いです。主対象が見える状態でゆっくり再撮影してください。")
                }
                if (imageIntrinsicsCount == 0) {
                    add("camera intrinsics が不足しています。ARCore が有効な状態で再撮影してください。")
                }
                if (lensDistortionCount == 0) {
                    add("lens distortion が不足しています。対応 frame を増やして再撮影してください。")
                }
                if (completenessScore < 1.0 && noneMatches(this, "不足しています")) {
                    add("必須入力の不足を解消してから再度 data-check を実行してください。")
                }
                if (isEmpty()) {
                    add("この session は correcting を通過し、次段の modeling へ進めます。")
                }
            }
        val recommendedModelingRoutes =
            buildList {
                add("route-da3metric-large-5fps-static-intrinsics")
                add("route-da3metric-large-10fps-static-intrinsics")
                if (intrinsicsModeCandidate == "per_frame") {
                    add("route-da3metric-large-10fps-per-frame-intrinsics")
                } else if (imageIntrinsicsCount > 0) {
                    add("route-da3metric-large-10fps-per-frame-intrinsics")
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
            validPoseCount = validPoseCount,
            calibrationFrameCount = calibrationFrameCount,
            imageIntrinsicsCount = imageIntrinsicsCount,
            textureIntrinsicsCount = textureIntrinsicsCount,
            lensDistortionCount = lensDistortionCount,
            imageIntrinsicsCoverageRatio = imageIntrinsicsCoverageRatio,
            textureIntrinsicsCoverageRatio = textureIntrinsicsCoverageRatio,
            lensDistortionCoverageRatio = lensDistortionCoverageRatio,
            timestampStartNs = timestampStartNs,
            timestampEndNs = timestampEndNs,
            intrinsicsModeCandidate = intrinsicsModeCandidate,
            intrinsicsChangedDuringRecording = intrinsicsChangedDuringRecording,
            legacySessionWithoutCalibration = legacySessionWithoutCalibration,
            qualityFlags = qualityFlags,
            warnings = warnings,
            spaceReconstructionBlockers = blockers,
            recommendedCorrections = recommendedCorrections,
            recommendedModelingRoutes = recommendedModelingRoutes,
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
            .put("timeAlignmentDeltaMs", nsToMs(parsed.nearestDeltas["poseNearestDeltaNs"]))
            .put(
                "scores",
                JSONObject()
                    .put("completenessScore", parsed.completenessScore)
                    .put("poseCoverageRatio", parsed.poseCoverageRatio)
                    .put("imageIntrinsicsCoverageRatio", parsed.imageIntrinsicsCoverageRatio)
                    .put("textureIntrinsicsCoverageRatio", parsed.textureIntrinsicsCoverageRatio)
                    .put("lensDistortionCoverageRatio", parsed.lensDistortionCoverageRatio),
            )
            .put(
                "trackingQualitySummary",
                JSONObject()
                    .put("validPoseCount", parsed.validPoseCount)
                    .put("trackingFrameCount", parsed.poseRows.count { stringValue(it, listOf("trackingState")) == "TRACKING" })
                    .put("nonTrackingFrameCount", parsed.poseRows.count { stringValue(it, listOf("trackingState")) !in listOf(null, "", "TRACKING") }),
            )
            .put("qualityFlags", JSONObject(parsed.qualityFlags))
            .put("warnings", JSONArray(parsed.warnings))
            .put("blockers", JSONArray(parsed.spaceReconstructionBlockers))
            .put("recommendedCorrections", JSONArray(parsed.recommendedCorrections))
            .toString(2)

    private fun buildCameraCalibrationSummaryJson(parsed: ParsedSession): String =
        JSONObject()
            .put("sessionId", parsed.sessionId)
            .put("specVersion", "2026-03-27-calibration-export-v1")
            .put("recordCount", parsed.poseRows.size)
            .put("validPoseCount", parsed.validPoseCount)
            .put("imageIntrinsicsCount", parsed.imageIntrinsicsCount)
            .put("textureIntrinsicsCount", parsed.textureIntrinsicsCount)
            .put("lensDistortionCount", parsed.lensDistortionCount)
            .put("calibrationFrameCount", parsed.calibrationFrameCount)
            .put("imageIntrinsicsCoverageRatio", parsed.imageIntrinsicsCoverageRatio)
            .put("textureIntrinsicsCoverageRatio", parsed.textureIntrinsicsCoverageRatio)
            .put("lensDistortionCoverageRatio", parsed.lensDistortionCoverageRatio)
            .put("timestampStartNs", parsed.timestampStartNs ?: JSONObject.NULL)
            .put("timestampEndNs", parsed.timestampEndNs ?: JSONObject.NULL)
            .put("intrinsicsModeCandidate", parsed.intrinsicsModeCandidate)
            .put("intrinsicsChangedDuringRecording", parsed.intrinsicsChangedDuringRecording)
            .put("legacySessionWithoutCalibration", parsed.legacySessionWithoutCalibration)
            .put("recommendedModelingRoutes", JSONArray(parsed.recommendedModelingRoutes))
            .put("warnings", JSONArray(parsed.warnings))
            .put("blockers", JSONArray(parsed.spaceReconstructionBlockers))
            .put("coordinateSystem", "right-handed world space from ARCore displayOrientedPose")
            .toString(2)

    private fun buildFramePoseIndexCsv(parsed: ParsedSession, imagesDir: File): String {
        val rows =
            mutableListOf(
                "frame_index,image_file_name,frame_timestamp_ns,pose_record_index,pose_timestamp_ns,time_delta_ms,image_intrinsics_mode,tracking_state",
            )
        parsed.frameRows.forEachIndexed { index, row ->
            val frameTime =
                longValue(
                    row,
                    listOf("camera_sensor_timestamp_ns", "timestamp_ns", "elapsed_realtime_ns"),
                ) ?: return@forEachIndexed
            val nearestPose =
                nearestRow(
                    frameTime,
                    parsed.poseRows,
                    listOf("frameTimestampNs", "captureTimestampNs", "elapsedRealtimeNanos", "timestamp_ns"),
                )
            val poseTime = nearestPose?.let { longValue(it, listOf("frameTimestampNs", "captureTimestampNs", "elapsedRealtimeNanos", "timestamp_ns")) }
            val deltaMs = if (poseTime == null) "" else "%.3f".format(abs(frameTime - poseTime) / 1_000_000.0)
            val imageFileName = imageFileName(index)
            rows +=
                listOf(
                    index.toString(),
                    if (File(imagesDir, imageFileName).exists()) imageFileName else "",
                    frameTime.toString(),
                    stringValue(nearestPose, listOf("recordIndex")) ?: "",
                    poseTime?.toString() ?: "",
                    deltaMs,
                    parsed.intrinsicsModeCandidate,
                    stringValue(nearestPose, listOf("trackingState")) ?: "",
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

    private fun buildSessionPackageJson(parsed: ParsedSession, imagesDir: File): String =
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
            .put("warnings", JSONArray(parsed.warnings))
            .put("blockers", JSONArray(parsed.spaceReconstructionBlockers))
            .put(
                "scores",
                JSONObject()
                    .put("completenessScore", parsed.completenessScore)
                    .put("poseCoverageRatio", parsed.poseCoverageRatio)
                    .put("imageIntrinsicsCoverageRatio", parsed.imageIntrinsicsCoverageRatio)
                    .put("lensDistortionCoverageRatio", parsed.lensDistortionCoverageRatio),
            )
            .put(
                "cameraCalibration",
                JSONObject()
                    .put("calibrationFrameCount", parsed.calibrationFrameCount)
                    .put("imageIntrinsicsCount", parsed.imageIntrinsicsCount)
                    .put("textureIntrinsicsCount", parsed.textureIntrinsicsCount)
                    .put("lensDistortionCount", parsed.lensDistortionCount),
            )
            .put("nearestDeltaNs", JSONObject().apply { parsed.nearestDeltas.forEach { (k, v) -> put(k, v) } })
            .put("mainVideoPath", "video.mp4")
            .put("imageDirectory", "${ARTIFACT_DERIVED_DIR}/${ARTIFACT_IMAGES_DIR}")
            .put("framePoseIndexPath", "${ARTIFACT_DERIVED_DIR}/${ARTIFACT_FRAME_POSE_INDEX}")
            .put("cameraCalibrationSummaryPath", "${ARTIFACT_DERIVED_DIR}/${ARTIFACT_CAMERA_CALIBRATION_SUMMARY}")
            .put("arcorePosePath", parsed.poseFilename ?: JSONObject.NULL)
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
                    .put("videoEvents", if (File(parsed.sessionDir, "video_events.jsonl").exists()) "video_events.jsonl" else JSONObject.NULL)
                    .put("cameraCalibrationSummary", ARTIFACT_CAMERA_CALIBRATION_SUMMARY)
                    .put("images", if (imagesDir.exists()) "${ARTIFACT_DERIVED_DIR}/${ARTIFACT_IMAGES_DIR}" else JSONObject.NULL),
            )
            .put("rawBundleRoot", parsed.sessionDir.absolutePath)
            .put("derivedBundleRoot", File(parsed.sessionDir, ARTIFACT_DERIVED_DIR).absolutePath)
            .toString(2)

    private fun buildSpaceHandoffManifestJson(parsed: ParsedSession, imagesDir: File): String =
        JSONObject()
            .put("sessionId", parsed.sessionId)
            .put("targetStage", "SpaceReconstruction")
            .put("readyForSpaceReconstruction", parsed.spaceReconstructionBlockers.isEmpty())
            .put("allowModelingProceed", true)
            .put("warnings", JSONArray(parsed.warnings))
            .put("blockers", JSONArray(parsed.spaceReconstructionBlockers))
            .put("recommendedCorrections", JSONArray(parsed.recommendedCorrections))
            .put(
                "requiredArtifacts",
                JSONArray(
                    listOf(
                        ARTIFACT_SESSION_PACKAGE,
                        ARTIFACT_INPUT_READINESS,
                        ARTIFACT_SENSOR_QUALITY,
                        ARTIFACT_FRAME_POSE_INDEX,
                        ARTIFACT_CAMERA_CALIBRATION_SUMMARY,
                        ARTIFACT_ARCORE_POSE,
                        ARTIFACT_IMAGES_DIR,
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

    private fun extractImages(parsed: ParsedSession, imagesDir: File) {
        imagesDir.mkdirs()
        imagesDir.listFiles()?.forEach { file -> file.delete() }
        val videoFile = File(parsed.sessionDir, "video.mp4")
        if (!videoFile.exists() || parsed.frameRows.isEmpty()) {
            return
        }
        runCatching {
            val firstElapsedRealtimeNs =
                parsed.frameRows.firstNotNullOfOrNull { row ->
                    longValue(row, listOf("elapsed_realtime_ns", "timestamp_ns"))
                } ?: 0L
            val retriever = MediaMetadataRetriever()
            retriever.setDataSource(videoFile.absolutePath)
            parsed.frameRows.forEachIndexed { index, row ->
                val elapsedRealtimeNs = longValue(row, listOf("elapsed_realtime_ns", "timestamp_ns")) ?: return@forEachIndexed
                val relativeUs = ((elapsedRealtimeNs - firstElapsedRealtimeNs).coerceAtLeast(0L)) / 1_000L
                val bitmap = retriever.getFrameAtTime(relativeUs, MediaMetadataRetriever.OPTION_CLOSEST) ?: return@forEachIndexed
                FileOutputStream(File(imagesDir, imageFileName(index))).use { output ->
                    bitmap.compress(Bitmap.CompressFormat.JPEG, 90, output)
                }
                bitmap.recycle()
            }
            retriever.release()
        }.onFailure {
            // image extraction failure is reflected later as missing images blocker/warning via file checks
        }
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
                buildMap {
                    flattenJsonObject("", json, this)
                }
            }
            .toList()

    private fun flattenJsonObject(prefix: String, json: JSONObject, output: MutableMap<String, String>) {
        json.keys().forEach { key ->
            val value = json.opt(key)
            val nextKey = if (prefix.isBlank()) key else "$prefix.$key"
            when (value) {
                is JSONObject -> flattenJsonObject(nextKey, value, output)
                is JSONArray -> output[nextKey] = value.toString()
                null, JSONObject.NULL -> output[nextKey] = ""
                else -> output[nextKey] = value.toString()
            }
            if (prefix.isBlank() && value !is JSONObject) {
                output[key] = output[nextKey].orEmpty()
            }
        }
    }

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

    private fun computePoseCoverageRatio(
        frameRows: List<Map<String, String>>,
        poseRows: List<Map<String, String>>,
        arCoreEnabled: Boolean,
        configuredArCoreIntervalMs: Long,
    ): Double {
        if (!arCoreEnabled) {
            return 1.0
        }
        if (poseRows.isEmpty()) {
            return 0.0
        }
        val frameTimes = frameRows.mapNotNull { row -> longValue(row, listOf("elapsed_realtime_ns", "timestamp_ns")) }
        val durationNs =
            if (frameTimes.size >= 2) {
                (frameTimes.maxOrNull() ?: 0L) - (frameTimes.minOrNull() ?: 0L)
            } else {
                0L
            }
        val intervalNs = configuredArCoreIntervalMs.coerceAtLeast(1L) * 1_000_000L
        val expectedPoseSamples =
            if (durationNs <= 0L) {
                1
            } else {
                ((durationNs / intervalNs).toInt() + 1).coerceAtLeast(1)
            }
        return min(1.0, poseRows.size.toDouble() / expectedPoseSamples.toDouble())
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

    private fun stringValue(row: Map<String, String>?, candidateKeys: List<String>): String? {
        if (row == null) {
            return null
        }
        candidateKeys.forEach { key ->
            val raw = row[key]
            if (!raw.isNullOrBlank() && raw != "null") {
                return raw
            }
        }
        return null
    }

    private fun firstNonBlank(vararg values: String?): String? =
        values.firstOrNull { !it.isNullOrBlank() }

    private fun noneMatches(items: List<String>, pattern: String): Boolean =
        items.none { it.contains(pattern) }

    private fun hasAnyValue(row: Map<String, String>, keys: List<String>): Boolean =
        keys.any { !row[it].isNullOrBlank() }

    private fun buildIntrinsicsSignature(row: Map<String, String>): String? {
        val values =
            listOf(
                stringValue(row, listOf("imageIntrinsics.fx", "imageFocalLength")),
                stringValue(row, listOf("imageIntrinsics.fy")),
                stringValue(row, listOf("imageIntrinsics.cx", "imagePrincipalPoint")),
                stringValue(row, listOf("imageIntrinsics.cy")),
                stringValue(row, listOf("imageIntrinsics.width", "imageDimensions")),
                stringValue(row, listOf("imageIntrinsics.height")),
            )
        return if (values.any { !it.isNullOrBlank() }) values.joinToString("|") else null
    }

    private fun nsToMs(value: Long?): Double? =
        value?.toDouble()?.div(1_000_000.0)

    private fun imageFileName(index: Int): String =
        "frame_${index.toString().padStart(6, '0')}.jpg"

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
        val validPoseCount: Int,
        val calibrationFrameCount: Int,
        val imageIntrinsicsCount: Int,
        val textureIntrinsicsCount: Int,
        val lensDistortionCount: Int,
        val imageIntrinsicsCoverageRatio: Double,
        val textureIntrinsicsCoverageRatio: Double,
        val lensDistortionCoverageRatio: Double,
        val timestampStartNs: Long?,
        val timestampEndNs: Long?,
        val intrinsicsModeCandidate: String,
        val intrinsicsChangedDuringRecording: Boolean,
        val legacySessionWithoutCalibration: Boolean,
        val qualityFlags: Map<String, Boolean>,
        val warnings: List<String>,
        val spaceReconstructionBlockers: List<String>,
        val recommendedCorrections: List<String>,
        val recommendedModelingRoutes: List<String>,
    )

    companion object {
        private const val ARTIFACT_DERIVED_DIR = "trajectreview"
        private const val ARTIFACT_IMAGES_DIR = "images"
        private const val ARTIFACT_INPUT_READINESS = "input_readiness.json"
        private const val ARTIFACT_SENSOR_QUALITY = "sensor_quality.json"
        private const val ARTIFACT_FRAME_POSE_INDEX = "frame_pose_index.csv"
        private const val ARTIFACT_CAMERA_CALIBRATION_SUMMARY = "camera_calibration_summary.json"
        private const val ARTIFACT_MEMBER_IDENTITY_MAP = "member_identity_map.json"
        private const val ARTIFACT_SESSION_PACKAGE = "session_package.json"
        private const val ARTIFACT_SPACE_HANDOFF_MANIFEST = "space_handoff_manifest.json"
        private const val ARTIFACT_ARCORE_POSE = "arcore_pose.jsonl"
    }
}
