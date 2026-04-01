package com.isensorium.app

import java.util.Locale

data class MainScreenFormState(
    val imuIntervalMs: Long,
    val gnssIntervalMs: Long,
    val bleIntervalMs: Long,
    val frameRecordEveryNUpdates: Int,
    val saveOnlyWhenTracking: Boolean,
    val bleEnabled: Boolean,
    val arCoreEnabled: Boolean,
    val recordingMode: RecordingMode,
)

data class SessionPresentation(
    val summaryText: String,
    val filesText: String,
)

data class RecordingConfigResolution(
    val config: RecordingConfig,
    val issue: RecordingIssue? = null,
)

class MainScreenController {

    fun buildRecordingConfig(formState: MainScreenFormState): RecordingConfig =
        resolveRecordingConfig(formState).config

    fun resolveRecordingConfig(formState: MainScreenFormState): RecordingConfigResolution {
        val normalizedBleIntervalMs =
            if (formState.recordingMode == RecordingMode.POCKET_RECORDING && formState.bleEnabled) {
                formState.bleIntervalMs.coerceAtLeast(5000L)
            } else {
                formState.bleIntervalMs
            }
        val normalizedArCoreEnabled =
            if (formState.recordingMode == RecordingMode.POCKET_RECORDING) {
                false
            } else {
                formState.arCoreEnabled
            }
        val normalizedArCoreIntervalMs = if (normalizedArCoreEnabled) 33L else 5000L
        val normalizedVideoIntervalMs = if (formState.recordingMode == RecordingMode.POCKET_RECORDING) 250L else 100L
        val normalizedFrameRecordEveryNUpdates =
            if (normalizedArCoreEnabled) {
                formState.frameRecordEveryNUpdates.coerceAtLeast(1)
            } else {
                1
            }
        val normalizedSaveOnlyWhenTracking = normalizedArCoreEnabled && formState.saveOnlyWhenTracking
        val config =
            RecordingConfig(
                videoFrameLogIntervalMs = normalizedVideoIntervalMs,
                imuIntervalMs = formState.imuIntervalMs,
                gnssIntervalMs = formState.gnssIntervalMs,
                bleIntervalMs = normalizedBleIntervalMs,
                arCoreIntervalMs = normalizedArCoreIntervalMs,
                bleEnabled = formState.bleEnabled,
                arCoreEnabled = normalizedArCoreEnabled,
                frameRecordEveryNUpdates = normalizedFrameRecordEveryNUpdates,
                saveOnlyWhenTracking = normalizedSaveOnlyWhenTracking,
                recordingMode = formState.recordingMode,
            )
        val issue =
            if (formState.recordingMode == RecordingMode.POCKET_RECORDING) {
                buildPocketModeIssue(
                    bleAdjusted = formState.bleEnabled && normalizedBleIntervalMs != formState.bleIntervalMs,
                    frameRecordSuppressed = formState.arCoreEnabled || formState.frameRecordEveryNUpdates != 1 || formState.saveOnlyWhenTracking,
                    config = config,
                )
            } else {
                null
            }
        return RecordingConfigResolution(config = config, issue = issue)
    }

    fun buildModeSummary(config: RecordingConfig, routeId: String): String {
        val sensorSummary =
            if (config.arCoreEnabled) {
                "主記録=${config.frameRecordEveryNUpdates} updateごと / trackingOnly=${config.saveOnlyWhenTracking} / IMU・GNSS・BLE を補助記録"
            } else if (config.bleEnabled) {
                "動画・IMU・GNSS を基準に、BLE を補助記録"
            } else {
                "動画・IMU・GNSS を基準に補助記録のみ"
            }
        return "記録モード: ${recordingModeLabel(config.recordingMode)} / route=$routeId / $sensorSummary"
    }

    fun buildPermissionDeniedIssue(): RecordingIssue =
        RecordingIssue(
            severity = RecordingIssueSeverity.ERROR,
            message = "カメラと録音の権限がないため、記録を開始できません。",
            suggestedAction = "権限ダイアログで「許可」を選び、再度開始してください。",
        )

    fun buildRouteChangeBlockedIssue(): RecordingIssue =
        RecordingIssue(
            severity = RecordingIssueSeverity.WARNING,
            message = "記録中は camera route を切り替えられません。",
            suggestedAction = "いったんセッションを停止してから route を変更してください。",
        )

    fun buildRefreshIssue(hasSession: Boolean): RecordingIssue? =
        if (hasSession) {
            null
        } else {
            RecordingIssue(
                severity = RecordingIssueSeverity.INFO,
                message = "まだ最新 session が見つかっていません。",
                suggestedAction = "まず 1 回記録してから「再読み込み」を実行してください。",
            )
        }

