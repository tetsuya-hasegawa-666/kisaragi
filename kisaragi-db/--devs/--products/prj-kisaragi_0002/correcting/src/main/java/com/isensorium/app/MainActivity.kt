package com.isensorium.app

import android.Manifest
import android.content.Intent
import android.content.Context
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.PowerManager
import android.os.Environment
import android.os.SystemClock
import android.provider.OpenableColumns
import android.text.InputType
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.CameraSelector
import androidx.core.content.ContextCompat
import androidx.documentfile.provider.DocumentFile
import com.google.android.material.button.MaterialButton
import com.google.android.material.materialswitch.MaterialSwitch
import com.isensorium.app.databinding.ActivityMainBinding
import org.json.JSONObject
import java.io.BufferedOutputStream
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream
import kotlin.concurrent.thread

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var recordingCoordinator: RecordingCoordinator
    private val mainScreenController = MainScreenController()
    private val preferences by lazy { getSharedPreferences("guarded_upstream_trial", Context.MODE_PRIVATE) }
    private var currentSession: RecordingSession? = null
    private var routeTransitionInProgress: Boolean = false
    private var runtimeIssue: RecordingIssue? = null
    private var configurationIssue: RecordingIssue? = null
    private val isCorrectingApp: Boolean by lazy { packageName == "com.reviework.correcting" }
    private val correctingDataCheckService by lazy { CorrectingDataCheckService() }
    private var dataCheckInProgress: Boolean = false
    private var transferInProgress: Boolean = false
    private var latestDataCheckResult: CorrectingDataCheckResult? = null
    private var checkedSessionId: String? = null
    private var successfulDataCheckCount: Int = 0
    private var saveDestinationSyncInProgress: Boolean = false
    private var saveDestinationStatusMessage: String? = null
    private var transferDestinationStatusMessage: String? = null
    private var transferDestinationUri: Uri? = null
    private var captureModeSyncInProgress: Boolean = false
    private var frameRecordEveryNUpdatesState: Int = 1
    private var saveOnlyWhenTrackingState: Boolean = true
    private var processingWakeLock: PowerManager.WakeLock? = null
    private val uiHandler = Handler(Looper.getMainLooper())
    private var latestSessionStatusText: String = ""
    private var latestSessionRecording: Boolean = false
    private var stopInProgress: Boolean = false
    private var stopRequestedElapsedSeconds: Long? = null
    private val selectedTransferSessionIds: MutableSet<String> = linkedSetOf()
    private val selectedTransferGroupsState: MutableSet<TransferGroup> =
        linkedSetOf(
            TransferGroup.CAPTURE,
            TransferGroup.SENSORS,
            TransferGroup.DERIVED,
            TransferGroup.IMAGES,
        )
    private val recordingElapsedRunnable =
        object : Runnable {
            override fun run() {
                renderCurrentStatus()
                if (latestSessionRecording) {
                    uiHandler.postDelayed(this, 1_000L)
                }
            }
        }

    private val permissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { result ->
            val requiredGranted = requiredPermissions.all {
                result[it] == true || ContextCompat.checkSelfPermission(this, it) == PackageManager.PERMISSION_GRANTED
            }
            if (requiredGranted) {
                runtimeIssue = null
                refreshConfigurationState()
                startCamera()
            } else {
                runtimeIssue = mainScreenController.buildPermissionDeniedIssue()
                refreshDisplayedIssue()
                renderState(runtimeIssue!!.message)
            }
        }

    private val saveDestinationLauncher =
        registerForActivityResult(ActivityResultContracts.OpenDocumentTree()) { uri ->
            if (uri == null) {
                renderSaveDestinationState("保存先の選択をキャンセルしました。")
                return@registerForActivityResult
            }
            runCatching {
                contentResolver.takePersistableUriPermission(
                    uri,
                    Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION,
                )
                preferences.edit().putString(PREF_SAVE_DESTINATION_TREE_URI, uri.toString()).apply()
                saveDestinationStatusMessage = null
                renderSaveDestinationState("保存先を更新しました。")
            }.onFailure { error ->
                renderSaveDestinationState("保存先の保持に失敗しました: ${error.message ?: error::class.java.simpleName}")
            }
        }

    private val transferDestinationLauncher =
        registerForActivityResult(ActivityResultContracts.CreateDocument("application/zip")) { uri ->
            if (uri == null) {
                renderTransferDestinationState("転送先の選択をキャンセルしました。")
                return@registerForActivityResult
            }
            runCatching {
                transferDestinationUri = uri
                transferDestinationStatusMessage = null
                renderTransferDestinationState("転送先を更新しました。")
                renderTransferState("転送先を更新しました。")
            }.onFailure { error ->
                renderTransferDestinationState("転送先の保持に失敗しました: ${error.message ?: error::class.java.simpleName}")
            }
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (!preferences.contains(PREF_GUARDED_ROUTE)) {
            preferences.edit().putBoolean(PREF_GUARDED_ROUTE, true).apply()
        }
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        configureForegroundKeepAwake()

        recordingCoordinator = buildRecordingCoordinator()

        binding.recordButton.setOnClickListener {
            if (recordingCoordinator.isRecording()) {
                stopRecordingAsync()
            } else {
                ensurePermissionsAndStart()
            }
        }

        binding.refreshButton.setOnClickListener {
            refreshLatestSessionDetails()
        }
        binding.dataCheckButton.setOnClickListener {
            if (latestDataCheckResult != null && !dataCheckInProgress) {
                showDataCheckDialog(latestDataCheckResult!!)
            } else {
                currentSession?.let { runCorrectingDataCheck(it, false, syncDerivedToLocalDestination = true) }
            }
                ?: Toast.makeText(this, "先に現場撮影データ保存を実行してください", Toast.LENGTH_SHORT).show()
        }
        binding.transferButton.setOnClickListener {
            runDriveTransfer()
        }
        binding.samplingConditionsButton.setOnClickListener {
            showSamplingConditionsDialog()
        }
        binding.transferDiscoveryButton.setOnClickListener {
            saveDestinationLauncher.launch(selectedLocalSaveDestinationUri())
        }
        binding.transferTargetButton.setOnClickListener { showTransferTargetDialog() }
        binding.selectTransferGroupsButton.setOnClickListener {
            showTransferGroupsDialog()
        }
        binding.selectTransferSessionButton.setOnClickListener {
            showTransferSessionPicker()
        }
        binding.manageTransferSessionsButton.setOnClickListener {
            showManageStoredSessionsDialog()
        }
        binding.recordingModeGroup.setOnCheckedChangeListener { _, _ ->
            if (!recordingCoordinator.isRecording()) {
                refreshConfigurationState()
            }
        }
        binding.captureModeSwitch.setOnCheckedChangeListener { _, isChecked ->
            if (captureModeSyncInProgress) {
                return@setOnCheckedChangeListener
            }
            if (recordingCoordinator.isRecording()) {
                syncCaptureModeSwitchFromCurrentControls()
                Toast.makeText(this, "記録中は撮影モードを変更できません", Toast.LENGTH_SHORT).show()
                return@setOnCheckedChangeListener
            }
            applyCaptureModeSelection(isChecked)
        }
        binding.guardedRouteSwitch.isChecked = prefersGuardedReplacementRoute()
        binding.guardedRouteSwitch.isEnabled = BuildConfig.CORECAMERA_RUNTIME_ENABLED
        binding.guardedRouteSwitch.setOnCheckedChangeListener { _, isChecked ->
            if (routeTransitionInProgress) {
                binding.guardedRouteSwitch.isChecked = !isChecked
                return@setOnCheckedChangeListener
            }
            if (recordingCoordinator.isRecording()) {
                binding.guardedRouteSwitch.isChecked = !isChecked
                runtimeIssue = mainScreenController.buildRouteChangeBlockedIssue()
                refreshDisplayedIssue()
                Toast.makeText(this, runtimeIssue!!.suggestedAction, Toast.LENGTH_SHORT).show()
                return@setOnCheckedChangeListener
            }
            routeTransitionInProgress = true
            binding.guardedRouteSwitch.isEnabled = false
            preferences.edit().putBoolean(PREF_GUARDED_ROUTE, isChecked).apply()
            recordingCoordinator.shutdown()
            recordingCoordinator = buildRecordingCoordinator()
            currentSession = null
            runtimeIssue = null
            refreshSessionDetails(null)
            refreshConfigurationState()
            ensurePermissionsAndStartPreview()
            binding.guardedRouteSwitch.postDelayed({
                routeTransitionInProgress = false
                binding.guardedRouteSwitch.isEnabled = BuildConfig.CORECAMERA_RUNTIME_ENABLED
            }, ROUTE_SWITCH_GUARD_MS)
            Toast.makeText(this, mainScreenController.buildRouteSwitchToast(isChecked), Toast.LENGTH_SHORT).show()
        }
        initializeCaptureModeControls()
        renderState(mainScreenController.buildInitialStatus())
        refreshConfigurationState()
        ensurePermissionsAndStartPreview()
        binding.recordButton.text = startRecordingButtonText()
        renderCorrectingDataCheck(null)
        renderTransferState(null)
        renderSaveDestinationState(null)
        renderTransferDestinationState(null)
        refreshRecordButtonState()
        renderBusyIndicator()
        updateBlockVisibility(recording = false)
    }

    override fun onDestroy() {
        uiHandler.removeCallbacks(recordingElapsedRunnable)
        releaseProcessingWakeLock()
        if (isCorrectingApp) {
            window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        }
        recordingCoordinator.shutdown()
        super.onDestroy()
    }

    override fun onResume() {
        super.onResume()
        recordingCoordinator.onHostResume()
    }

    override fun onPause() {
        recordingCoordinator.onHostPause()
        super.onPause()
    }

    private fun ensurePermissionsAndStartPreview() {
        if (hasRequiredPermissions()) {
            startCamera()
        } else {
            permissionLauncher.launch(allRequestedPermissions)
        }
    }

    private fun ensurePermissionsAndStart() {
        if (hasRequiredPermissions()) {
            val resolution = resolveRecordingConfig()
            runCatching {
                recordingCoordinator.updateRecordingConfig(resolution.config)
                recordingCoordinator.startSession()
                resetCorrectingWorkflowState()
                runtimeIssue = null
                refreshDisplayedIssue()
            }.onFailure { error ->
                runtimeIssue = mainScreenController.buildSessionStartIssue(resolution.config, error)
                refreshDisplayedIssue()
                renderState(runtimeIssue!!.message)
            }
        } else {
            permissionLauncher.launch(allRequestedPermissions)
        }
    }

    private fun hasRequiredPermissions(): Boolean =
        requiredPermissions.all {
            ContextCompat.checkSelfPermission(this, it) == PackageManager.PERMISSION_GRANTED
        }

    private fun buildRecordingCoordinator(): RecordingCoordinator =
        RecordingCoordinator(
            context = applicationContext,
            lifecycleOwner = this,
            previewView = binding.previewView,
            replacementPreviewImageView = binding.replacementPreviewImage,
            arCoreGlSurfaceView = binding.arCoreGlSurfaceView,
            statusListener = ::onSessionStateChanged,
            requestedRouteValue = selectedRoute().routeId,
        )

    private fun selectedRoute(): CameraStackRoute =
        if (BuildConfig.CORECAMERA_RUNTIME_ENABLED && prefersGuardedReplacementRoute()) {
            CameraStackRoute.CORECAMERA_SHARED_CAMERA_TRIAL
        } else {
            CameraStackRoute.FROZEN_CAMERAX_ARCORE
        }

    private fun prefersGuardedReplacementRoute(): Boolean =
        preferences.getBoolean(PREF_GUARDED_ROUTE, false)

    private fun startCamera() {
        runCatching {
            recordingCoordinator.startPreview(CameraSelector.DEFAULT_BACK_CAMERA)
            runtimeIssue = null
            refreshDisplayedIssue()
        }.onFailure { error ->
            runtimeIssue = mainScreenController.buildPreviewStartIssue(error)
            refreshDisplayedIssue()
            renderState(runtimeIssue!!.message)
        }
    }

    private fun onSessionStateChanged(state: SessionUiState) {
        runOnUiThread {
            currentSession = state.session
            runtimeIssue = state.issue
            if (state.session != null && selectedTransferSessionIds.isEmpty()) {
                selectedTransferSessionIds.add(state.session.sessionId)
            }
            if (state.session?.sessionId != checkedSessionId) {
                checkedSessionId = state.session?.sessionId
                latestDataCheckResult = null
                successfulDataCheckCount = 0
                selectedTransferSessionIds.clear()
                state.session?.sessionId?.let(selectedTransferSessionIds::add)
                renderTransferState(null)
            }
            latestSessionStatusText = state.statusText
            latestSessionRecording = state.recording
            if (!state.recording) {
                stopInProgress = false
                stopRequestedElapsedSeconds = null
            }
            binding.recordButton.text = startRecordingButtonText()
            binding.bleSwitch.isEnabled = !state.recording
            binding.captureModeSwitch.isEnabled = !state.recording
            binding.arcoreSwitch.isEnabled = !state.recording
            setInputsEnabled(!state.recording)
            showRecordingUi(state.recording)
            renderCurrentStatus()
            refreshDisplayedIssue()
            refreshSessionDetails(state.session)
            refreshRecordButtonState()
            renderBusyIndicator()
            uiHandler.removeCallbacks(recordingElapsedRunnable)
            if (state.recording) {
                uiHandler.post(recordingElapsedRunnable)
            }
            if (!state.recording) {
                refreshConfigurationState()
                if (isCorrectingApp && state.session != null) {
                    runPostRecordingPipeline(state.session)
                }
            }
        }
    }

    private fun renderState(message: String) {
        if (!latestSessionRecording) {
            latestSessionStatusText = message
        }
        binding.statusText.text = message
    }

    private fun renderCurrentStatus() {
        val rendered =
            if (latestSessionRecording) {
                buildRecordingElapsedStatus(
                    baseStatusText = latestSessionStatusText,
                    session = currentSession,
                    frozenElapsedSeconds = stopRequestedElapsedSeconds,
                )
            } else {
                latestSessionStatusText
            }
        binding.statusText.text = rendered
        binding.recordingOverlayText.text = rendered
    }

    private fun buildRecordingElapsedStatus(
        baseStatusText: String,
        session: RecordingSession?,
        frozenElapsedSeconds: Long? = null,
    ): String {
        val startedNs = session?.timebase?.sessionStartElapsedRealtimeNanos ?: 0L
        if (startedNs <= 0L) {
            return baseStatusText
        }
        val elapsedSec =
            frozenElapsedSeconds
                ?: (((SystemClock.elapsedRealtimeNanos() - startedNs).coerceAtLeast(0L)) / 1_000_000_000L)
        return "経過時間: ${formatElapsedDuration(elapsedSec)}\n$baseStatusText"
    }

    private fun formatElapsedDuration(totalSeconds: Long): String {
        val minutes = totalSeconds / 60
        val seconds = totalSeconds % 60
        return String.format(Locale.JAPAN, "%02d:%02d", minutes, seconds)
    }

    private fun stopRecordingAsync() {
        if (stopInProgress) {
            return
        }
        stopInProgress = true
        stopRequestedElapsedSeconds =
            currentSession?.timebase?.sessionStartElapsedRealtimeNanos?.let { startedNs ->
                ((SystemClock.elapsedRealtimeNanos() - startedNs).coerceAtLeast(0L)) / 1_000_000_000L
            }
        latestSessionStatusText = "停止処理を実行中です。"
        renderCurrentStatus()
        refreshRecordButtonState()
        renderBusyIndicator()
        thread {
            runCatching { recordingCoordinator.stopSession() }
                .onFailure { error ->
                    runOnUiThread {
                        stopInProgress = false
                        stopRequestedElapsedSeconds = null
                        runtimeIssue =
                            RecordingIssue(
                                severity = RecordingIssueSeverity.ERROR,
                                message = "停止処理に失敗しました: ${error.message ?: error::class.java.simpleName}",
                                suggestedAction = "app を再起動し、残った session を確認してください。",
                            )
                        latestSessionStatusText = runtimeIssue!!.message
                        renderCurrentStatus()
                        refreshDisplayedIssue()
                        refreshRecordButtonState()
                        renderBusyIndicator()
                    }
                }
        }
    }

    private fun refreshDisplayedIssue() {
        renderIssue(runtimeIssue ?: configurationIssue)
    }

    private fun renderIssue(issue: RecordingIssue?) {
        if (issue == null) {
            binding.issueText.visibility = View.GONE
            binding.issueText.text = ""
            return
        }
        binding.issueText.visibility = View.VISIBLE
        binding.issueText.text = "${issue.message}\n対応: ${issue.suggestedAction}"
    }

    private fun showRecordingUi(recording: Boolean) {
        binding.controlsCard.visibility = View.VISIBLE
        binding.recordingOverlay.visibility = View.GONE
        binding.recordButton.visibility = View.VISIBLE
        binding.recordButton.text =
            if (recording) {
                stopRecordingButtonText()
            } else {
                startRecordingButtonText()
            }
        refreshRecordButtonState()
        updateBlockVisibility(recording)
    }

    private fun renderModeState(config: RecordingConfig) {
        binding.recordingModeText.text = mainScreenController.buildModeSummary(config, selectedRoute().routeId)
    }

    private fun setInputsEnabled(enabled: Boolean) {
        listOf(
            binding.videoIntervalInput,
            binding.imuIntervalInput,
            binding.gnssIntervalInput,
            binding.bleIntervalInput,
            binding.arcoreIntervalInput,
            binding.standardModeRadio,
            binding.pocketModeRadio,
            binding.captureModeSwitch,
            binding.bleSwitch,
        ).forEach { it.isEnabled = enabled }
    }

    private fun resolveRecordingConfig(): RecordingConfigResolution =
        mainScreenController.resolveRecordingConfig(
            MainScreenFormState(
                imuIntervalMs = readMs(binding.imuIntervalInput, 20L),
                gnssIntervalMs = readMs(binding.gnssIntervalInput, 1000L),
                bleIntervalMs = readMs(binding.bleIntervalInput, 2000L),
                frameRecordEveryNUpdates = frameRecordEveryNUpdatesState,
                saveOnlyWhenTracking = saveOnlyWhenTrackingState,
                bleEnabled = binding.bleSwitch.isChecked,
                arCoreEnabled = binding.arcoreSwitch.isChecked,
                recordingMode = selectedRecordingMode(),
            ),
        )

    private fun refreshConfigurationState() {
        val resolution = resolveRecordingConfig()
        configurationIssue =
            if (
                selectedRoute() == CameraStackRoute.FROZEN_CAMERAX_ARCORE &&
                resolution.config.arCoreEnabled
            ) {
                RecordingIssue(
                    severity = RecordingIssueSeverity.INFO,
                    message = "frozen route では録画安定性を優先し、記録中の ARCore 収集を停止します。",
                    suggestedAction = "ARCore を使った pose 記録が必要な時は guarded replacement route を ON にしてください。",
                )
            } else {
                resolution.issue
            }
        renderModeState(resolution.config)
        refreshDisplayedIssue()
    }

    private fun selectedRecordingMode(): RecordingMode =
        if (binding.pocketModeRadio.isChecked) {
            RecordingMode.POCKET_RECORDING
        } else {
            RecordingMode.STANDARD_HANDHELD
        }

    private fun readMs(input: EditText, fallback: Long): Long =
        input.text?.toString()?.trim()?.toLongOrNull()?.coerceAtLeast(1L) ?: fallback

    private fun readInt(input: EditText, fallback: Int): Int =
        input.text?.toString()?.trim()?.toIntOrNull()?.coerceAtLeast(1) ?: fallback

    private fun refreshLatestSessionDetails() {
        runCatching {
            val refreshed = recordingCoordinator.findLatestSession()
            currentSession = refreshed ?: currentSession
            if (currentSession != null && selectedTransferSessionIds.isEmpty()) {
                currentSession?.sessionId?.let(selectedTransferSessionIds::add)
            }
            refreshSessionDetails(currentSession)
            runtimeIssue = mainScreenController.buildRefreshIssue(currentSession != null)
            renderState(mainScreenController.buildRefreshStatus(currentSession != null, System.currentTimeMillis()))
            refreshDisplayedIssue()
            Toast.makeText(
                this,
                if (currentSession == null) "最新 session はまだありません" else "再読み込みが完了しました",
                Toast.LENGTH_SHORT,
            ).show()
            if (isCorrectingApp && currentSession != null) {
                runCorrectingDataCheck(currentSession!!, false, syncDerivedToLocalDestination = true)
            }
        }.onFailure { error ->
            runtimeIssue = mainScreenController.buildRefreshExecutionIssue(error)
            refreshDisplayedIssue()
            renderState(runtimeIssue!!.message)
        }
    }

    private fun refreshSessionDetails(session: RecordingSession?) {
        if (session == null) {
            binding.sessionText.text = "現在表示できる session はありません。"
            binding.filesText.text = ""
            return
        }

        val sessionElapsedSec =
            if (session.timebase.sessionStartElapsedRealtimeNanos > 0L) {
                (SystemClock.elapsedRealtimeNanos() - session.timebase.sessionStartElapsedRealtimeNanos) / 1_000_000_000.0
            } else {
                -1.0
            }
        val presentation = mainScreenController.buildSessionPresentation(session, sessionElapsedSec)
        binding.sessionText.text = presentation.summaryText
        binding.filesText.text = presentation.filesText
        binding.dataCheckButton.isEnabled = !dataCheckInProgress
        val transferSessions = selectedTransferSessions()
        binding.transferButton.isEnabled =
            !transferInProgress &&
            transferSessions.isNotEmpty() &&
            selectedTransferDestinationUri() != null
        renderSaveDestinationState(null)
        renderTransferDestinationState(null)
        refreshRecordButtonState()
        updateBlockVisibility(recordingCoordinator.isRecording())
    }

    private fun resetCorrectingWorkflowState() {
        checkedSessionId = null
        latestDataCheckResult = null
        successfulDataCheckCount = 0
        selectedTransferSessionIds.clear()
        renderCorrectingDataCheck(null)
        renderTransferState("収録後に転送Dataを選択できます。")
    }

    private fun runPostRecordingPipeline(session: RecordingSession) {
        val rawGroups = setOf(TransferGroup.CAPTURE, TransferGroup.SENSORS)
        syncSessionToSelectedLocalDestinationIfNeeded(
            session = session,
            groups = rawGroups,
            inProgressMessage = "端末保存先へ保存中です。",
            successMessage = "保存先へ保存しました。品質確認を開始します。",
            failureMessagePrefix = "保存先への保存に失敗しました",
        ) {
            runCorrectingDataCheck(session, autoTriggered = true, syncDerivedToLocalDestination = true)
        }
    }

    private fun runCorrectingDataCheck(
        session: RecordingSession,
        autoTriggered: Boolean,
        syncDerivedToLocalDestination: Boolean,
    ) {
        if (!isCorrectingApp || dataCheckInProgress) {
            return
        }
        dataCheckInProgress = true
        binding.dataCheckButton.isEnabled = false
        binding.dataCheckText.text =
            if (autoTriggered) {
                "収録を保存しました。自動で品質確認を実行中です。"
            } else {
                "品質確認を実行中です。"
            }
        renderBusyIndicator()
        thread {
            val result = runCatching { correctingDataCheckService.run(session.sessionDir) }
            runOnUiThread {
                dataCheckInProgress = false
                binding.dataCheckButton.isEnabled = true
                renderBusyIndicator()
                result.onSuccess {
                    checkedSessionId = session.sessionId
                    latestDataCheckResult = it
                    successfulDataCheckCount += 1
                    renderCorrectingDataCheck(it)
                    renderTransferState(null)
                    if (syncDerivedToLocalDestination) {
                        syncSessionToSelectedLocalDestinationIfNeeded(
                            session = session,
                            groups = setOf(TransferGroup.DERIVED),
                            inProgressMessage = "品質確認結果を端末保存先へ同期中です。",
                            successMessage = "品質確認結果を保存先へ同期しました。",
                            failureMessagePrefix = "品質確認結果の同期に失敗しました",
                        )
                    }
                    if (!autoTriggered) {
                        showDataCheckDialog(it)
                        Toast.makeText(this, "data-check を更新しました", Toast.LENGTH_SHORT).show()
                    }
                }.onFailure { error ->
                    latestDataCheckResult = null
                    binding.dataCheckText.text = "data-check に失敗しました: ${error.message ?: error::class.java.simpleName}"
                    if (!autoTriggered) {
                        Toast.makeText(this, "data-check に失敗しました", Toast.LENGTH_SHORT).show()
                    }
                }
            }
        }
    }

    private fun renderCorrectingDataCheck(result: CorrectingDataCheckResult?) {
        if (!isCorrectingApp) {
            return
        }
        binding.dataCheckText.text =
            if (result == null) {
                "収録後に品質確認できます。"
            } else {
                summarizeDataCheckIssues(result)
            }
    }

    private fun renderSyncMinimalSessionState(session: RecordingSession) {
        binding.sessionText.text = "Session: ${session.sessionId}"
        binding.filesText.text = ""
        binding.dataCheckText.text = "品質確認OK"
    }

    private fun summarizeDataCheckIssues(result: CorrectingDataCheckResult): String {
        val issues =
            buildList {
                addAll(result.missingRequiredInputs.map { "$it 不足" })
                addAll(result.blockers.map(::summarizeIssueLabel))
                addAll(result.warnings.map(::summarizeIssueLabel))
            }.filter { it.isNotBlank() }
                .distinct()
        return if (issues.isEmpty()) {
            "品質確認OK"
        } else {
            issues.joinToString(" / ")
        }
    }

    private fun summarizeIssueLabel(issue: String): String =
        when {
            issue.contains("video.mp4") -> "主動画不足"
            issue.contains("frame timeline") || issue.contains("video_frame_timestamps") -> "frame timeline 不足"
            issue.contains("imu.csv") -> "IMU 不足"
            issue.contains("BLE") || issue.contains("bt") -> "BLE 不足"
            issue.contains("arcore_pose") -> "pose 不足"
            issue.contains("pose がほぼ 0") -> "pose 不足"
            issue.contains("intrinsics がほぼ 0") -> "camera intrinsics 不足"
            issue.contains("camera intrinsics 対応率") -> "camera intrinsics 対応率"
            issue.contains("texture intrinsics 対応率") -> "texture intrinsics 対応率"
            issue.contains("lens distortion 対応率") -> "lens distortion 対応率"
            issue.contains("tracking が不安定") -> "tracking 不安定"
            issue.contains("time_delta_ms") -> "time delta"
            issue.contains("calibration export 実装前") -> "旧形式 data"
            issue.contains("読取試行") -> "calibration 読取失敗"
            issue.contains("sessionStartElapsedRealtimeNanos") -> "timebase 不足"
            else -> issue
        }

    private fun showDataCheckDialog(result: CorrectingDataCheckResult) {
        val detail =
            buildString {
                appendLine("data-check: ${result.sessionId}")
                appendLine("診断進行可: ${result.readyForDiagnose}")
                appendLine("modeling 着手可: ${result.readyForSpaceReconstruction}")
                appendLine("warning 付き続行可: ${result.allowModelingProceed}")
                appendLine("欠落入力: ${result.missingRequiredInputs.joinToString(", ").ifBlank { "なし" }}")
                appendLine("blocker: ${result.blockers.joinToString(", ").ifBlank { "なし" }}")
                appendLine("充足率: ${"%.2f".format(result.completenessScore)}")
                appendLine("pose 対応率: ${"%.2f".format(result.poseCoverageRatio)}")
                appendLine("camera intrinsics 対応率: ${"%.2f".format(result.imageIntrinsicsCoverageRatio)}")
                appendLine("lens distortion 対応率: ${"%.2f".format(result.lensDistortionCoverageRatio)}")
                appendLine("calibration frame 数: ${result.calibrationFrameCount}")
                appendLine("補正指示: ${result.recommendedCorrections.joinToString(" / ")}")
                append("保存先: ${result.derivedDir.absolutePath}")
            }
        AlertDialog.Builder(this)
            .setTitle("品質確認")
            .setMessage(detail)
            .setPositiveButton("閉じる", null)
            .show()
    }

    private fun runDriveTransfer() {
        if (!isCorrectingApp || transferInProgress) {
            return
        }
        val sessions = selectedTransferSessions()
        if (sessions.isEmpty()) {
            renderTransferState("転送するデータを選択してください。保存済み data が無い時は先に記録を停止してください。")
            return
        }
        val nonTransferable = sessions.filterNot(::canTransferSelectedSession)
        if (nonTransferable.isNotEmpty()) {
            renderTransferState(
                "選択した data の一部に data-check 結果がありません: ${
                    nonTransferable.joinToString(", ") { it.sessionId }
                }\n対処: 品質確認済みの data のみ選ぶか、先に品質確認を実行してください。",
            )
            return
        }
        if (selectedTransferDestinationUri() == null) {
            renderTransferState("転送先を選択すると転送できます。")
            return
        }
        if (selectedTransferGroups().isEmpty()) {
            renderTransferState("送信Dataset を 1 つ以上選ぶと転送できます。")
            return
        }
        transferInProgress = true
        binding.transferButton.isEnabled = false
        renderTransferState("Google Drive 転送を開始しています。")
        renderBusyIndicator()
        thread {
            val result =
                runCatching {
                    if (selectedTransferGroups().contains(TransferGroup.IMAGES)) {
                        sessions.forEach { correctingDataCheckService.exportImages(it.sessionDir) }
                    }
                    syncSessionToSelectedDestination(
                        sessions = sessions,
                        selectedGroups = selectedTransferGroups(),
                        successMessage = "Google Drive へ data を転送しました。",
                    )
                }
            runOnUiThread {
                transferInProgress = false
                renderBusyIndicator()
                binding.transferButton.isEnabled =
                    selectedTransferSessions().isNotEmpty() &&
                    selectedTransferDestinationUri() != null
                result.onSuccess {
                    transferDestinationUri = null
                    renderTransferState(it)
                    renderTransferDestinationState(null)
                    Toast.makeText(this, "Google Drive 転送が完了しました", Toast.LENGTH_SHORT).show()
                }.onFailure { error ->
                    renderTransferState(
                        "Google Drive 転送に失敗しました: ${error.message ?: error::class.java.simpleName}\n" +
                            "対処: 転送先を選択し直し、転送するデータと送信データセットが選ばれていることを確認してください。",
                    )
                    renderTransferDestinationState(null)
                    Toast.makeText(this, "Google Drive 転送に失敗しました", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }

    private fun renderTransferState(message: String?) {
        if (!isCorrectingApp) {
            binding.transferBlock.visibility = View.GONE
            binding.transferExecuteBlock.visibility = View.GONE
            return
        }
        val hasStoredSessions = loadStoredSessions().isNotEmpty()
        binding.transferBlock.visibility =
            if (!recordingCoordinator.isRecording() && (currentSession != null || hasStoredSessions)) View.VISIBLE else View.GONE
        val selectedSessions = selectedTransferSessions()
        binding.selectTransferSessionButton.isEnabled = !recordingCoordinator.isRecording()
        binding.manageTransferSessionsButton.isEnabled = !recordingCoordinator.isRecording() && hasStoredSessions
        binding.selectTransferGroupsButton.isEnabled = !recordingCoordinator.isRecording()
        binding.transferTargetButton.visibility = View.VISIBLE
        binding.transferExecuteBlock.visibility = binding.transferBlock.visibility
        binding.transferButton.isEnabled =
            !transferInProgress &&
            selectedSessions.isNotEmpty() &&
            selectedTransferDestinationUri() != null
        binding.transferText.text =
            message ?: transferRequirementSummary(selectedSessions)
    }

    private fun renderSaveDestinationState(statusMessage: String?) {
        if (!isCorrectingApp) {
            binding.transferDestinationText.visibility = View.GONE
            return
        }
        binding.transferDestinationText.visibility = View.VISIBLE
        binding.transferDiscoveryButton.isEnabled = !recordingCoordinator.isRecording() && !saveDestinationSyncInProgress
        if (statusMessage != null) {
            saveDestinationStatusMessage = statusMessage
        }
        if (saveDestinationSyncInProgress) {
            binding.transferDestinationText.visibility = View.VISIBLE
            binding.transferDestinationText.text = "端末保存先へ同期中です。"
            refreshRecordButtonState()
            renderBusyIndicator()
            return
        }
        val selectedUri = selectedLocalSaveDestinationUri()
        if (selectedUri == null) {
            binding.transferDestinationText.visibility = View.VISIBLE
            binding.transferDestinationText.text = "端末保存先：未設定"
        } else {
            binding.transferDestinationText.visibility = View.GONE
            binding.transferDestinationText.text = ""
        }
        refreshRecordButtonState()
        renderBusyIndicator()
    }

    private fun renderTransferDestinationState(statusMessage: String?) {
        if (!isCorrectingApp) {
            binding.transferTargetText.visibility = View.GONE
            return
        }
        binding.transferTargetButton.isEnabled = !recordingCoordinator.isRecording() && !transferInProgress
        if (statusMessage != null) {
            transferDestinationStatusMessage = statusMessage
        }
        binding.transferTargetText.visibility = View.GONE
        binding.transferTargetText.text = ""
        renderBusyIndicator()
    }

    private fun configureForegroundKeepAwake() {
        if (!isCorrectingApp) {
            return
        }
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        binding.root.keepScreenOn = true
        binding.previewView.keepScreenOn = true
    }

    private fun refreshRecordButtonState() {
        binding.recordButton.isEnabled =
            !stopInProgress && (recordingCoordinator.isRecording() || selectedLocalSaveDestinationUri() != null)
    }

    private fun renderBusyIndicator() {
        if (!isCorrectingApp) {
            binding.processingIndicatorLayout.visibility = View.GONE
            binding.transferProcessingIndicatorLayout.visibility = View.GONE
            return
        }
        val recordBusyState =
            when {
                saveDestinationSyncInProgress ->
                    "端末保存先へ同期中です。" to "次の収録はできますが、同期完了まで待機を推奨します。"
                dataCheckInProgress ->
                    "品質確認を実行中です。" to "次の収録はできますが、品質確認完了まで待機を推奨します。"
                stopInProgress ->
                    "停止処理を実行中です。" to "停止完了まで待機してください。"
                else -> null
            }
        if (recordBusyState == null) {
            binding.processingIndicatorLayout.visibility = View.GONE
            binding.processingStatusText.text = ""
            binding.processingRecommendationText.text = ""
        } else {
            binding.processingIndicatorLayout.visibility = View.VISIBLE
            binding.processingStatusText.text = recordBusyState.first
            binding.processingRecommendationText.text = recordBusyState.second
        }

        val transferBusyState =
            if (transferInProgress) {
                "転送を実行中です。" to "転送完了まで待機してください。"
            } else {
                null
            }
        if (transferBusyState == null) {
            binding.transferProcessingIndicatorLayout.visibility = View.GONE
            binding.transferProcessingStatusText.text = ""
            binding.transferProcessingRecommendationText.text = ""
        } else {
            binding.transferProcessingIndicatorLayout.visibility = View.VISIBLE
            binding.transferProcessingStatusText.text = transferBusyState.first
            binding.transferProcessingRecommendationText.text = transferBusyState.second
        }
        updateProcessingWakeLock()
    }

    private fun updateProcessingWakeLock() {
        if (!isCorrectingApp) {
            return
        }
        val shouldHoldWakeLock =
            recordingCoordinator.isRecording() ||
                stopInProgress ||
                saveDestinationSyncInProgress ||
                dataCheckInProgress ||
                transferInProgress
        if (!shouldHoldWakeLock) {
            releaseProcessingWakeLock()
            return
        }
        val wakeLock =
            processingWakeLock ?: run {
                val powerManager = getSystemService(Context.POWER_SERVICE) as PowerManager
                powerManager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "$packageName:correcting-active").apply {
                    setReferenceCounted(false)
                }.also { processingWakeLock = it }
            }
        if (!wakeLock.isHeld) {
            wakeLock.acquire(PROCESSING_WAKE_LOCK_TIMEOUT_MS)
        }
    }

    private fun releaseProcessingWakeLock() {
        processingWakeLock?.let { wakeLock ->
            if (wakeLock.isHeld) {
                wakeLock.release()
            }
        }
    }

    private fun showTransferTargetDialog() {
        val input = EditText(this)
        input.inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_URI
        input.setText(selectedTransferTargetUrl())
        AlertDialog.Builder(this)
            .setTitle("転送先を選択")
            .setMessage(
                "アドレスを入力してください。\n" +
                    "保存先を app へ設定する時は、下の「保存先fileを設定する」を押してください。\n" +
                    "Android 標準の保存画面が開くので、左上メニューなどから Google Drive を選び、zip 保存先 file を指定してください。",
            )
            .setView(input)
            .setNeutralButton("保存先fileを設定する") { _, _ ->
                val url = normalizeTransferTargetUrl(input.text?.toString().orEmpty())
                saveTransferTargetUrl(url)
                transferDestinationLauncher.launch(defaultTransferArchiveName())
                renderTransferState(
                    "Android の保存画面で zip 保存先 file を選択してください。" +
                        "\nGoogle Drive を使う時は、左上メニューなどから Google Drive を選んでください。" +
                        "\n選択が完了すると app に戻って転送先が設定されます。",
                )
            }
            .setPositiveButton("OK") { _, _ ->
                val url = normalizeTransferTargetUrl(input.text?.toString().orEmpty())
                saveTransferTargetUrl(url)
            }
            .setNegativeButton("キャンセル", null)
            .show()
    }

    private fun normalizeTransferTargetUrl(value: String): String =
        value.trim().ifBlank { DEFAULT_TARGET_DRIVE_FOLDER_URL }

    private fun saveTransferTargetUrl(url: String) {
        preferences.edit().putString(PREF_TRANSFER_TARGET_URL, url).apply()
        transferDestinationStatusMessage = null
        renderTransferDestinationState("転送先URLを更新しました。")
        renderTransferState("転送先URLを更新しました。")
    }

    private fun showSamplingConditionsDialog() {
        val dialogView = layoutInflater.inflate(R.layout.dialog_sampling_conditions, null)
        val captureSwitch = dialogView.findViewById<MaterialSwitch>(R.id.dialogCaptureModeSwitch)
        val bleSwitch = dialogView.findViewById<MaterialSwitch>(R.id.dialogBleSwitch)
        val frameRecordEveryInput = dialogView.findViewById<EditText>(R.id.dialogFrameRecordEveryInput)
        val trackingOnlySwitch = dialogView.findViewById<MaterialSwitch>(R.id.dialogTrackingOnlySwitch)
        val frameRecordEveryContainer = dialogView.findViewById<View>(R.id.dialogFrameRecordEveryContainer)
        val frameRecordNoteText = dialogView.findViewById<TextView>(R.id.dialogFrameRecordNoteText)
        val videoSupplementNoteText = dialogView.findViewById<TextView>(R.id.dialogVideoSupplementNoteText)
        val imuInput = dialogView.findViewById<EditText>(R.id.dialogImuIntervalInput)
        val gnssInput = dialogView.findViewById<EditText>(R.id.dialogGnssIntervalInput)
        val bleInput = dialogView.findViewById<EditText>(R.id.dialogBleIntervalInput)

        captureSwitch.isChecked = binding.captureModeSwitch.isChecked
        bleSwitch.isChecked = binding.bleSwitch.isChecked
        frameRecordEveryInput.setText(frameRecordEveryNUpdatesState.toString())
        frameRecordEveryInput.inputType = InputType.TYPE_CLASS_NUMBER
        trackingOnlySwitch.isChecked = saveOnlyWhenTrackingState
        imuInput.setText(binding.imuIntervalInput.text)
        gnssInput.setText(binding.gnssIntervalInput.text)
        bleInput.setText(binding.bleIntervalInput.text)
        val refreshSamplingDialogState = {
            val captureEnabled = captureSwitch.isChecked
            frameRecordEveryContainer.isEnabled = captureEnabled
            frameRecordEveryInput.isEnabled = captureEnabled
            trackingOnlySwitch.isEnabled = captureEnabled
            frameRecordNoteText.alpha = if (captureEnabled) 1.0f else 0.5f
            videoSupplementNoteText.alpha = if (captureEnabled) 1.0f else 0.7f
            bleInput.isEnabled = bleSwitch.isChecked
            if (!captureEnabled) {
                trackingOnlySwitch.isChecked = false
            }
        }
        captureSwitch.setOnCheckedChangeListener { _, _ -> refreshSamplingDialogState() }
        bleSwitch.setOnCheckedChangeListener { _, _ -> refreshSamplingDialogState() }
        refreshSamplingDialogState()

        AlertDialog.Builder(this)
            .setTitle("サンプリング条件")
            .setView(dialogView)
            .setPositiveButton("確定") { _, _ ->
                binding.captureModeSwitch.isChecked = captureSwitch.isChecked
                binding.bleSwitch.isChecked = bleSwitch.isChecked
                frameRecordEveryNUpdatesState = readInt(frameRecordEveryInput, 1).coerceAtLeast(1)
                saveOnlyWhenTrackingState = captureSwitch.isChecked && trackingOnlySwitch.isChecked
                binding.imuIntervalInput.setText(imuInput.text)
                binding.gnssIntervalInput.setText(gnssInput.text)
                binding.bleIntervalInput.setText(bleInput.text)
                refreshConfigurationState()
                renderTransferState("サンプリング条件を更新しました。")
            }
            .setNegativeButton("キャンセル", null)
            .show()
    }

    private fun selectedTransferSessions(): List<RecordingSession> {
        val storedById = loadStoredSessions().associateBy { it.sessionId }
        if (selectedTransferSessionIds.isEmpty()) {
            return currentSession?.let(::listOf) ?: emptyList()
        }
        return selectedTransferSessionIds.mapNotNull { selectedId ->
            if (currentSession?.sessionId == selectedId) currentSession else storedById[selectedId]?.recordingSession
        }
    }

    private fun showTransferGroupsDialog() {
        val groups = TransferGroup.values()
        val labels = groups.map { group ->
            "${group.label}\n${group.relativePaths.joinToString(", ")}"
        }.toTypedArray()
        val checkedItems = groups.map { group -> selectedTransferGroupsState.contains(group) }.toBooleanArray()
        AlertDialog.Builder(this)
            .setTitle("送信データセットの選択")
            .setMultiChoiceItems(labels, checkedItems) { _, which, isChecked ->
                val group = groups[which]
                if (isChecked) {
                    selectedTransferGroupsState.add(group)
                } else {
                    selectedTransferGroupsState.remove(group)
                }
            }
            .setPositiveButton("確定") { _, _ ->
                renderTransferState(null)
            }
            .setNegativeButton("キャンセル", null)
            .show()
    }

    private fun showTransferSessionPicker() {
        loadStoredSessionsWithFreshDataCheck("転送Data 一覧を更新中です。") { summaries ->
            if (summaries.isEmpty()) {
                Toast.makeText(this, "転送できる data がまだありません", Toast.LENGTH_SHORT).show()
                return@loadStoredSessionsWithFreshDataCheck
            }
            val root =
                LinearLayout(this).apply {
                    orientation = LinearLayout.VERTICAL
                    setPadding(dp(20), dp(16), dp(20), dp(8))
                }
            val backButton =
                MaterialButton(this, null, com.google.android.material.R.attr.materialButtonOutlinedStyle).apply {
                    text = "戻る"
                    layoutParams =
                        LinearLayout.LayoutParams(
                            LinearLayout.LayoutParams.MATCH_PARENT,
                            LinearLayout.LayoutParams.WRAP_CONTENT,
                        )
                }
            val headerText =
                TextView(this).apply {
                    text = "転送する data を複数選択できます"
                    textAlignment = View.TEXT_ALIGNMENT_VIEW_START
                    layoutParams =
                        LinearLayout.LayoutParams(
                            LinearLayout.LayoutParams.MATCH_PARENT,
                            LinearLayout.LayoutParams.WRAP_CONTENT,
                        ).apply {
                            topMargin = dp(12)
                        }
                }
            val listContainer =
                LinearLayout(this).apply {
                    orientation = LinearLayout.VERTICAL
                }
            val scrollView =
                ScrollView(this).apply {
                    addView(
                        listContainer,
                        ViewGroup.LayoutParams(
                            ViewGroup.LayoutParams.MATCH_PARENT,
                            ViewGroup.LayoutParams.WRAP_CONTENT,
                        ),
                    )
                }
            val footerButton =
                MaterialButton(this).apply {
                    text = "OK"
                    layoutParams =
                        LinearLayout.LayoutParams(
                            LinearLayout.LayoutParams.MATCH_PARENT,
                            LinearLayout.LayoutParams.WRAP_CONTENT,
                        ).apply {
                            topMargin = dp(12)
                        }
                }
            root.addView(backButton)
            root.addView(headerText)
            root.addView(
                scrollView,
                LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    dp(420),
                ).apply {
                    topMargin = dp(12)
                },
            )
            root.addView(footerButton)

            val dialog =
                AlertDialog.Builder(this)
                    .setTitle("転送Data選択")
                    .setView(root)
                    .create()

            fun buildSummaryText(summary: StoredSessionSummary): String =
                buildString {
                    if (selectedTransferSessionIds.contains(summary.sessionId)) {
                        append("選択中\n")
                    }
                    append(summary.displayLabel())
                    append("\n取得日時: ${summary.startedAtLabel}")
                    append("\n長さ: ${summary.durationLabel}")
                }

            fun renderButtons() {
                listContainer.removeAllViews()
                summaries.forEach { summary ->
                    val button =
                        MaterialButton(this, null, com.google.android.material.R.attr.materialButtonOutlinedStyle).apply {
                            text = buildSummaryText(summary)
                            textAlignment = View.TEXT_ALIGNMENT_VIEW_START
                            layoutParams =
                                LinearLayout.LayoutParams(
                                    LinearLayout.LayoutParams.MATCH_PARENT,
                                    LinearLayout.LayoutParams.WRAP_CONTENT,
                                ).apply {
                                    bottomMargin = dp(8)
                                }
                            setOnClickListener {
                                if (!selectedTransferSessionIds.add(summary.sessionId)) {
                                    selectedTransferSessionIds.remove(summary.sessionId)
                                }
                                renderButtons()
                            }
                        }
                    listContainer.addView(button)
                    if (summary.hasConcerns) {
                        val concernText =
                            TextView(this).apply {
                                text = summary.concernLine()
                                textAlignment = View.TEXT_ALIGNMENT_VIEW_START
                                layoutParams =
                                    LinearLayout.LayoutParams(
                                        LinearLayout.LayoutParams.MATCH_PARENT,
                                        LinearLayout.LayoutParams.WRAP_CONTENT,
                                    ).apply {
                                        bottomMargin = dp(8)
                                        marginStart = dp(8)
                                    }
                            }
                        listContainer.addView(concernText)
                    }
                }
            }

            backButton.setOnClickListener { dialog.dismiss() }
            footerButton.setOnClickListener {
                renderTransferState(null)
                dialog.dismiss()
            }
            renderButtons()
            dialog.show()
        }
    }

    private fun showManageStoredSessionsDialog() {
        loadStoredSessionsWithFreshDataCheck("保存済み Data 一覧を更新中です。") { initialSummaries ->
            if (initialSummaries.isEmpty()) {
                Toast.makeText(this, "保存済み data がまだありません", Toast.LENGTH_SHORT).show()
                return@loadStoredSessionsWithFreshDataCheck
            }
            val summaries = initialSummaries.toMutableList()
            val deleteTargets = linkedSetOf<String>()
            var deleteMode = false

            val root =
                LinearLayout(this).apply {
                    orientation = LinearLayout.VERTICAL
                    setPadding(dp(20), dp(16), dp(20), dp(8))
                }
            val backButton =
                MaterialButton(this, null, com.google.android.material.R.attr.materialButtonOutlinedStyle).apply {
                    text = "戻る"
                    layoutParams =
                        LinearLayout.LayoutParams(
                            LinearLayout.LayoutParams.MATCH_PARENT,
                            LinearLayout.LayoutParams.WRAP_CONTENT,
                        )
                }
            val modeSwitch =
                MaterialSwitch(this).apply {
                    text = "OFF：名称変更、ON：削除モード"
                    isChecked = false
                    layoutParams =
                        LinearLayout.LayoutParams(
                            LinearLayout.LayoutParams.MATCH_PARENT,
                            LinearLayout.LayoutParams.WRAP_CONTENT,
                        ).apply {
                            topMargin = dp(12)
                        }
                }

            val listContainer =
                LinearLayout(this).apply {
                    orientation = LinearLayout.VERTICAL
                }
            val scrollView =
                ScrollView(this).apply {
                    addView(
                        listContainer,
                        ViewGroup.LayoutParams(
                            ViewGroup.LayoutParams.MATCH_PARENT,
                            ViewGroup.LayoutParams.WRAP_CONTENT,
                        ),
                    )
                }

            val footerRow =
                LinearLayout(this).apply {
                    orientation = LinearLayout.HORIZONTAL
                    setPadding(0, dp(12), 0, 0)
                }
            val deleteButton =
                MaterialButton(this).apply {
                    text = "削除実行"
                    isEnabled = false
                    layoutParams =
                        LinearLayout.LayoutParams(
                            LinearLayout.LayoutParams.MATCH_PARENT,
                            LinearLayout.LayoutParams.WRAP_CONTENT,
                        )
                }
            footerRow.addView(deleteButton)

            root.addView(backButton)
            root.addView(modeSwitch)
            root.addView(
                scrollView,
                LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    dp(420),
                ).apply {
                    topMargin = dp(12)
                },
            )
            root.addView(footerRow)

            val dialog =
                AlertDialog.Builder(this)
                    .setTitle("Data一覧＋名称変更")
                    .setView(root)
                    .create()

            fun refreshState() {
                deleteButton.isEnabled = deleteMode && deleteTargets.isNotEmpty()
                modeSwitch.isChecked = deleteMode
            }

            fun buildSummaryText(summary: StoredSessionSummary): String =
                buildString {
                    if (deleteMode && deleteTargets.contains(summary.sessionId)) {
                        append("削除対象\n")
                    }
                    append(summary.displayLabel())
                    append("\n取得日時: ${summary.startedAtLabel}")
                    append("\n長さ: ${summary.durationLabel}")
                    if (summary.hasConcerns) {
                        append("\n${summary.concernLine()}")
                    }
                }

            fun refreshSummaries(): Boolean {
                summaries.clear()
                summaries.addAll(loadStoredSessions())
                deleteTargets.retainAll(summaries.map { it.sessionId }.toSet())
                if (summaries.isEmpty()) {
                    dialog.dismiss()
                    Toast.makeText(this, "保存済み data がなくなりました", Toast.LENGTH_SHORT).show()
                    refreshSessionDetails(currentSession)
                    renderTransferState(null)
                    return false
                }
                return true
            }

            fun renderButtons() {
                listContainer.removeAllViews()
                summaries.forEach { summary ->
                    val button =
                        MaterialButton(this, null, com.google.android.material.R.attr.materialButtonOutlinedStyle).apply {
                            text = buildSummaryText(summary)
                            textAlignment = View.TEXT_ALIGNMENT_VIEW_START
                            layoutParams =
                                LinearLayout.LayoutParams(
                                    LinearLayout.LayoutParams.MATCH_PARENT,
                                    LinearLayout.LayoutParams.WRAP_CONTENT,
                                ).apply {
                                    bottomMargin = dp(8)
                                }
                            setOnClickListener {
                                if (deleteMode) {
                                    if (!deleteTargets.add(summary.sessionId)) {
                                        deleteTargets.remove(summary.sessionId)
                                    }
                                    refreshState()
                                    renderButtons()
                                } else {
                                    showRenameTransferSessionDialog(summary) {
                                        if (refreshSummaries()) {
                                            refreshState()
                                            renderButtons()
                                        }
                                    }
                                }
                            }
                        }
                    listContainer.addView(button)
                    if (deleteMode && deleteTargets.contains(summary.sessionId)) {
                        val cautionText =
                            TextView(this).apply {
                                text = "削除対象です"
                                textAlignment = View.TEXT_ALIGNMENT_VIEW_START
                                layoutParams =
                                    LinearLayout.LayoutParams(
                                        LinearLayout.LayoutParams.MATCH_PARENT,
                                        LinearLayout.LayoutParams.WRAP_CONTENT,
                                    ).apply {
                                        bottomMargin = dp(8)
                                        marginStart = dp(8)
                                    }
                            }
                        listContainer.addView(cautionText)
                    }
                }
            }

            modeSwitch.setOnCheckedChangeListener { _, isChecked ->
                deleteMode = isChecked
                if (!deleteMode) {
                    deleteTargets.clear()
                }
                refreshState()
                renderButtons()
            }
            backButton.setOnClickListener { dialog.dismiss() }
            deleteButton.setOnClickListener {
                val targetIds = deleteTargets.toSet()
                if (targetIds.isEmpty()) {
                    return@setOnClickListener
                }
                deleteStoredSessions(targetIds)
                if (refreshSummaries()) {
                    refreshState()
                    renderButtons()
                }
            }

            refreshState()
            renderButtons()
            dialog.show()
        }
    }

    private fun loadStoredSessionsWithFreshDataCheck(
        progressMessage: String,
        onLoaded: (List<StoredSessionSummary>) -> Unit,
    ) {
        renderTransferState(progressMessage)
        thread {
            val sessionsRoot = File(getExternalFilesDir(Environment.DIRECTORY_DOCUMENTS), "sessions")
            val dirs = sessionsRoot.listFiles { file -> file.isDirectory }?.sortedByDescending { it.lastModified() } ?: emptyList()
            val freshResults =
                dirs.associate { dir ->
                    dir.name to runCatching { correctingDataCheckService.inspect(dir) }.getOrNull()
                }.filterValues { it != null }
                    .mapValues { it.value!! }
            val refreshed = loadStoredSessions(freshResults)
            runOnUiThread {
                renderTransferState(null)
                onLoaded(refreshed)
            }
        }
    }

    private fun showRenameTransferSessionDialog(summary: StoredSessionSummary, onUpdated: () -> Unit) {
        val input = EditText(this)
        input.setText(summary.sessionId)
        val dialog =
            AlertDialog.Builder(this)
                .setTitle("Data名を変更")
                .setView(input)
                .setPositiveButton("変更", null)
                .setNegativeButton("キャンセル", null)
                .create()
        dialog.setOnShowListener {
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener {
                val newName = input.text?.toString()?.trim().orEmpty()
                if (renameStoredSession(summary, newName)) {
                    onUpdated()
                    dialog.dismiss()
                }
            }
        }
        dialog.show()
    }

    private fun renameStoredSession(summary: StoredSessionSummary, newName: String): Boolean {
        if (newName.isBlank()) {
            Toast.makeText(this, "データ名を入力してください", Toast.LENGTH_SHORT).show()
            return false
        }
        if (!Regex("^[A-Za-z0-9._-]+$").matches(newName)) {
            Toast.makeText(this, "半角英数字と . _ - のみ使えます", Toast.LENGTH_SHORT).show()
            return false
        }
        val targetDir = File(summary.sessionDir.parentFile, newName)
        if (targetDir.exists()) {
            Toast.makeText(this, "同名 directory が既にあります", Toast.LENGTH_SHORT).show()
            return false
        }
        if (!summary.sessionDir.renameTo(targetDir)) {
            Toast.makeText(this, "データ名の変更に失敗しました", Toast.LENGTH_SHORT).show()
            return false
        }
        if (selectedTransferSessionIds.remove(summary.sessionId)) {
            selectedTransferSessionIds.add(newName)
        }
        if (currentSession?.sessionId == summary.sessionId) {
            currentSession = buildRecordingSessionFromDir(targetDir)
        }
        renderTransferState("データ名を変更しました。")
        refreshSessionDetails(currentSession)
        return true
    }

    private fun deleteStoredSessions(sessionIds: Set<String>) {
        if (sessionIds.isEmpty()) {
            return
        }
        var deletedCount = 0
        var archiveDeleted = false
        sessionIds.forEach { sessionId ->
            val summary = loadStoredSessions().firstOrNull { it.sessionId == sessionId } ?: return@forEach
            val localDeleted = summary.sessionDir.deleteRecursively()
            val mirroredDeleted = deleteSessionFromSelectedLocalDestination(sessionId)
            archiveDeleted = deleteGeneratedArchivesFromSelectedLocalDestination() || archiveDeleted
            if (localDeleted) {
                deletedCount += 1
                selectedTransferSessionIds.remove(sessionId)
                if (checkedSessionId == sessionId) {
                    checkedSessionId = null
                    latestDataCheckResult = null
                    successfulDataCheckCount = 0
                    renderCorrectingDataCheck(null)
                }
                if (currentSession?.sessionId == sessionId) {
                    currentSession = loadStoredSessions().firstOrNull()?.recordingSession
                }
            } else if (mirroredDeleted) {
                selectedTransferSessionIds.remove(sessionId)
            }
        }
        renderTransferState(
            if (deletedCount > 0) {
                if (archiveDeleted) {
                    "$deletedCount 件の data を削除し、端末保存先の転送 zip も整理しました。"
                } else {
                    "$deletedCount 件の data を削除しました。"
                }
            } else {
                "削除できる data がありませんでした。"
            },
        )
        refreshSessionDetails(currentSession)
    }

    private fun deleteSessionFromSelectedLocalDestination(sessionId: String): Boolean {
        val destinationUri = selectedLocalSaveDestinationUri() ?: return false
        val rootTree = DocumentFile.fromTreeUri(this, destinationUri) ?: return false
        migrateLegacyTransferLayoutIfNeeded(rootTree)
        val target = rootTree.findFile(sessionId) ?: return false
        return target.delete()
    }

    private fun deleteGeneratedArchivesFromSelectedLocalDestination(): Boolean {
        val destinationUri = selectedLocalSaveDestinationUri() ?: return false
        val rootTree = DocumentFile.fromTreeUri(this, destinationUri) ?: return false
        var deletedAny = false
        rootTree.listFiles().forEach { child ->
            if (!child.isFile) {
                return@forEach
            }
            val name = child.name.orEmpty()
            if (isGeneratedTransferArchiveName(name) && child.delete()) {
                deletedAny = true
            }
        }
        return deletedAny
    }

    private fun isGeneratedTransferArchiveName(name: String): Boolean {
        if (!name.endsWith(".zip", ignoreCase = true)) {
            return false
        }
        if (name.startsWith("trajectreview-correcting")) {
            return true
        }
        return Regex(""".+-session-\d{8}-\d{6}\.zip""").matches(name)
    }

    private fun dp(value: Int): Int =
        (value * resources.displayMetrics.density).toInt()

    private fun loadStoredSessions(
        freshResults: Map<String, CorrectingDataCheckResult> = emptyMap(),
    ): List<StoredSessionSummary> {
        val sessionsRoot = File(getExternalFilesDir(Environment.DIRECTORY_DOCUMENTS), "sessions")
        return sessionsRoot.listFiles { file -> file.isDirectory }?.mapNotNull { dir ->
            buildStoredSessionSummary(dir, freshResults[dir.name])
        }?.sortedByDescending { it.startedAtMillis } ?: emptyList()
    }

    private fun buildStoredSessionSummary(
        sessionDir: File,
        freshResult: CorrectingDataCheckResult? = null,
    ): StoredSessionSummary? {
        val recordingSession = buildRecordingSessionFromDir(sessionDir) ?: return null
        val manifest = readJsonObjectOrNull(recordingSession.manifestFile)
        val startedAtMillis = recordingSession.timebase.sessionStartWallTimeMs
        val durationMillis = readDurationMillis(recordingSession.videoEventsFile)
        val sensorQualityFile = File(sessionDir, "trajectreview/sensor_quality.json")
        val sensorQuality = readJsonObjectOrNull(sensorQualityFile)
        val warnings = freshResult?.warnings ?: (sensorQuality?.optJSONArray("warnings")?.toStringList() ?: emptyList())
        val blockers = freshResult?.blockers ?: (sensorQuality?.optJSONArray("blockers")?.toStringList() ?: emptyList())
        return StoredSessionSummary(
            sessionId = recordingSession.sessionId,
            sessionDir = sessionDir,
            recordingSession = recordingSession,
            startedAtMillis = startedAtMillis,
            startedAtLabel = transferTimestampFormat.format(Date(startedAtMillis)),
            durationLabel = "%.1f 秒".format(durationMillis / 1000.0),
            manifest = manifest,
            hasTransferReady = canTransferSelectedSession(recordingSession),
            warnings = warnings,
            blockers = blockers,
        )
    }

    private fun buildRecordingSessionFromDir(sessionDir: File): RecordingSession? {
        if (!sessionDir.exists() || !sessionDir.isDirectory) {
            return null
        }
        val manifestFile = File(sessionDir, "session_manifest.json")
        val manifest = readJsonObjectOrNull(manifestFile)
        val timebase = manifest?.optJSONObject("timebase")
        val adapterMetadata =
            GuardedUpstreamTrialContract.sessionAdapterMetadataFromJson(manifest?.optJSONObject("sessionAdapter"))
                ?: GuardedUpstreamTrialContract.buildSessionAdapterMetadata(
                    GuardedUpstreamTrialContract.resolve(selectedRoute().routeId, BuildConfig.CORECAMERA_RUNTIME_ENABLED),
                )
        return RecordingSession(
            sessionId = sessionDir.name,
            sessionDir = sessionDir,
            manifestFile = manifestFile,
            videoFile = File(sessionDir, "video.mp4"),
            imuFile = File(sessionDir, "imu.csv"),
            gnssFile = File(sessionDir, "gnss.csv"),
            bleFile = File(sessionDir, "ble_scan.jsonl"),
            arCoreFile =
                listOf("frame_record.jsonl", "arcore_pose.jsonl")
                    .map { File(sessionDir, it) }
                    .firstOrNull { it.exists() }
                    ?: File(sessionDir, "frame_record.jsonl"),
            imagesDir = resolveSessionImageDir(sessionDir),
            frameTimestampsFile = File(sessionDir, "video_frame_timestamps.csv"),
            videoEventsFile = File(sessionDir, "video_events.jsonl"),
            timebase = SessionTimebase(
                sessionStartWallTimeMs = timebase?.optLong("sessionStartWallTimeMs") ?: sessionDir.lastModified(),
                sessionStartElapsedRealtimeNanos = timebase?.optLong("sessionStartElapsedRealtimeNanos") ?: 0L,
            ),
            adapterMetadata = adapterMetadata,
            sensorSampleCount = manifest?.optLong("imuSampleCount") ?: 0L,
            gnssSampleCount = manifest?.optLong("gnssSampleCount") ?: 0L,
            bleSampleCount = manifest?.optLong("bleSampleCount") ?: 0L,
            arCoreSampleCount = manifest?.optLong("arCoreSampleCount") ?: 0L,
            recordingConfig =
                manifest?.optJSONObject("recordingConfig")?.let(::recordingConfigFromJson)
                    ?: RecordingConfig(recordingMode = RecordingMode.fromModeId(manifest?.optString("recordingMode"))),
        )
    }

    private fun resolveSessionImageDir(sessionDir: File): File =
        listOf(
            File(File(sessionDir, "trajectreview"), "image"),
            File(File(sessionDir, "trajectreview"), "images"),
            File(sessionDir, "image"),
            File(sessionDir, "images"),
        ).firstOrNull { it.exists() } ?: File(File(sessionDir, "trajectreview"), "image")

    private fun readJsonObjectOrNull(file: File): JSONObject? {
        if (!file.exists()) {
            return null
        }
        val raw = runCatching { file.readText().trim() }.getOrNull().orEmpty()
        if (raw.isBlank()) {
            return null
        }
        return runCatching { JSONObject(raw) }.getOrNull()
    }

    private fun readDurationMillis(videoEventsFile: File): Long {
        if (!videoEventsFile.exists()) {
            return 0L
        }
        return videoEventsFile.useLines { lines ->
            lines.mapNotNull { line ->
                runCatching { JSONObject(line).optLong("durationNanos", 0L) }.getOrNull()
            }.maxOrNull()
        }?.div(1_000_000L) ?: 0L
    }

    private fun canTransferSelectedSession(session: RecordingSession?): Boolean {
        if (session == null) {
            return false
        }
        val derivedDir = File(session.sessionDir, "trajectreview")
        return File(derivedDir, "session_package.json").exists() && File(derivedDir, "space_handoff_manifest.json").exists()
    }

    private fun selectedTransferGroups(): Set<TransferGroup> =
        selectedTransferGroupsState.toSet()

    private fun transferRequirementSummary(sessions: List<RecordingSession>): String {
        val dataStatus =
            when {
                sessions.isEmpty() -> "転送Data: 収録後に選択可"
                sessions.any { !canTransferSelectedSession(it) } -> "転送Data: 要品質確認"
                else -> "転送Data: 設定済み"
            }
        val destinationStatus =
            if (selectedTransferDestinationUri() == null) {
                "転送先: 未設定"
            } else {
                "転送先: 設定済み"
            }
        return "$dataStatus / $destinationStatus\n転送実行には、転送Dataの選択と転送先の選択が必要です。"
    }

    private fun initializeCaptureModeControls() {
        captureModeSyncInProgress = true
        val initialCaptureMode = prefersGuardedReplacementRoute()
        binding.captureModeSwitch.isChecked = initialCaptureMode
        binding.arcoreSwitch.isChecked = initialCaptureMode
        if (initialCaptureMode) {
            binding.standardModeRadio.isChecked = true
        } else {
            binding.pocketModeRadio.isChecked = true
        }
        captureModeSyncInProgress = false
    }

    private fun applyCaptureModeSelection(enabled: Boolean) {
        captureModeSyncInProgress = true
        binding.arcoreSwitch.isChecked = enabled
        if (enabled) {
            binding.standardModeRadio.isChecked = true
        } else {
            binding.pocketModeRadio.isChecked = true
        }
        captureModeSyncInProgress = false
        if (binding.guardedRouteSwitch.isChecked != enabled) {
            binding.guardedRouteSwitch.isChecked = enabled
        } else {
            refreshConfigurationState()
        }
    }

    private fun syncCaptureModeSwitchFromCurrentControls() {
        captureModeSyncInProgress = true
        binding.captureModeSwitch.isChecked =
            binding.guardedRouteSwitch.isChecked && binding.arcoreSwitch.isChecked && binding.standardModeRadio.isChecked
        captureModeSyncInProgress = false
    }

    private fun updateBlockVisibility(recording: Boolean) {
        binding.configBlock.visibility = View.GONE
        binding.recordBlock.visibility = View.VISIBLE
        binding.sessionText.visibility = if (currentSession != null) View.VISIBLE else View.GONE
        binding.filesText.visibility = if (currentSession != null) View.VISIBLE else View.GONE
        binding.transferBlock.visibility =
            if (!recording && (currentSession != null || loadStoredSessions().isNotEmpty())) View.VISIBLE else View.GONE
        binding.transferExecuteBlock.visibility = binding.transferBlock.visibility
    }

    private fun selectedLocalSaveDestinationUri(): Uri? =
        preferences.getString(PREF_SAVE_DESTINATION_TREE_URI, null)?.let(Uri::parse)

    private fun selectedTransferDestinationUri(): Uri? =
        transferDestinationUri

    private fun selectedTransferTargetUrl(): String =
        preferences.getString(PREF_TRANSFER_TARGET_URL, DEFAULT_TARGET_DRIVE_FOLDER_URL)?.trim().orEmpty()

    private fun syncSessionToSelectedDestination(
        sessions: List<RecordingSession>,
        selectedGroups: Set<TransferGroup>,
        successMessage: String,
    ): String {
        require(isCorrectingApp) { "correcting app 以外では転送を使いません。" }
        val destinationUri = selectedTransferDestinationUri() ?: run {
            error("転送先を選択してください。")
        }
        require(sessions.isNotEmpty()) { "転送する data を選択してください。" }
        try {
            contentResolver.openOutputStream(destinationUri, "wt")?.use { output ->
                ZipOutputStream(BufferedOutputStream(output)).use { zipOutput ->
                    sessions.forEach { session ->
                        writeSelectedSessionToZip(
                            sourceDir = session.sessionDir,
                            sessionId = session.sessionId,
                            zipOutput = zipOutput,
                            selectedGroups = selectedGroups,
                        )
                    }
                }
            } ?: error("転送先の書き込みを開始できません。")
            val destinationName = readDocumentDisplayName(destinationUri)
            transferDestinationStatusMessage =
                "$successMessage\n転送先: $destinationName\n対象: ${sessions.joinToString(", ") { it.sessionId }}\n送信 group: ${selectedGroups.joinToString(", ") { it.label }}"
            return "$successMessage\n転送先: $destinationName"
        } finally {
            Unit
        }
    }

    private fun syncSessionToSelectedLocalDestinationIfNeeded(
        session: RecordingSession,
        groups: Set<TransferGroup>,
        inProgressMessage: String,
        successMessage: String,
        failureMessagePrefix: String,
        onFinished: (() -> Unit)? = null,
    ) {
        val destinationUri = selectedLocalSaveDestinationUri()
        if (destinationUri == null) {
            onFinished?.invoke()
            return
        }
        if (saveDestinationSyncInProgress) {
            return
        }
        saveDestinationSyncInProgress = true
        runOnUiThread {
            renderSyncMinimalSessionState(session)
            binding.dataCheckText.text = inProgressMessage
            renderBusyIndicator()
        }
        thread {
            val result =
                runCatching {
                    val rootTree =
                        DocumentFile.fromTreeUri(this, destinationUri)
                            ?: error("保存先 directory にアクセスできません。")
                    migrateLegacyTransferLayoutIfNeeded(rootTree)
                    val sessionRoot =
                        if (groups.containsAll(setOf(TransferGroup.CAPTURE, TransferGroup.SENSORS)) && !groups.contains(TransferGroup.DERIVED)) {
                            recreateDirectory(rootTree, session.sessionId)
                        } else {
                            ensureDirectory(rootTree, session.sessionId)
                        }
                    if (groups.contains(TransferGroup.IMAGES)) {
                        correctingDataCheckService.exportImages(session.sessionDir)
                    }
                    copySelectedSessionContents(session.sessionDir, sessionRoot, groups)
                    sessionRoot.uri.toString()
                }
            runOnUiThread {
                saveDestinationSyncInProgress = false
                renderBusyIndicator()
                result.onSuccess {
                    renderSaveDestinationState(successMessage)
                    refreshSessionDetails(currentSession)
                    latestDataCheckResult?.let(::renderCorrectingDataCheck)
                    onFinished?.invoke()
                }.onFailure { error ->
                    renderSaveDestinationState("$failureMessagePrefix: ${error.message ?: error::class.java.simpleName}")
                    refreshSessionDetails(currentSession)
                    latestDataCheckResult?.let(::renderCorrectingDataCheck)
                    onFinished?.invoke()
                }
            }
        }
    }

    private fun ensureDirectory(parent: DocumentFile, name: String): DocumentFile =
        parent.findFile(name)?.takeIf { it.isDirectory } ?: parent.createDirectory(name)
        ?: error("$name を作成できません。")

    private fun recreateDirectory(parent: DocumentFile, name: String): DocumentFile {
        parent.findFile(name)?.delete()
        return parent.createDirectory(name) ?: error("$name を作成できません。")
    }

    private fun migrateLegacyTransferLayoutIfNeeded(rootTree: DocumentFile) {
        val legacyRoot = rootTree.findFile("trajectreview-correcting")?.takeIf { it.isDirectory } ?: return
        legacyRoot.listFiles().forEach { child ->
            val childName = child.name ?: return@forEach
            if (rootTree.findFile(childName) == null) {
                if (child.isDirectory) {
                    val targetDir = rootTree.createDirectory(childName) ?: return@forEach
                    copyDocumentDirectoryContents(child, targetDir)
                } else if (child.isFile) {
                    copyDocumentFile(child, rootTree, childName)
                }
            }
            child.delete()
        }
        legacyRoot.delete()
    }

    private fun copySelectedSessionContents(
        sourceDir: File,
        targetDir: DocumentFile,
        selectedGroups: Set<TransferGroup>,
    ) {
        selectedGroups.forEach { group ->
            group.relativePaths.forEach { relativePath ->
                val source = File(sourceDir, relativePath)
                if (!source.exists()) {
                    return@forEach
                }
                if (source.isDirectory) {
                    val childDir = ensureRelativeDirectory(targetDir, relativePath)
                    copyDirectoryContents(source, childDir)
                } else {
                    copySingleFileToRelativePath(source, targetDir, relativePath)
                }
            }
        }
    }

    private fun writeSelectedSessionToZip(
        sourceDir: File,
        sessionId: String,
        zipOutput: ZipOutputStream,
        selectedGroups: Set<TransferGroup>,
    ) {
        selectedGroups.forEach { group ->
            group.relativePaths.forEach { relativePath ->
                val source = File(sourceDir, relativePath)
                if (!source.exists()) {
                    return@forEach
                }
                if (source.isDirectory) {
                    writeDirectoryToZip(source, "$sessionId/$relativePath", zipOutput)
                } else {
                    writeFileToZip(source, "$sessionId/$relativePath", zipOutput)
                }
            }
        }
    }

    private fun writeDirectoryToZip(sourceDir: File, entryPrefix: String, zipOutput: ZipOutputStream) {
        sourceDir.listFiles()?.sortedBy { it.name }?.forEach { child ->
            val nextEntry = "$entryPrefix/${child.name}".replace('\\', '/')
            if (child.isDirectory) {
                writeDirectoryToZip(child, nextEntry, zipOutput)
            } else {
                writeFileToZip(child, nextEntry, zipOutput)
            }
        }
    }

    private fun writeFileToZip(sourceFile: File, entryName: String, zipOutput: ZipOutputStream) {
        zipOutput.putNextEntry(ZipEntry(entryName.replace('\\', '/')))
        sourceFile.inputStream().use { input -> input.copyTo(zipOutput) }
        zipOutput.closeEntry()
    }

    private fun copyDirectoryContents(sourceDir: File, targetDir: DocumentFile) {
        sourceDir.listFiles()?.sortedBy { it.name }?.forEach { file ->
            if (file.isDirectory) {
                val childDir = ensureDirectory(targetDir, file.name)
                copyDirectoryContents(file, childDir)
            } else {
                val existing = targetDir.findFile(file.name)
                if (existing != null && existing.isFile) {
                    existing.delete()
                }
                val targetFile =
                    targetDir.createFile(detectMimeType(file.name), file.name)
                        ?: error("${file.name} を作成できません。")
                contentResolver.openOutputStream(targetFile.uri, "wt")?.use { output ->
                    file.inputStream().use { input -> input.copyTo(output) }
                } ?: error("${file.name} の書き込みを開始できません。")
            }
        }
    }

    private fun copySingleFileToRelativePath(sourceFile: File, targetRoot: DocumentFile, relativePath: String) {
        val segments = relativePath.split('/').filter { it.isNotBlank() }
        val parentDir =
            segments.dropLast(1).fold(targetRoot) { current, segment ->
                ensureDirectory(current, segment)
            }
        val fileName = segments.lastOrNull() ?: sourceFile.name
        val existing = parentDir.findFile(fileName)
        if (existing != null && existing.isFile) {
            existing.delete()
        }
        val targetFile =
            parentDir.createFile(detectMimeType(fileName), fileName)
                ?: error("$relativePath を作成できません。")
        contentResolver.openOutputStream(targetFile.uri, "wt")?.use { output ->
            sourceFile.inputStream().use { input -> input.copyTo(output) }
        } ?: error("$relativePath の書き込みを開始できません。")
    }

    private fun copyDocumentDirectoryContents(sourceDir: DocumentFile, targetDir: DocumentFile) {
        sourceDir.listFiles().forEach { child ->
            val childName = child.name ?: return@forEach
            if (child.isDirectory) {
                val nextDir = ensureDirectory(targetDir, childName)
                copyDocumentDirectoryContents(child, nextDir)
            } else if (child.isFile) {
                copyDocumentFile(child, targetDir, childName)
            }
        }
    }

    private fun copyDocumentFile(sourceFile: DocumentFile, targetDir: DocumentFile, fileName: String) {
        val existing = targetDir.findFile(fileName)
        if (existing != null && existing.isFile) {
            existing.delete()
        }
        val targetFile =
            targetDir.createFile(detectMimeType(fileName), fileName)
                ?: error("$fileName を作成できません。")
        contentResolver.openInputStream(sourceFile.uri)?.use { input ->
            contentResolver.openOutputStream(targetFile.uri, "wt")?.use { output ->
                input.copyTo(output)
            } ?: error("$fileName の書き込みを開始できません。")
        } ?: error("$fileName の読み込みを開始できません。")
    }

    private fun ensureRelativeDirectory(targetRoot: DocumentFile, relativePath: String): DocumentFile =
        relativePath.split('/').filter { it.isNotBlank() }.fold(targetRoot) { current, segment ->
            ensureDirectory(current, segment)
        }

    private fun detectMimeType(name: String): String =
        when {
            name.endsWith(".json") -> "application/json"
            name.endsWith(".jsonl") -> "application/octet-stream"
            name.endsWith(".csv") -> "text/csv"
            name.endsWith(".mp4") -> "video/mp4"
            name.endsWith(".jpg") || name.endsWith(".jpeg") -> "image/jpeg"
            else -> "application/octet-stream"
        }

    private fun recordingConfigFromJson(json: JSONObject): RecordingConfig =
        RecordingConfig(
            videoFrameLogIntervalMs = json.optLong("videoFrameLogIntervalMs", 100L),
            imuIntervalMs = json.optLong("imuIntervalMs", 20L),
            gnssIntervalMs = json.optLong("gnssIntervalMs", 1000L),
            bleIntervalMs = json.optLong("bleIntervalMs", 2000L),
            arCoreIntervalMs = json.optLong("arCoreIntervalMs", 33L),
            bleEnabled = json.optBoolean("bleEnabled", true),
            arCoreEnabled = json.optBoolean("arCoreEnabled", true),
            frameRecordEveryNUpdates = json.optInt("frameRecordEveryNUpdates", 1).coerceAtLeast(1),
            saveOnlyWhenTracking = json.optBoolean("saveOnlyWhenTracking", true),
            recordingMode = RecordingMode.fromModeId(json.optString("recordingMode")),
        )

    private fun readDocumentDisplayName(uri: Uri): String =
        runCatching {
            contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { cursor ->
                if (cursor.moveToFirst()) {
                    cursor.getString(0)
                } else {
                    uri.lastPathSegment ?: uri.toString()
                }
            } ?: (uri.lastPathSegment ?: uri.toString())
        }.getOrDefault(uri.lastPathSegment ?: uri.toString())

    private fun defaultTransferArchiveName(): String {
        val sessions = selectedTransferSessions()
        if (sessions.isEmpty()) {
            return "trajectreview-correcting-session-${transferTimestampFormat.format(Date()).replace("-", "").replace(":", "").replace(" ", "-")}.zip"
        }
        if (sessions.size == 1) {
            val session = sessions.first()
            val suffix = canonicalSessionSuffix(session)
            val customBase =
                if (session.sessionId == suffix || session.sessionId.startsWith("session-")) {
                    "trajectreview-correcting"
                } else {
                    session.sessionId
                }
            val base =
                if (customBase.endsWith("-$suffix")) {
                    customBase
                } else {
                    "$customBase-$suffix"
                }
            return "$base.zip"
        }
        val suffix = canonicalSessionSuffix(sessions.first())
        return "trajectreview-correcting-$suffix.zip"
    }

    private fun canonicalSessionSuffix(session: RecordingSession): String {
        val manifestSessionId =
            runCatching {
                if (session.manifestFile.exists()) {
                    JSONObject(session.manifestFile.readText()).optString("sessionId")
                } else {
                    ""
                }
            }.getOrDefault("")
        return when {
            manifestSessionId.startsWith("session-") -> manifestSessionId
            session.sessionId.startsWith("session-") -> session.sessionId
            else -> "session-${SimpleDateFormat("yyyyMMdd-HHmmss", Locale.JAPAN).format(Date(session.timebase.sessionStartWallTimeMs))}"
        }
    }

    companion object {
        private const val PREF_GUARDED_ROUTE = "pref_guarded_route"
        private const val PREF_SAVE_DESTINATION_TREE_URI = "pref_save_destination_tree_uri"
        private const val PREF_TRANSFER_DESTINATION_URI = "pref_transfer_destination_uri"
        private const val PREF_TRANSFER_TARGET_URL = "pref_transfer_target_url"
        private const val ROUTE_SWITCH_GUARD_MS = 800L
        private const val DEFAULT_TARGET_DRIVE_FOLDER_URL = "https://drive.google.com/drive/u/2/folders/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_"
        private const val PROCESSING_WAKE_LOCK_TIMEOUT_MS = 15 * 60 * 1000L

        private val requiredPermissions = arrayOf(
            Manifest.permission.CAMERA,
            Manifest.permission.RECORD_AUDIO,
        )

        private val optionalPermissions = arrayOf(
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.BLUETOOTH_SCAN,
            Manifest.permission.BLUETOOTH_CONNECT,
        )

        private val allRequestedPermissions = requiredPermissions + optionalPermissions
    }

    private val transferTimestampFormat = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.JAPAN)

    private fun startRecordingButtonText(): String =
        if (isCorrectingApp) {
            getString(R.string.record_start_button)
        } else {
            getString(R.string.start_recording)
        }

    private fun stopRecordingButtonText(): String =
        if (isCorrectingApp) {
            getString(R.string.record_stop_button)
        } else {
            getString(R.string.stop_recording)
        }

    private enum class TransferGroup(val label: String, val relativePaths: List<String>) {
        CAPTURE(
            label = "撮影データ",
            relativePaths =
                listOf(
                    "session_manifest.json",
                    "video.mp4",
                    "video_events.jsonl",
                    "video_frame_timestamps.csv",
                ),
        ),
        SENSORS(
            label = "センサ記録",
            relativePaths =
                listOf(
                    "imu.csv",
                    "gnss.csv",
                    "ble_scan.jsonl",
                    "frame_record.jsonl",
                ),
        ),
        DERIVED(
            label = "data-check結果と後段受け渡し",
            relativePaths =
                listOf(
                    "trajectreview/input_readiness.json",
                    "trajectreview/sensor_quality.json",
                    "trajectreview/frame_pose_index.csv",
                    "trajectreview/camera_calibration_summary.json",
                    "trajectreview/member_identity_map.json",
                    "trajectreview/session_package.json",
                    "trajectreview/space_handoff_manifest.json",
                ),
        ),
        IMAGES(
            label = "frame画像群",
            relativePaths = listOf("trajectreview/image"),
        ),
    }

    private data class StoredSessionSummary(
        val sessionId: String,
        val sessionDir: File,
        val recordingSession: RecordingSession,
        val startedAtMillis: Long,
        val startedAtLabel: String,
        val durationLabel: String,
        val manifest: JSONObject?,
        val hasTransferReady: Boolean,
        val warnings: List<String>,
        val blockers: List<String>,
    )

    private fun StoredSessionSummary.displayLabel(): String =
        buildString {
            if (hasConcerns) append("▲")
            append(sessionId)
        }

    private val StoredSessionSummary.hasConcerns: Boolean
        get() = warnings.isNotEmpty() || blockers.isNotEmpty()

    private fun StoredSessionSummary.concernLine(): String =
        buildString {
            append("▲ ")
            append((blockers + warnings).joinToString(" / ").ifBlank { "懸念なし" })
        }

    private fun org.json.JSONArray.toStringList(): List<String> =
        buildList {
            for (index in 0 until length()) {
                optString(index).takeIf { it.isNotBlank() }?.let(::add)
            }
        }
}
