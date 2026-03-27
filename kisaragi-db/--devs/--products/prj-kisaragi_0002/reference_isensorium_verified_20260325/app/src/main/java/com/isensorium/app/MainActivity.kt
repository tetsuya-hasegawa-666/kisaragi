package com.isensorium.app

import android.Manifest
import android.content.Intent
import android.content.Context
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.os.Environment
import android.os.SystemClock
import android.provider.OpenableColumns
import android.text.InputType
import android.view.View
import android.widget.EditText
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.CameraSelector
import androidx.core.content.ContextCompat
import androidx.documentfile.provider.DocumentFile
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
    private var captureModeSyncInProgress: Boolean = false
    private val selectedTransferSessionIds: MutableSet<String> = linkedSetOf()
    private val selectedTransferGroupsState: MutableSet<TransferGroup> =
        linkedSetOf(
            TransferGroup.CAPTURE,
            TransferGroup.SENSORS,
            TransferGroup.DERIVED,
            TransferGroup.IMAGES,
        )

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
                preferences.edit().putString(PREF_TRANSFER_DESTINATION_URI, uri.toString()).apply()
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

        recordingCoordinator = buildRecordingCoordinator()

        binding.recordButton.setOnClickListener {
            if (recordingCoordinator.isRecording()) {
                recordingCoordinator.stopSession()
            } else {
                ensurePermissionsAndStart()
            }
        }

        binding.refreshButton.setOnClickListener {
            refreshLatestSessionDetails()
        }
        binding.dataCheckButton.setOnClickListener {
            currentSession?.let { runCorrectingDataCheck(it, false) }
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
        updateBlockVisibility(recording = false)
    }

    override fun onDestroy() {
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
            binding.recordButton.text = startRecordingButtonText()
            binding.bleSwitch.isEnabled = !state.recording
            binding.captureModeSwitch.isEnabled = !state.recording
            binding.arcoreSwitch.isEnabled = !state.recording
            setInputsEnabled(!state.recording)
            showRecordingUi(state.recording, state.statusText)
            renderState(state.statusText)
            refreshDisplayedIssue()
            refreshSessionDetails(state.session)
            if (!state.recording) {
                refreshConfigurationState()
                if (isCorrectingApp && state.session != null) {
                    runCorrectingDataCheck(state.session, true)
                }
            }
        }
    }

    private fun renderState(message: String) {
        binding.statusText.text = message
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

    private fun showRecordingUi(recording: Boolean, statusText: String) {
        binding.controlsCard.visibility = View.VISIBLE
        binding.recordingOverlay.visibility = View.GONE
        binding.recordingOverlayText.text = statusText
        binding.recordButton.visibility = View.VISIBLE
        binding.recordButton.text =
            if (recording) {
                stopRecordingButtonText()
            } else {
                startRecordingButtonText()
            }
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
                videoFrameLogIntervalMs = readMs(binding.videoIntervalInput, 100L),
                imuIntervalMs = readMs(binding.imuIntervalInput, 20L),
                gnssIntervalMs = readMs(binding.gnssIntervalInput, 1000L),
                bleIntervalMs = readMs(binding.bleIntervalInput, 2000L),
                arCoreIntervalMs = readMs(binding.arcoreIntervalInput, 2000L),
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
                runCorrectingDataCheck(currentSession!!, false)
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
            selectedTransferDestinationUri() != null &&
            selectedTransferGroups().isNotEmpty()
        renderSaveDestinationState(null)
        renderTransferDestinationState(null)
        updateBlockVisibility(recordingCoordinator.isRecording())
    }

    private fun resetCorrectingWorkflowState() {
        checkedSessionId = null
        latestDataCheckResult = null
        successfulDataCheckCount = 0
        selectedTransferSessionIds.clear()
        renderCorrectingDataCheck(null)
        renderTransferState("未選択")
    }

    private fun runCorrectingDataCheck(session: RecordingSession, autoTriggered: Boolean) {
        if (!isCorrectingApp || dataCheckInProgress) {
            return
        }
        dataCheckInProgress = true
        binding.dataCheckButton.isEnabled = false
        binding.dataCheckText.text = "data-check を実行中です。"
        thread {
            val result = runCatching { correctingDataCheckService.run(session.sessionDir) }
            runOnUiThread {
                dataCheckInProgress = false
                binding.dataCheckButton.isEnabled = true
                result.onSuccess {
                    checkedSessionId = session.sessionId
                    latestDataCheckResult = it
                    successfulDataCheckCount += 1
                    renderCorrectingDataCheck(it)
                    renderTransferState(null)
                    syncSessionToSelectedLocalDestinationIfNeeded(session)
                    if (!autoTriggered) {
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
                "未実行"
            } else {
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
            }
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
            renderTransferState("送信データセットの選択で 1 つ以上の group を選ぶと転送できます。")
            return
        }
        transferInProgress = true
        binding.transferButton.isEnabled = false
        renderTransferState("Google Drive 転送を開始しています。")
        thread {
            val result =
                runCatching {
                    syncSessionToSelectedDestination(
                        sessions = sessions,
                        selectedGroups = selectedTransferGroups(),
                        successMessage = "Google Drive へ data を転送しました。",
                    )
                }
            runOnUiThread {
                transferInProgress = false
                binding.transferButton.isEnabled =
                    selectedTransferSessions().isNotEmpty() &&
                    selectedTransferDestinationUri() != null &&
                    selectedTransferGroups().isNotEmpty()
                result.onSuccess {
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
        val selectedSessionLabels =
            selectedSessions.joinToString(", ") { session ->
                sessionSummaryById(session.sessionId)?.displayLabel() ?: session.sessionId
            }.ifBlank { "未選択" }
        binding.selectTransferSessionButton.isEnabled = !recordingCoordinator.isRecording()
        binding.manageTransferSessionsButton.isEnabled = !recordingCoordinator.isRecording() && hasStoredSessions
        binding.selectTransferGroupsButton.isEnabled = !recordingCoordinator.isRecording()
        binding.transferTargetButton.visibility = View.VISIBLE
        binding.transferExecuteBlock.visibility = binding.transferBlock.visibility
        binding.transferButton.isEnabled =
            !transferInProgress &&
            selectedSessions.isNotEmpty() &&
            selectedTransferDestinationUri() != null &&
            selectedTransferGroups().isNotEmpty()
        binding.transferText.text =
            message ?: buildString {
                appendLine("事前設定: 1. 転送先を選択 2. URL を確認 3. 保存先fileを設定する")
                appendLine("転送対象: $selectedSessionLabels")
                appendLine("送信データセット: ${selectedTransferGroups().joinToString(", ") { it.label }.ifBlank { "未選択" }}")
                append(sessionTransferGuidance(selectedSessions))
            }
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
        val selectedUri = selectedLocalSaveDestinationUri()
        binding.transferDestinationText.text =
            when {
                selectedUri == null -> "保存先は未設定です。"
                saveDestinationStatusMessage != null -> "${saveDestinationStatusMessage}\n保存先は設定済みです。"
                else -> "保存先は設定済みです。"
            }
    }

    private fun renderTransferDestinationState(statusMessage: String?) {
        if (!isCorrectingApp) {
            binding.transferTargetText.visibility = View.GONE
            return
        }
        binding.transferTargetText.visibility = View.VISIBLE
        binding.transferTargetButton.isEnabled = !recordingCoordinator.isRecording() && !transferInProgress
        if (statusMessage != null) {
            transferDestinationStatusMessage = statusMessage
        }
        val selectedUri = selectedTransferDestinationUri()
        binding.transferTargetText.text =
            when {
                selectedUri == null -> "転送先は未設定です。"
                else -> "転送先は設定済みです。"
            }
    }

    private fun showTransferTargetDialog() {
        val input = EditText(this)
        input.inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_URI
        input.setText(selectedTransferTargetUrl())
        AlertDialog.Builder(this)
            .setTitle("転送先を選択")
            .setMessage("アドレスを入力してください")
            .setView(input)
            .setNeutralButton("保存先fileを設定する") { _, _ ->
                val url = normalizeTransferTargetUrl(input.text?.toString().orEmpty())
                saveTransferTargetUrl(url)
                openTransferTargetUrl(url)
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

    private fun openTransferTargetUrl(url: String) {
        val intent =
            Intent(Intent.ACTION_VIEW, Uri.parse(url)).apply {
                addCategory(Intent.CATEGORY_BROWSABLE)
            }
        runCatching {
            startActivity(intent)
            transferDestinationLauncher.launch(defaultTransferArchiveName())
            renderTransferState("Google Drive を開きました。保存先 folder を確認または作成し、続けて保存先 file を選んでください。")
        }.onFailure { error ->
            renderTransferState(
                "Google Drive URL を開けませんでした: ${error.message ?: error::class.java.simpleName}\n" +
                    "URL: $url",
            )
        }
    }

    private fun showSamplingConditionsDialog() {
        val dialogView = layoutInflater.inflate(R.layout.dialog_sampling_conditions, null)
        val captureSwitch = dialogView.findViewById<MaterialSwitch>(R.id.dialogCaptureModeSwitch)
        val bleSwitch = dialogView.findViewById<MaterialSwitch>(R.id.dialogBleSwitch)
        val videoInput = dialogView.findViewById<EditText>(R.id.dialogVideoIntervalInput)
        val arcoreInput = dialogView.findViewById<EditText>(R.id.dialogArcoreIntervalInput)
        val imuInput = dialogView.findViewById<EditText>(R.id.dialogImuIntervalInput)
        val gnssInput = dialogView.findViewById<EditText>(R.id.dialogGnssIntervalInput)
        val bleInput = dialogView.findViewById<EditText>(R.id.dialogBleIntervalInput)

        captureSwitch.isChecked = binding.captureModeSwitch.isChecked
        bleSwitch.isChecked = binding.bleSwitch.isChecked
        videoInput.setText(binding.videoIntervalInput.text)
        arcoreInput.setText(binding.arcoreIntervalInput.text)
        imuInput.setText(binding.imuIntervalInput.text)
        gnssInput.setText(binding.gnssIntervalInput.text)
        bleInput.setText(binding.bleIntervalInput.text)

        AlertDialog.Builder(this)
            .setTitle("サンプリング条件")
            .setView(dialogView)
            .setPositiveButton("確定") { _, _ ->
                binding.captureModeSwitch.isChecked = captureSwitch.isChecked
                binding.bleSwitch.isChecked = bleSwitch.isChecked
                binding.videoIntervalInput.setText(videoInput.text)
                binding.arcoreIntervalInput.setText(arcoreInput.text)
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
        val summaries = loadStoredSessions()
        if (summaries.isEmpty()) {
            Toast.makeText(this, "転送できる data がまだありません", Toast.LENGTH_SHORT).show()
            return
        }
        val labels =
            summaries.map { summary ->
                buildString {
                    append(summary.displayLabel())
                    append("\n")
                    append("取得日時: ${summary.startedAtLabel} | 長さ: ${summary.durationLabel}")
                    if (summary.hasConcerns) {
                        append("\n")
                        append(summary.concernLine())
                    }
                }
            }.toTypedArray()
        val checkedItems = summaries.map { selectedTransferSessionIds.contains(it.sessionId) }.toBooleanArray()
        AlertDialog.Builder(this)
            .setTitle("転送する data を選択")
            .setMultiChoiceItems(labels, checkedItems) { _, which, isChecked ->
                val sessionId = summaries[which].sessionId
                if (isChecked) {
                    selectedTransferSessionIds.add(sessionId)
                } else {
                    selectedTransferSessionIds.remove(sessionId)
                }
            }
            .setPositiveButton("OK") { _, _ -> renderTransferState(null) }
            .setNegativeButton("閉じる", null)
            .show()
    }

    private fun showManageStoredSessionsDialog() {
        val summaries = loadStoredSessions()
        if (summaries.isEmpty()) {
            Toast.makeText(this, "保存済み data がまだありません", Toast.LENGTH_SHORT).show()
            return
        }
        val labels =
            summaries.map {
                buildString {
                    append(it.displayLabel())
                    append("\n取得日時: ${it.startedAtLabel}\n長さ: ${it.durationLabel}")
                    if (it.hasConcerns) {
                        append("\n")
                        append(it.concernLine())
                    }
                }
            }.toTypedArray()
        AlertDialog.Builder(this)
            .setTitle("データ一覧＋名称変更")
            .setItems(labels) { _, which ->
                showRenameTransferSessionDialog(summaries[which])
            }
            .setNegativeButton("閉じる", null)
            .show()
    }

    private fun showRenameTransferSessionDialog(summary: StoredSessionSummary) {
        val input = EditText(this)
        input.setText(summary.sessionId)
        AlertDialog.Builder(this)
            .setTitle("データ名を変更")
            .setView(input)
            .setPositiveButton("変更") { _, _ ->
                val newName = input.text?.toString()?.trim().orEmpty()
                renameStoredSession(summary, newName)
            }
            .setNegativeButton("キャンセル", null)
            .show()
    }

    private fun renameStoredSession(summary: StoredSessionSummary, newName: String) {
        if (newName.isBlank()) {
            Toast.makeText(this, "データ名を入力してください", Toast.LENGTH_SHORT).show()
            return
        }
        if (!Regex("^[A-Za-z0-9._-]+$").matches(newName)) {
            Toast.makeText(this, "半角英数字と . _ - のみ使えます", Toast.LENGTH_SHORT).show()
            return
        }
        val targetDir = File(summary.sessionDir.parentFile, newName)
        if (targetDir.exists()) {
            Toast.makeText(this, "同名 directory が既にあります", Toast.LENGTH_SHORT).show()
            return
        }
        if (!summary.sessionDir.renameTo(targetDir)) {
            Toast.makeText(this, "データ名の変更に失敗しました", Toast.LENGTH_SHORT).show()
            return
        }
        if (selectedTransferSessionIds.remove(summary.sessionId)) {
            selectedTransferSessionIds.add(newName)
        }
        if (currentSession?.sessionId == summary.sessionId) {
            currentSession = buildRecordingSessionFromDir(targetDir)
        }
        renderTransferState("データ名を変更しました。")
        refreshSessionDetails(currentSession)
    }

    private fun loadStoredSessions(): List<StoredSessionSummary> {
        val sessionsRoot = File(getExternalFilesDir(Environment.DIRECTORY_DOCUMENTS), "sessions")
        return sessionsRoot.listFiles { file -> file.isDirectory }?.mapNotNull { dir ->
            buildStoredSessionSummary(dir)
        }?.sortedByDescending { it.startedAtMillis } ?: emptyList()
    }

    private fun sessionSummaryById(sessionId: String): StoredSessionSummary? =
        loadStoredSessions().firstOrNull { it.sessionId == sessionId }

    private fun buildStoredSessionSummary(sessionDir: File): StoredSessionSummary? {
        val recordingSession = buildRecordingSessionFromDir(sessionDir) ?: return null
        val manifest =
            recordingSession.manifestFile.takeIf { it.exists() }?.readText()?.let(::JSONObject)
        val startedAtMillis = recordingSession.timebase.sessionStartWallTimeMs
        val durationMillis = readDurationMillis(recordingSession.videoEventsFile)
        val sensorQualityFile = File(sessionDir, "trajectreview/sensor_quality.json")
        val sensorQuality = sensorQualityFile.takeIf { it.exists() }?.readText()?.let(::JSONObject)
        val warnings = sensorQuality?.optJSONArray("warnings")?.toStringList() ?: emptyList()
        val blockers = sensorQuality?.optJSONArray("blockers")?.toStringList() ?: emptyList()
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
        val manifest = manifestFile.takeIf { it.exists() }?.readText()?.let(::JSONObject)
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
            arCoreFile = File(sessionDir, "arcore_pose.jsonl"),
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

    private fun sessionTransferGuidance(sessions: List<RecordingSession>): String =
        when {
            sessions.isEmpty() -> "手順: 1. 送信データセットを選択 2. 転送するデータを選択 3. 転送先を選択 4. 転送実行"
            sessions.any { !canTransferSelectedSession(it) } -> "選択した data の中に品質確認結果が不足したものがあります。品質確認済みの data のみ選んでください。"
            selectedTransferTargetUrl().isBlank() ->
                "転送先を選択して Google Drive URL を設定すると転送できます。"
            selectedTransferDestinationUri() == null ->
                "転送先URLは設定済みです。`転送先を選択` から `保存先fileを設定する` を押すと転送できます。"
            selectedTransferGroups().isEmpty() -> "送信データセットの選択で 1 つ以上の group を選ぶと転送できます。"
            else -> "転送実行できます。選んだ Google Drive 保存場所に zip を作成します。"
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
        preferences.getString(PREF_TRANSFER_DESTINATION_URI, null)?.let(Uri::parse)

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

    private fun syncSessionToSelectedLocalDestinationIfNeeded(session: RecordingSession) {
        val destinationUri = selectedLocalSaveDestinationUri() ?: return
        if (saveDestinationSyncInProgress) {
            return
        }
        saveDestinationSyncInProgress = true
        thread {
            val result =
                runCatching {
                    val rootTree =
                        DocumentFile.fromTreeUri(this, destinationUri)
                            ?: error("保存先 directory にアクセスできません。")
                    migrateLegacyTransferLayoutIfNeeded(rootTree)
                    val sessionRoot = recreateDirectory(rootTree, session.sessionId)
                    copySelectedSessionContents(session.sessionDir, sessionRoot, TransferGroup.values().toSet())
                    sessionRoot.uri.toString()
                }
            runOnUiThread {
                saveDestinationSyncInProgress = false
                result.onSuccess {
                    renderSaveDestinationState("保存先へ同期しました。")
                }.onFailure { error ->
                    renderSaveDestinationState("保存先への同期に失敗しました: ${error.message ?: error::class.java.simpleName}")
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
            name.endsWith(".json") || name.endsWith(".jsonl") -> "application/json"
            name.endsWith(".csv") -> "text/csv"
            name.endsWith(".mp4") -> "video/mp4"
            else -> "application/octet-stream"
        }

    private fun recordingConfigFromJson(json: JSONObject): RecordingConfig =
        RecordingConfig(
            videoFrameLogIntervalMs = json.optLong("videoFrameLogIntervalMs", 100L),
            imuIntervalMs = json.optLong("imuIntervalMs", 20L),
            gnssIntervalMs = json.optLong("gnssIntervalMs", 1000L),
            bleIntervalMs = json.optLong("bleIntervalMs", 2000L),
            arCoreIntervalMs = json.optLong("arCoreIntervalMs", 2000L),
            bleEnabled = json.optBoolean("bleEnabled", true),
            arCoreEnabled = json.optBoolean("arCoreEnabled", true),
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
        return if (sessions.size == 1) {
            "${sessions.first().sessionId}.zip"
        } else {
            "trajectreview-correcting-export.zip"
        }
    }

    companion object {
        private const val PREF_GUARDED_ROUTE = "pref_guarded_route"
        private const val PREF_SAVE_DESTINATION_TREE_URI = "pref_save_destination_tree_uri"
        private const val PREF_TRANSFER_DESTINATION_URI = "pref_transfer_destination_uri"
        private const val PREF_TRANSFER_TARGET_URL = "pref_transfer_target_url"
        private const val ROUTE_SWITCH_GUARD_MS = 800L
        private const val DEFAULT_TARGET_DRIVE_FOLDER_URL = "https://drive.google.com/drive/u/2/folders/1bHJGtRhmrcZ8xaEG3DVnHfQhMaGnlP5_"

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
                    "arcore_pose.jsonl",
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
            relativePaths = listOf("trajectreview/images"),
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