    fun buildPreviewStartIssue(error: Throwable): RecordingIssue =
        RecordingIssue(
            severity = RecordingIssueSeverity.ERROR,
            message = "プレビュー開始中に例外が発生しました: ${error.localizedMessage ?: error::class.java.simpleName}",
            suggestedAction = "端末の権限とカメラ状態を確認し、画面を再読み込みしてください。",
        )

    fun buildSessionStartIssue(config: RecordingConfig, error: Throwable): RecordingIssue =
        RecordingIssue(
            severity = RecordingIssueSeverity.ERROR,
            message =
                "${recordingModeLabel(config.recordingMode)}の開始中に例外が発生しました: ${error.localizedMessage ?: error::class.java.simpleName}",
            suggestedAction = "設定値を見直し、必要ならアプリを再起動してから再試行してください。",
        )

    fun buildRefreshExecutionIssue(error: Throwable): RecordingIssue =
        RecordingIssue(
            severity = RecordingIssueSeverity.ERROR,
            message = "session 再読み込み中に例外が発生しました: ${error.localizedMessage ?: error::class.java.simpleName}",
            suggestedAction = "session_manifest.json を確認し、必要ならアプリを再起動してください。",
        )

    fun buildSessionPresentation(session: RecordingSession, sessionElapsedSec: Double): SessionPresentation {
        val modeLabel = recordingModeLabel(session.recordingConfig.recordingMode)
        val summaryText =
            buildString {
                appendLine("Session: ${session.sessionId}")
                appendLine("Directory: ${session.sessionDir.absolutePath}")
                appendLine("Recording mode: ${session.recordingConfig.recordingMode.modeId} ($modeLabel)")
                appendLine(
                    "Camera route: requested=${session.adapterMetadata.requestedRoute}, active=${session.adapterMetadata.activeRoute}",
                )
                appendLine("Cutover gate: ${session.adapterMetadata.cutoverGateStatus} via ${session.adapterMetadata.adapterSeamId}")
                session.adapterMetadata.fallbackReason?.let { appendLine("Guard: $it") }
                appendLine(
                    "Started: wall=${session.timebase.sessionStartWallTimeMs} ms, mono=${session.timebase.sessionStartElapsedRealtimeNanos} ns",
                )
                if (sessionElapsedSec >= 0.0) {
                    appendLine(String.format(Locale.US, "Elapsed since start: %.1f sec", sessionElapsedSec))
                }
            }.trim()

        val filesText =
            session.listOutputFiles().joinToString("\n") { file ->
                String.format(Locale.US, "%s (%d bytes)", file.name, file.length())
            }.ifBlank { "No session outputs yet." }

        return SessionPresentation(summaryText = summaryText, filesText = filesText)
    }

    fun buildInitialStatus(): String = "現場の風景と経路を記録します。1. 条件設定⇒2. 収録⇒3. 転送"

    fun buildRefreshStatus(hasSession: Boolean, refreshedAtMillis: Long): String =
        if (hasSession) {
            "最新 session を再読み込みしました。($refreshedAtMillis)"
        } else {
            "まだ最新 session がありません。"
        }

    fun buildRouteSwitchToast(isGuardedSelected: Boolean): String =
        if (isGuardedSelected) {
            "guarded replacement route を選択しました。"
        } else {
            "frozen route を選択しました。"
        }

    private fun buildPocketModeIssue(
        bleAdjusted: Boolean,
        frameRecordSuppressed: Boolean,
        config: RecordingConfig,
    ): RecordingIssue {
        val adjustments =
            buildList {
                if (bleAdjusted) add("BLE 間隔を ${config.bleIntervalMs} ms に調整")
                if (frameRecordSuppressed) add("ポケット収納計測では主記録 frame を無効化")
            }
        val message =
            if (adjustments.isEmpty()) {
                "ポケット収納計測では、動画・IMU・GNSS を主軸に記録し、主記録 frame は扱いません。"
            } else {
                "ポケット収納計測向けに補助記録設定へ調整しました。"
            }
        val suggestedAction =
            if (adjustments.isEmpty()) {
                "収納したまま記録する場合は、画面を見続けなくてもよい状態で開始してください。"
            } else {
                adjustments.joinToString(" / ")
            }
        return RecordingIssue(
            severity = if (adjustments.isEmpty()) RecordingIssueSeverity.INFO else RecordingIssueSeverity.WARNING,
            message = message,
            suggestedAction = suggestedAction,
        )
    }

    private fun recordingModeLabel(mode: RecordingMode): String =
        when (mode) {
            RecordingMode.STANDARD_HANDHELD -> "通常計測"
            RecordingMode.POCKET_RECORDING -> "ポケット収納計測"
        }
}
