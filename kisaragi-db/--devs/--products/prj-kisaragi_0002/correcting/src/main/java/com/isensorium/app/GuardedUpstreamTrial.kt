package com.isensorium.app

import org.json.JSONArray
import org.json.JSONObject

enum class CameraStackRoute(val routeId: String) {
    FROZEN_CAMERAX_ARCORE("frozen_camerax_arcore"),
    CORECAMERA_SHARED_CAMERA_TRIAL("corecamera_shared_camera_trial"),
    ;

    companion object {
        fun fromRouteId(value: String?): CameraStackRoute =
            entries.firstOrNull { it.routeId.equals(value, ignoreCase = true) } ?: FROZEN_CAMERAX_ARCORE
    }
}

data class RouteResolution(
    val requestedRoute: CameraStackRoute,
    val activeRoute: CameraStackRoute,
    val cutoverGateStatus: String,
    val fallbackReason: String? = null,
)

data class SessionAdapterMetadata(
    val adapterSeamId: String,
    val requestedRoute: String,
    val activeRoute: String,
    val cutoverGateStatus: String,
    val fallbackReason: String? = null,
    val rollbackAnchorTag: String,
    val rollbackAnchorCommit: String,
    val preservedOperations: List<String>,
)

object GuardedUpstreamTrialContract {
    const val adapterSeamId = "shared-camera-session-adapter"
    const val rollbackAnchorTag = "rollback-isensorium-pre-upstream-trial-2026-03-15-001"
    const val rollbackAnchorCommit = "c5656973ee190e2bb1e99d3cd806f813d4b7ce7a"
    private const val upstreamTrialPackageVersion = "upstream-trial-package/v1"
    private const val adapterPlanVersion = "shared-camera-session-adapter/v1"
    private const val evidenceProject = "coreCamera"
    private const val evidencePlanSet = "2026-03-14-001"
    private const val evidenceSessionId = "session-20260315-044922"
    private const val evidencePackageStatus = "READY"
    private const val cutoverGateHold = "HOLD_FROZEN_ROUTE"
    private const val cutoverGateReady = "READY_FOR_RUNTIME_WIRING"

    val preservedOperations = listOf("startSession", "stopSession", "findLatestSession")
    val requiredArtifacts = listOf(
        "session_manifest.json",
        "video.mp4",
        "imu.csv",
        "gnss.csv",
        "ble_scan.jsonl",
        "arcore_pose.jsonl",
        "video_frame_timestamps.csv",
        "video_events.jsonl",
    )

    fun resolve(requestedRouteValue: String, replacementRuntimeEnabled: Boolean): RouteResolution {
        val requestedRoute = CameraStackRoute.fromRouteId(requestedRouteValue)
        return if (requestedRoute == CameraStackRoute.CORECAMERA_SHARED_CAMERA_TRIAL && replacementRuntimeEnabled) {
            RouteResolution(
                requestedRoute = requestedRoute,
                activeRoute = CameraStackRoute.CORECAMERA_SHARED_CAMERA_TRIAL,
                cutoverGateStatus = cutoverGateReady,
            )
        } else if (requestedRoute == CameraStackRoute.CORECAMERA_SHARED_CAMERA_TRIAL) {
            RouteResolution(
                requestedRoute = requestedRoute,
                activeRoute = CameraStackRoute.FROZEN_CAMERAX_ARCORE,
                cutoverGateStatus = cutoverGateHold,
                fallbackReason = "coreCamera replacement stack is validated in the sibling project, but iSensorium runtime wiring is still disabled by the guarded cutover gate",
            )
        } else {
            RouteResolution(
                requestedRoute = requestedRoute,
                activeRoute = CameraStackRoute.FROZEN_CAMERAX_ARCORE,
                cutoverGateStatus = cutoverGateHold,
            )
        }
    }

    fun buildSessionAdapterMetadata(resolution: RouteResolution): SessionAdapterMetadata =
        SessionAdapterMetadata(
            adapterSeamId = adapterSeamId,
            requestedRoute = resolution.requestedRoute.routeId,
            activeRoute = resolution.activeRoute.routeId,
            cutoverGateStatus = resolution.cutoverGateStatus,
            fallbackReason = resolution.fallbackReason,
            rollbackAnchorTag = rollbackAnchorTag,
            rollbackAnchorCommit = rollbackAnchorCommit,
            preservedOperations = preservedOperations,
        )

    fun sessionAdapterMetadataJson(metadata: SessionAdapterMetadata): JSONObject =
        JSONObject()
            .put("adapterSeamId", metadata.adapterSeamId)
            .put("adapterPlanVersion", adapterPlanVersion)
            .put("requestedRoute", metadata.requestedRoute)
            .put("activeRoute", metadata.activeRoute)
            .put("cutoverGateStatus", metadata.cutoverGateStatus)
            .put("fallbackReason", metadata.fallbackReason)
            .put("rollbackAnchorTag", metadata.rollbackAnchorTag)
            .put("rollbackAnchorCommit", metadata.rollbackAnchorCommit)
            .put("preservedOperations", JSONArray(metadata.preservedOperations))

    fun sessionAdapterMetadataFromJson(json: JSONObject?): SessionAdapterMetadata? {
        if (json == null) return null
        val preservedOperations = buildList {
            val operations = json.optJSONArray("preservedOperations") ?: JSONArray()
            for (index in 0 until operations.length()) {
                add(operations.optString(index))
            }
        }.filter { it.isNotBlank() }
        return SessionAdapterMetadata(
            adapterSeamId = json.optString("adapterSeamId", adapterSeamId),
            requestedRoute = json.optString("requestedRoute", CameraStackRoute.FROZEN_CAMERAX_ARCORE.routeId),
            activeRoute = json.optString("activeRoute", CameraStackRoute.FROZEN_CAMERAX_ARCORE.routeId),
            cutoverGateStatus = json.optString("cutoverGateStatus", cutoverGateHold),
            fallbackReason = json.optString("fallbackReason").ifBlank { null },
            rollbackAnchorTag = json.optString("rollbackAnchorTag", rollbackAnchorTag),
            rollbackAnchorCommit = json.optString("rollbackAnchorCommit", rollbackAnchorCommit),
            preservedOperations = preservedOperations.ifEmpty { this.preservedOperations },
        )
    }

    fun guardedUpstreamTrialJson(resolution: RouteResolution): JSONObject =
        JSONObject()
            .put("status", "PREPARED")
            .put("requestedRoute", resolution.requestedRoute.routeId)
            .put("activeRoute", resolution.activeRoute.routeId)
            .put("cutoverGateStatus", resolution.cutoverGateStatus)
            .put("upstreamTrialPackageVersion", upstreamTrialPackageVersion)
            .put("upstreamTrialPackageStatus", evidencePackageStatus)
            .put("adapterSeamId", adapterSeamId)
            .put("requiredArtifacts", JSONArray(requiredArtifacts))
            .put("preservedOperations", JSONArray(preservedOperations))
            .put("evidenceProject", evidenceProject)
            .put("evidencePlanSet", evidencePlanSet)
            .put("evidenceSessionId", evidenceSessionId)
            .put("rollbackAnchorTag", rollbackAnchorTag)
            .put("rollbackAnchorCommit", rollbackAnchorCommit)
            .put(
                "guardRule",
                "keep the frozen CameraX + ARCore path as the default runtime route until explicit replacement wiring is validated inside iSensorium",
            )
            .put("replacementRuntimeEnabled", resolution.activeRoute == CameraStackRoute.CORECAMERA_SHARED_CAMERA_TRIAL)
            .put("fallbackReason", resolution.fallbackReason)
}
