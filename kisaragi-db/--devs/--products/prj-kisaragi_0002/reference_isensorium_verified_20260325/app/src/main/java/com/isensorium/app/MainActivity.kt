package com.isensorium.app

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.SystemClock
import android.view.View
import android.widget.ArrayAdapter
import android.widget.EditText
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.CameraSelector
import androidx.core.content.ContextCompat
import com.isensorium.app.databinding.ActivityMainBinding
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
    private val pcTransferService by lazy { PcTransferService() }
    private var dataCheckInProgress: Boolean = false
    private var transferInProgress: Boolean = false
    private var latestDataCheckResult: CorrectingDataCheckResult? = null
    private var checkedSessionId: String? = null
    private var successfulDataCheckCount: Int = 0
    private var discoveredTargets: List<PcTransferTarget> = emptyList()
    private var selectedTarget: PcTransferTarget? = null

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

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
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
        binding.overlayStopButton.setOnClickListener {
            recordingCoordinator.stopSession()
        }

        binding.refreshButton.setOnClickListener {
            refreshLatestSessionDetails()
        }
        binding.dataCheckButton.setOnClickListener {
            currentSession?.let { runCorrectingDataCheck(it, false) }
                ?: Toast.makeText(this, "先に現場撮影データ保存を実行してください", Toast.LENGTH_SHORT).show()
        }
        binding.transferButton.setOnClickListener {
            currentSession?.let { runPcTransfer(it) }
                ?: Toast.makeText(this, "先に現場撮影データ保存を実行してください", Toast.LENGTH_SHORT).show()
        }
        binding.transferDiscoveryButton.setOnClickListener {
            discoverPcTargets()
        }
        binding.transferTargetSpinner.onItemSelectedListener =
            object : android.widget.AdapterView.OnItemSelectedListener {
                override fun onItemSelected(parent: android.widget.AdapterView<*>?, view: View?, position: Int, id: Long) {
                    selectedTarget = discoveredTargets.getOrNull(position)
                    renderTransferState(null)
                }

                override fun onNothingSelected(parent: android.widget.AdapterView<*>?) {
                    selectedTarget = null
                    renderTransferState(null)
                }
            }
        binding.recordingModeGroup.setOnCheckedChangeListener { _, _ ->
            if (!recordingCoordinator.isRecording()) {
                refreshConfigurationState()
            }
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
        renderState(mainScreenController.buildInitialStatus())
        refreshConfigurationState()
        ensurePermissionsAndStartPreview()
        binding.recordButton.text = startRecordingButtonText()
        renderCorrectingDataCheck(null)
        renderTransferState(null)
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
            if (state.session?.sessionId != checkedSessionId) {
                checkedSessionId = state.session?.sessionId
                latestDataCheckResult = null
                successfulDataCheckCount = 0
                discoveredTargets = emptyList()
                selectedTarget = null
                renderTransferState(null)
            }
            binding.recordButton.text =
                if (state.recording) stopRecordingButtonText() else startRecordingButtonText()
            binding.bleSwitch.isEnabled = !state.recording
            binding.arcoreSwitch.isEnabled = !state.recording
            setInputsEnabled(!state.recording)
            showRecordingUi(state.recording, state.statusText)
            renderState(state.statusText)
            refreshDisplayedIssue()
            refreshSessionDetails(state.session)
            state.toastMessage?.let {
                Toast.makeText(this, it, Toast.LENGTH_SHORT).show()
            }
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
        binding.controlsCard.visibility = if (recording) View.GONE else View.VISIBLE
        binding.recordingOverlay.visibility = if (recording) View.VISIBLE else View.GONE
        binding.recordingOverlayText.text =
            if (recording) statusText else getString(R.string.recording_overlay_default)
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
        binding.transferButton.isEnabled = !transferInProgress && successfulDataCheckCount > 0 && selectedTarget != null
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
            binding.dataCheckHeaderText.visibility = View.GONE
            binding.dataCheckText.visibility = View.GONE
            binding.dataCheckButton.visibility = View.GONE
            return
        }
        binding.dataCheckHeaderText.visibility = View.VISIBLE
        binding.dataCheckText.visibility = View.VISIBLE
        binding.dataCheckButton.visibility = View.VISIBLE
        binding.dataCheckText.text =
            if (result == null) {
                "記録停止後に同じ app 内で data-check を実行し、補正結果を確認できます。"
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
                    appendLine("補正指示: ${result.recommendedCorrections.joinToString(" / ")}")
                    append("保存先: ${result.derivedDir.absolutePath}")
                }
            }
    }

    private fun runPcTransfer(session: RecordingSession) {
        if (!isCorrectingApp || transferInProgress) {
            return
        }
        if (successfulDataCheckCount <= 0 || latestDataCheckResult == null) {
            Toast.makeText(this, "先に 1 回以上 data-check を実行してください", Toast.LENGTH_SHORT).show()
            return
        }
        val target = selectedTarget ?: run {
            Toast.makeText(this, "同一ネットワーク上の対象 PC を選択してください", Toast.LENGTH_SHORT).show()
            return
        }
        transferInProgress = true
        binding.transferButton.isEnabled = false
        renderTransferState("PC 転送を開始しています。")
        thread {
            val result =
                runCatching {
                    pcTransferService.transferCheckedSession(
                        sessionDir = session.sessionDir,
                        dataCheckCount = successfulDataCheckCount,
                        target = target,
                    )
                }
            runOnUiThread {
                transferInProgress = false
                binding.transferButton.isEnabled = successfulDataCheckCount > 0
                result.onSuccess {
                    renderTransferState(
                        buildString {
                            appendLine("PC 転送完了: ${it.sessionId}")
                            appendLine("送信先: ${it.resolvedHost}:${it.resolvedPort}")
                            appendLine("PC 保存先: ${it.targetRoot}")
                            append("送信量: ${it.uploadedBytes} bytes")
                        },
                    )
                    Toast.makeText(this, "PC 転送が完了しました", Toast.LENGTH_SHORT).show()
                }.onFailure { error ->
                    renderTransferState("PC 転送に失敗しました: ${error.message ?: error::class.java.simpleName}")
                    Toast.makeText(this, "PC 転送に失敗しました", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }

    private fun renderTransferState(message: String?) {
        if (!isCorrectingApp) {
            binding.transferHeaderText.visibility = View.GONE
            binding.transferText.visibility = View.GONE
            binding.transferDiscoveryButton.visibility = View.GONE
            binding.transferTargetSpinner.visibility = View.GONE
            binding.transferButton.visibility = View.GONE
            return
        }
        binding.transferHeaderText.visibility = View.VISIBLE
        binding.transferText.visibility = View.VISIBLE
        binding.transferDiscoveryButton.visibility = View.VISIBLE
        binding.transferTargetSpinner.visibility = View.VISIBLE
        binding.transferButton.visibility = View.VISIBLE
        binding.transferButton.isEnabled = !transferInProgress && successfulDataCheckCount > 0 && selectedTarget != null
        val labels =
            if (discoveredTargets.isEmpty()) {
                listOf("同一ネットワーク上の PC 候補を検索してください")
            } else {
                discoveredTargets.map { "${it.displayName} (${it.host}:${it.port})" }
            }
        binding.transferTargetSpinner.adapter =
            ArrayAdapter(this, android.R.layout.simple_spinner_item, labels).also { adapter ->
                adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
            }
        if (discoveredTargets.isNotEmpty()) {
            val index = discoveredTargets.indexOfFirst { it == selectedTarget }.takeIf { it != -1 } ?: 0
            binding.transferTargetSpinner.setSelection(index, false)
        }
        binding.transferText.text =
            message ?: buildString {
                appendLine("同一ネットワーク上の PC 候補を検索して選択してください。")
                appendLine("PC 転送は data-check を 1 回以上実行すると有効になります。")
                appendLine("転送順: 現場撮影データ保存 -> data-check -> PC 転送")
                appendLine("選択中 PC: ${selectedTarget?.displayName ?: "未選択"}")
                append("成功した data-check 回数: $successfulDataCheckCount")
            }
    }

    private fun discoverPcTargets() {
        if (transferInProgress) {
            return
        }
        binding.transferDiscoveryButton.isEnabled = false
        renderTransferState("同一ネットワーク上の PC 候補を検索しています。")
        thread {
            val result = runCatching { pcTransferService.discoverTargets() }
            runOnUiThread {
                binding.transferDiscoveryButton.isEnabled = true
                result.onSuccess { targets ->
                    discoveredTargets = targets
                    selectedTarget = targets.firstOrNull()
                    renderTransferState(
                        if (targets.isEmpty()) {
                            "同一ネットワーク上の PC 候補が見つかりません。PC で bootstrap script を起動してください。"
                        } else {
                            "PC 候補を ${targets.size} 件検出しました。対象 PC を選択してください。"
                        },
                    )
                }.onFailure { error ->
                    discoveredTargets = emptyList()
                    selectedTarget = null
                    renderTransferState("PC 候補検索に失敗しました: ${error.message ?: error::class.java.simpleName}")
                }
            }
        }
    }

    companion object {
        private const val PREF_GUARDED_ROUTE = "pref_guarded_route"
        private const val ROUTE_SWITCH_GUARD_MS = 800L

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

    private fun startRecordingButtonText(): String =
        if (isCorrectingApp) {
            "現場撮影データ保存を開始"
        } else {
            getString(R.string.start_recording)
        }

    private fun stopRecordingButtonText(): String =
        if (isCorrectingApp) {
            "現場撮影データ保存を停止"
        } else {
            getString(R.string.stop_recording)
        }
}
