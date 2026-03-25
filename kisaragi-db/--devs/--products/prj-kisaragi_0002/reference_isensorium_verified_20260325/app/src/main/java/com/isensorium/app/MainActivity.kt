package com.isensorium.app

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.SystemClock
import android.view.View
import android.widget.EditText
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.CameraSelector
import androidx.core.content.ContextCompat
import com.isensorium.app.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var recordingCoordinator: RecordingCoordinator
    private val mainScreenController = MainScreenController()
    private val preferences by lazy { getSharedPreferences("guarded_upstream_trial", Context.MODE_PRIVATE) }
    private var currentSession: RecordingSession? = null
    private var routeTransitionInProgress: Boolean = false
    private var runtimeIssue: RecordingIssue? = null
    private var configurationIssue: RecordingIssue? = null

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
            binding.recordButton.text =
                if (state.recording) getString(R.string.stop_recording) else getString(R.string.start_recording)
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
        configurationIssue = resolution.issue
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
}
