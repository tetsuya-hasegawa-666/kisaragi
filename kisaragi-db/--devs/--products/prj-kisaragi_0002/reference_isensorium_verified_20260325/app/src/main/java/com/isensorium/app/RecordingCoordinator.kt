package com.isensorium.app

import android.annotation.SuppressLint
import android.bluetooth.BluetoothManager
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.hardware.camera2.CameraCaptureSession
import android.hardware.camera2.CameraCharacteristics
import android.hardware.camera2.CameraDevice
import android.hardware.camera2.CameraManager
import android.hardware.camera2.CaptureRequest
import android.hardware.camera2.CaptureResult
import android.hardware.camera2.TotalCaptureResult
import android.location.Location
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.os.Handler
import android.os.HandlerThread
import android.os.Looper
import android.os.SystemClock
import android.opengl.GLES11Ext
import android.opengl.GLES20
import android.opengl.GLSurfaceView
import android.util.Size
import android.view.Surface
import android.view.View
import android.view.WindowManager
import android.widget.ImageView
import android.graphics.Bitmap
import android.util.Log
import androidx.camera.core.AspectRatio
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.video.FileOutputOptions
import androidx.camera.video.PendingRecording
import androidx.camera.video.Quality
import androidx.camera.video.QualitySelector
import androidx.camera.video.Recorder
import androidx.camera.video.Recording
import androidx.camera.video.VideoCapture
import androidx.camera.video.VideoRecordEvent
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import androidx.core.content.PermissionChecker
import androidx.lifecycle.DefaultLifecycleObserver
import androidx.lifecycle.LifecycleOwner
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.ar.core.ArCoreApk
import com.google.ar.core.Config
import com.google.ar.core.Session
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.BufferedWriter
import java.io.FileWriter
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import javax.microedition.khronos.egl.EGLConfig
import javax.microedition.khronos.opengles.GL10

class RecordingCoordinator(
    private val context: Context,
    private val lifecycleOwner: LifecycleOwner,
    private val previewView: PreviewView,
    private val replacementPreviewImageView: ImageView,
    private val arCoreGlSurfaceView: GLSurfaceView,
    private val statusListener: (SessionUiState) -> Unit,
    requestedRouteValue: String = BuildConfig.CAMERA_STACK_ROUTE,
) : DefaultLifecycleObserver {

    private val routeResolution =
        GuardedUpstreamTrialContract.resolve(
            requestedRouteValue,
            BuildConfig.CORECAMERA_RUNTIME_ENABLED,
        )
    private val sessionManager = SessionManager(context, routeResolution)
    private val cameraExecutor: ExecutorService = Executors.newSingleThreadExecutor()
    private val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
    private val bluetoothManager = context.getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager

    private val imuLogger = ImuLogger()
    private val gnssLogger = GnssLogger()
    private val bleLogger = BleLogger()
    private val arCoreLogger =
        (arCoreGlSurfaceView.getTag(arCoreGlSurfaceView.id) as? ArCoreLogger) ?: ArCoreLogger()
    private val replacementPreviewRenderer = ReplacementPreviewRenderer(replacementPreviewImageView)

    private var cameraProvider: ProcessCameraProvider? = null
    private var videoCapture: VideoCapture<Recorder>? = null
    private var analysis: ImageAnalysis? = null
    private var recording: Recording? = null
    private var currentSession: RecordingSession? = null
    private var lastStatusUiUpdateElapsedNs: Long = 0L
    private var recordingConfig: RecordingConfig = RecordingConfig()
    private var lastVideoTimestampLoggedAtNs: Long = 0L
    private var lastPreviewCameraSelector: CameraSelector = CameraSelector.DEFAULT_BACK_CAMERA
    private var trialRecordingActive: Boolean = false
    private val sessionRouteAdapter: SessionRouteAdapter =
        when (routeResolution.activeRoute) {
            CameraStackRoute.CORECAMERA_SHARED_CAMERA_TRIAL -> CoreCameraTrialSessionAdapter()
            CameraStackRoute.FROZEN_CAMERAX_ARCORE -> FrozenCameraSessionAdapter()
        }

    init {
        lifecycleOwner.lifecycle.addObserver(this)
        initializeArCoreGlSurfaceView()
    }

    override fun onStop(owner: LifecycleOwner) {
        if (isRecording()) {
            stopSession()
        }
    }

    fun isRecording(): Boolean = recording != null || trialRecordingActive

    fun updateRecordingConfig(config: RecordingConfig) {
        recordingConfig = config
    }

    fun findLatestSession(): RecordingSession? = sessionRouteAdapter.findLatestSession()

    fun startPreview(cameraSelector: CameraSelector) {
        lastPreviewCameraSelector = cameraSelector
        sessionRouteAdapter.startPreview(cameraSelector)
    }

    fun startSession() {
        sessionRouteAdapter.startSession()
    }

    fun stopSession() {
        sessionRouteAdapter.stopSession()
    }

    fun shutdown() {
        sessionRouteAdapter.shutdown()
        lifecycleOwner.lifecycle.removeObserver(this)
    }

    fun onHostResume() {
        sessionRouteAdapter.onHostResume()
    }

    fun onHostPause() {
        sessionRouteAdapter.onHostPause()
    }

    private fun startFrozenPreview(cameraSelector: CameraSelector) {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(context)
        cameraProviderFuture.addListener(
            {
                cameraProvider = cameraProviderFuture.get()
                bindUseCases(cameraSelector)
            },
            ContextCompat.getMainExecutor(context),
        )
    }

    private fun startFrozenSession() {
        if (recording != null) return

        val capture = videoCapture ?: run {
            statusListener(
                SessionUiState(
                    recording = false,
                    session = null,
                    statusText = "カメラの準備がまだ完了していません。",
                    issue = RecordingIssue(
                        severity = RecordingIssueSeverity.ERROR,
                        message = "カメラが未初期化のため、セッションを開始できません。",
                        suggestedAction = "数秒待ってから再度開始するか、再読み込みしてください。",
                    ),
                ),
            )
            return
        }

        val session = sessionManager.createSession()
        currentSession = session
        session.recordingConfig = recordingConfig
        sessionManager.writeInitialManifest(session)
        lastStatusUiUpdateElapsedNs = 0L
        lastVideoTimestampLoggedAtNs = 0L
        statusListener(
            SessionUiState(
                false,
                session,
                if (recordingConfig.bleEnabled || recordingConfig.arCoreEnabled) {
                    "${recordingModeLabel(recordingConfig.recordingMode)}でセッションを作成しました。動画・IMU・GNSS を準備し、BLE / ARCore は低頻度確認として開始します。"
                } else {
                    "${recordingModeLabel(recordingConfig.recordingMode)}でセッションを作成しました。動画・IMU・GNSS の記録を開始します。"
                },
            ),
        )

        imuLogger.start(sensorManager, session)
        gnssLogger.start(session)
        if (recordingConfig.bleEnabled) {
            bleLogger.start(session)
        } else {
            sessionManager.appendCollectorStatus(session, "ble", "disabled")
        }
        if (recordingConfig.arCoreEnabled) {
            arCoreLogger.start(session)
        } else {
            sessionManager.appendCollectorStatus(session, "arcore", "disabled")
        }

        val outputOptions = FileOutputOptions.Builder(session.videoFile).build()
        val pendingRecording = capture.output
            .prepareRecording(context, outputOptions)
            .withAudioEnabled()

        startRecording(pendingRecording, session)
    }

    private fun stopFrozenSession() {
        if (recording == null) return
        recording?.stop()
        recording = null
        stopCollectors()
            currentSession?.let {
                sessionManager.flushSessionOutputs(it)
                sessionManager.finalizeManifest(it, "stopped")
                statusListener(SessionUiState(false, it, "セッションを停止しました。保存先を確認して続きの判断を行ってください。"))
            }
        }

    private fun shutdownFrozenSession() {
        if (isRecording()) {
            stopFrozenSession()
        }
        analysis?.clearAnalyzer()
        cameraProvider?.unbindAll()
        cameraExecutor.shutdown()
        lifecycleOwner.lifecycle.removeObserver(this)
    }

    private fun resumeFrozenSession() {
        arCoreLogger.onResume()
        arCoreGlSurfaceView.onResume()
    }

    private fun pauseFrozenSession() {
        arCoreLogger.onPause()
        arCoreGlSurfaceView.onPause()
    }

    private fun recordingModeLabel(mode: RecordingMode): String =
        when (mode) {
            RecordingMode.STANDARD_HANDHELD -> "通常計測"
            RecordingMode.POCKET_RECORDING -> "ポケット収納計測"
        }

    @SuppressLint("MissingPermission")
    private fun startRecording(pendingRecording: PendingRecording, session: RecordingSession) {
        recording = pendingRecording.start(ContextCompat.getMainExecutor(context)) { event ->
            when (event) {
                is VideoRecordEvent.Start -> {
                    sessionManager.appendVideoEvent(
                        session,
                        VideoEvent(
                            type = "recording_start",
                            eventTimeMillis = System.currentTimeMillis(),
                            elapsedRealtimeNanos = SystemClock.elapsedRealtimeNanos(),
                            recordingStats = event.recordingStats,
                        ),
                    )
                    sessionManager.finalizeManifest(session, "recording")
                    statusListener(
                        SessionUiState(
                            recording = true,
                            session = session,
                            statusText = "${recordingModeLabel(session.recordingConfig.recordingMode)}: ${session.sessionId} を記録中です。",
                            toastMessage = if (session.recordingConfig.bleEnabled || session.recordingConfig.arCoreEnabled) {
                                "動画・IMU・GNSS を記録中、BLE / ARCore は低頻度確認です"
                            } else {
                                "動画・IMU・GNSS を記録中です"
                            },
                        ),
                    )
                }

                is VideoRecordEvent.Status -> {
                    sessionManager.appendVideoEvent(
                        session,
                        VideoEvent(
                            type = "recording_status",
                            eventTimeMillis = System.currentTimeMillis(),
                            elapsedRealtimeNanos = SystemClock.elapsedRealtimeNanos(),
                            recordingStats = event.recordingStats,
                        ),
                    )
                    val nowNs = SystemClock.elapsedRealtimeNanos()
                    if (nowNs - lastStatusUiUpdateElapsedNs >= 1_000_000_000L) {
                        lastStatusUiUpdateElapsedNs = nowNs
                        statusListener(
                            SessionUiState(
                                recording = true,
                                session = session,
                                statusText = "記録中: ${session.sessionId} (${event.recordingStats.numBytesRecorded} bytes / ${session.activeStreamSummary()})",
                            ),
                        )
                    }
                }

                is VideoRecordEvent.Finalize -> {
                    stopCollectors()
                    sessionManager.appendVideoEvent(
                        session,
                        VideoEvent(
                            type = "recording_finalize",
                            eventTimeMillis = System.currentTimeMillis(),
                            elapsedRealtimeNanos = SystemClock.elapsedRealtimeNanos(),
                            recordingStats = event.recordingStats,
                            outputUri = event.outputResults.outputUri,
                            error = event.error.toString(),
                            cause = event.cause?.message,
                        ),
                    )
                    sessionManager.finalizeManifest(
                        session = session,
                        status = if (event.hasError()) "finalized_with_error" else "finalized",
                    )
                    sessionManager.closeSessionOutputs(session)
                    recording?.close()
                    recording = null
                    statusListener(
                        SessionUiState(
                            recording = false,
                            session = session,
                            statusText = if (event.hasError()) {
                                "セッション終了時にエラーが発生しました: ${event.error}"
                            } else {
                                if (session.recordingConfig.bleEnabled || session.recordingConfig.arCoreEnabled) {
                                    "5 系統構成のセッションを保存しました。保存先を確認してください。"
                                } else {
                                    "動画・IMU・GNSS のセッションを保存しました。保存先を確認してください。"
                                }
                            },
                            toastMessage = if (event.hasError()) {
                                null
                            } else if (session.recordingConfig.bleEnabled || session.recordingConfig.arCoreEnabled) {
                                "5 系統構成のセッションを保存しました"
                            } else {
                                "動画・IMU・GNSS のセッションを保存しました"
                            },
                            issue =
                                if (event.hasError()) {
                                    RecordingIssue(
                                        severity = RecordingIssueSeverity.ERROR,
                                        message = "セッション保存は完了しましたが、finalize 処理に異常があります。",
                                        suggestedAction = "session_manifest.json と video_events.jsonl を確認し、再度セッションを試してください。",
                                    )
                                } else {
                                    null
                                },
                        ),
                    )
                }
            }
        }
    }

    private fun stopCollectors() {
        imuLogger.stop()
        gnssLogger.stop()
        bleLogger.stop()
        arCoreLogger.stop()
    }

    private fun hasPermission(permission: String): Boolean =
        ContextCompat.checkSelfPermission(context, permission) == PermissionChecker.PERMISSION_GRANTED

    private fun bindUseCases(cameraSelector: CameraSelector) {
        val provider = cameraProvider ?: return
        val preview = Preview.Builder()
            .setTargetAspectRatio(AspectRatio.RATIO_16_9)
            .build()
            .also { it.surfaceProvider = previewView.surfaceProvider }

        val recorder = Recorder.Builder()
            .setQualitySelector(QualitySelector.from(Quality.FHD))
            .build()

        videoCapture = VideoCapture.withOutput(recorder)
        analysis = ImageAnalysis.Builder()
            .setTargetAspectRatio(AspectRatio.RATIO_16_9)
            .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
            .build()
            .also { useCase ->
                useCase.setAnalyzer(cameraExecutor) { image ->
                    currentSession?.let { session ->
                        val nowNs = SystemClock.elapsedRealtimeNanos()
                        if (nowNs - lastVideoTimestampLoggedAtNs >= session.recordingConfig.videoFrameLogIntervalMs * 1_000_000L) {
                            lastVideoTimestampLoggedAtNs = nowNs
                            val frameTimestamp = FrameTimestamp(
                                sensorTimestampNs = image.imageInfo.timestamp,
                                elapsedRealtimeNanos = nowNs,
                                wallTimeMillis = System.currentTimeMillis(),
                                rotationDegrees = image.imageInfo.rotationDegrees,
                            )
                            sessionManager.appendFrameTimestamp(session, frameTimestamp)
                        }
                    }
                    image.close()
                }
            }

        provider.unbindAll()
        provider.bindToLifecycle(
            lifecycleOwner,
            cameraSelector,
            preview,
            videoCapture,
            analysis,
        )

        statusListener(SessionUiState(false, currentSession, "カメラの準備ができました。追加センサを含む記録を開始できます。"))
    }

    private fun initializeArCoreGlSurfaceView() {
        val currentRenderer = arCoreGlSurfaceView.getTag(arCoreGlSurfaceView.id)
        if (currentRenderer !is ArCoreLogger) {
            arCoreGlSurfaceView.setEGLContextClientVersion(2)
            arCoreGlSurfaceView.preserveEGLContextOnPause = true
            arCoreGlSurfaceView.setRenderer(arCoreLogger)
            arCoreGlSurfaceView.renderMode = GLSurfaceView.RENDERMODE_WHEN_DIRTY
            arCoreGlSurfaceView.setTag(arCoreGlSurfaceView.id, arCoreLogger)
        }
    }

    private class ReplacementPreviewRenderer(
        private val imageView: ImageView,
    ) {
        @Volatile
        private var active = false
        private var firstFrame = true
        private var rotationDegrees: Int = 0
        private val logTag = "isensorium-preview"

        fun start() {
            active = true
            firstFrame = true
            imageView.post {
                imageView.visibility = View.VISIBLE
                imageView.rotation = rotationDegrees.toFloat()
            }
            Log.d(logTag, "preview renderer started")
        }

        fun stop() {
            active = false
            imageView.post {
                imageView.setImageDrawable(null)
                imageView.visibility = View.GONE
            }
            Log.d(logTag, "preview renderer stopped")
        }

        fun setRotationDegrees(degrees: Int) {
            rotationDegrees = degrees
            imageView.post {
                imageView.rotation = rotationDegrees.toFloat()
            }
        }

        fun onFrame(bitmap: Bitmap, timestampNs: Long) {
            if (!active) return
            imageView.post {
                if (!active) return@post
                if (firstFrame) {
                    firstFrame = false
                    Log.d(logTag, "preview renderer first frame ${bitmap.width}x${bitmap.height}")
                }
                imageView.setImageBitmap(bitmap)
            }
        }
    }

    private interface SessionRouteAdapter {
        fun startPreview(cameraSelector: CameraSelector)
        fun startSession()
        fun stopSession()
        fun findLatestSession(): RecordingSession?
        fun shutdown()
        fun onHostResume()
        fun onHostPause()
    }

    private inner class FrozenCameraSessionAdapter : SessionRouteAdapter {
        override fun startPreview(cameraSelector: CameraSelector) {
            startFrozenPreview(cameraSelector)
        }

        override fun startSession() {
            startFrozenSession()
        }

        override fun stopSession() {
            stopFrozenSession()
        }

        override fun findLatestSession(): RecordingSession? = sessionManager.findLatestSession()

        override fun shutdown() {
            shutdownFrozenSession()
        }

        override fun onHostResume() {
            resumeFrozenSession()
        }

        override fun onHostPause() {
            pauseFrozenSession()
        }
    }

    private inner class CoreCameraTrialSessionAdapter : SessionRouteAdapter {
        private val lifecycleMachine = TrialSharedCameraLifecycleMachine().apply { markPreviewReady() }
        private val cameraThread = HandlerThread("isensorium-shared-camera-trial").apply { start() }
        private val cameraHandler = Handler(cameraThread.looper)
        private val cameraManager = context.getSystemService(CameraManager::class.java)

        private var sharedArSession: Session? = null
        private var cameraDevice: CameraDevice? = null
        private var captureSession: CameraCaptureSession? = null
        private var videoRecorder: TrialCpuImageVideoRecorder? = null
        private var poseSampler: OffscreenArCorePoseSampler? = null
        private var sharedCameraHostResumed = false
        private var sharedCameraResumed = false
        private var closingRuntime = false
        private var previewRotationDegrees = 0
        private var collectorStatus: MutableMap<String, String> = mutableMapOf(
            "camera2" to "idle",
            "sharedCamera" to "idle",
            "video" to "idle",
            "pose" to "idle",
        )

        override fun startPreview(cameraSelector: CameraSelector) {
            startFrozenPreview(cameraSelector)
            lifecycleMachine.markPreviewReady()
            statusListener(
                SessionUiState(
                    recording = false,
                    session = currentSession,
                    statusText = "guarded replacement route を待機状態にしました。開始前の preview は frozen path を維持します。",
                ),
            )
        }

        override fun startSession() {
            if (trialRecordingActive || lifecycleMachine.state == TrialSharedCameraLifecycleState.STARTING) {
                return
            }
            lifecycleMachine.beginStart()
            cameraProvider?.unbindAll()
            analysis?.clearAnalyzer()
            replacementPreviewRenderer.start()

            val session = sessionManager.createSession()
            currentSession = session
            session.recordingConfig = recordingConfig
            sessionManager.writeInitialManifest(session)
            sessionManager.appendCollectorStatus(session, "camera2", "starting")
            sessionManager.appendCollectorStatus(session, "sharedCamera", "starting")
            sessionManager.appendCollectorStatus(session, "video", "starting")
            sessionManager.appendCollectorStatus(session, "pose", if (session.recordingConfig.arCoreEnabled) "starting" else "disabled")
            trialRecordingActive = true
            collectorStatus = mutableMapOf(
                "camera2" to "starting",
                "sharedCamera" to "starting",
                "video" to "starting",
                "pose" to if (session.recordingConfig.arCoreEnabled) "starting" else "disabled",
            )

            imuLogger.start(sensorManager, session)
            gnssLogger.start(session)
            if (session.recordingConfig.bleEnabled) {
                bleLogger.start(session)
            } else {
                sessionManager.appendCollectorStatus(session, "ble", "disabled")
            }
            if (!session.recordingConfig.arCoreEnabled) {
                sessionManager.appendCollectorStatus(session, "arcore", "disabled")
            }
            statusListener(
                SessionUiState(
                    recording = false,
                    session = session,
                    statusText = "${recordingModeLabel(session.recordingConfig.recordingMode)}で guarded replacement runtime を開始しています。",
                ),
            )
            initializeSharedCamera(session)
        }

        override fun stopSession() {
            val session = currentSession ?: return
            if (!trialRecordingActive && lifecycleMachine.state != TrialSharedCameraLifecycleState.STARTING) {
                return
            }
            lifecycleMachine.beginStop()
            session.acceptFrameTimestamps = false
            val runtimeMetadata = closeRuntime(session)
            lifecycleMachine.markStopped()
            trialRecordingActive = false
            sessionManager.closeSessionOutputs(session)
            sessionManager.finalizeManifest(
                session,
                if (runtimeMetadata["runtimeStatus"] == "error") "finalized_with_error" else "finalized",
            )
            replacementPreviewRenderer.stop()
            restoreFrozenPreview(
                session = session,
                statusText = if (runtimeMetadata["runtimeStatus"] == "error") {
                    "guarded replacement runtime をエラー付きで停止しました。frozen preview を復帰しました。"
                } else {
                    "guarded replacement runtime を終了し、frozen preview を復帰しました。"
                },
                toastMessage = if (runtimeMetadata["runtimeStatus"] == "error") null else "replacement route の session を保存しました",
                issue =
                    if (runtimeMetadata["runtimeStatus"] == "error") {
                        RecordingIssue(
                            severity = RecordingIssueSeverity.ERROR,
                            message = "replacement runtime の終了処理に異常があります。",
                            suggestedAction = "session_manifest.json と video_events.jsonl を確認し、必要なら frozen route で再試行してください。",
                        )
                    } else {
                        null
                    },
            )
        }

        override fun findLatestSession(): RecordingSession? = sessionManager.findLatestSession()

        override fun shutdown() {
            if (trialRecordingActive) {
                stopSession()
            }
            cameraProvider?.unbindAll()
            analysis?.clearAnalyzer()
            replacementPreviewRenderer.stop()
            cameraExecutor.shutdown()
            runCatching { cameraThread.quitSafely() }
        }

        override fun onHostResume() {
            sharedCameraHostResumed = true
            if (trialRecordingActive && !sharedCameraResumed) {
                resumeSharedArSession(currentSession)
            }
        }

        override fun onHostPause() {
            sharedCameraHostResumed = false
            pauseSharedArSession()
        }

        private fun initializeSharedCamera(session: RecordingSession) {
            try {
                val arSession = Session(context, setOf(Session.Feature.SHARED_CAMERA))
                arSession.configure(
                    Config(arSession).apply {
                        updateMode = Config.UpdateMode.LATEST_CAMERA_IMAGE
                    },
                )
                sharedArSession = arSession
                collectorStatus["sharedCamera"] = "ar_session_created"
                sessionManager.appendCollectorStatus(session, "sharedCamera", "ar_session_created")
                val cameraId = resolveBackCameraId(arSession)
                updatePreviewRotation(cameraId)
                replacementPreviewRenderer.setRotationDegrees(previewRotationDegrees)
                prepareOutputRuntime(session)
                openSharedCamera(arSession, session, cameraId)
            } catch (error: Exception) {
                failSharedCameraSession(session, "shared camera の初期化に失敗しました: ${error.javaClass.simpleName}。")
            }
        }

        private fun resolveBackCameraId(arSession: Session): String {
            val preferredId = arSession.cameraConfig.cameraId
            if (preferredId.isNotBlank()) {
                return preferredId
            }
            return cameraManager.cameraIdList.firstOrNull { id ->
                cameraManager.getCameraCharacteristics(id)
                    .get(CameraCharacteristics.LENS_FACING) == CameraCharacteristics.LENS_FACING_BACK
            } ?: cameraManager.cameraIdList.first()
        }

        private fun updatePreviewRotation(cameraId: String) {
            val characteristics = cameraManager.getCameraCharacteristics(cameraId)
            val sensorOrientation = characteristics.get(CameraCharacteristics.SENSOR_ORIENTATION) ?: 90
            val windowManager = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
            val displayRotation = windowManager.defaultDisplay.rotation
            val displayDegrees = when (displayRotation) {
                Surface.ROTATION_0 -> 0
                Surface.ROTATION_90 -> 90
                Surface.ROTATION_180 -> 180
                Surface.ROTATION_270 -> 270
                else -> 0
            }
            previewRotationDegrees = (sensorOrientation - displayDegrees + 360) % 360
        }

        private fun prepareOutputRuntime(session: RecordingSession) {
            videoRecorder?.release()
            videoRecorder =
                TrialCpuImageVideoRecorder(
                    outputFile = session.videoFile,
                    recordingSize = Size(640, 480),
                    callbackHandler = cameraHandler,
                ).also { it.prepare() }
            videoRecorder?.setPreviewListener(replacementPreviewRenderer::onFrame, previewFps = 5)
            sessionManager.appendCollectorStatus(session, "video", "prepared")
        }

        @SuppressLint("MissingPermission")
        private fun openSharedCamera(arSession: Session, session: RecordingSession, cameraId: String) {
            val wrappedCallback =
                arSession.sharedCamera.createARDeviceStateCallback(
                    object : CameraDevice.StateCallback() {
                        override fun onOpened(device: CameraDevice) {
                            cameraDevice = device
                            collectorStatus["camera2"] = "camera_opened"
                            sessionManager.appendCollectorStatus(session, "camera2", "camera_opened")
                            createSharedCaptureSession(device, arSession, session, cameraId)
                        }

                        override fun onDisconnected(device: CameraDevice) {
                            device.close()
                            if (!closingRuntime) {
                                failSharedCameraSession(session, "shared camera が起動中に切断されました。")
                            }
                        }

                        override fun onError(device: CameraDevice, error: Int) {
                            device.close()
                            if (!closingRuntime) {
                                failSharedCameraSession(session, "shared camera の起動に失敗しました。error=$error。")
                            }
                        }
                    },
                    cameraHandler,
                )
            cameraManager.openCamera(cameraId, wrappedCallback, cameraHandler)
        }

        private fun createSharedCaptureSession(
            device: CameraDevice,
            arSession: Session,
            session: RecordingSession,
            cameraId: String,
        ) {
            val recorderSurface = checkNotNull(videoRecorder?.surface) { "Replacement runtime recorder surface missing." }
            arSession.sharedCamera.setAppSurfaces(cameraId, listOf(recorderSurface))
            val targets =
                buildList {
                    addAll(arSession.sharedCamera.arCoreSurfaces)
                    add(recorderSurface)
                }
            val request =
                device.createCaptureRequest(CameraDevice.TEMPLATE_RECORD).apply {
                    targets.forEach(::addTarget)
                    set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_VIDEO)
                }
            val captureCallback =
                object : CameraCaptureSession.CaptureCallback() {
                    override fun onCaptureCompleted(
                        sessionCapture: CameraCaptureSession,
                        request: CaptureRequest,
                        result: TotalCaptureResult,
                    ) {
                        collectorStatus["camera2"] = "streaming"
                        sessionManager.appendCollectorStatus(session, "camera2", "streaming")
                        sessionManager.appendFrameTimestamp(
                            session,
                            FrameTimestamp(
                                sensorTimestampNs = result.get(CaptureResult.SENSOR_TIMESTAMP) ?: -1L,
                                elapsedRealtimeNanos = SystemClock.elapsedRealtimeNanos(),
                                wallTimeMillis = System.currentTimeMillis(),
                                rotationDegrees = 0,
                            ),
                        )
                    }
                }
            arSession.sharedCamera.setCaptureCallback(captureCallback, cameraHandler)
            val wrappedSessionCallback =
                arSession.sharedCamera.createARSessionStateCallback(
                    object : CameraCaptureSession.StateCallback() {
                        override fun onConfigured(cameraCaptureSession: CameraCaptureSession) {
                            captureSession = cameraCaptureSession
                            collectorStatus["sharedCamera"] = "capture_session_configured"
                            sessionManager.appendCollectorStatus(session, "sharedCamera", "capture_session_configured")
                            cameraCaptureSession.setRepeatingRequest(request.build(), captureCallback, cameraHandler)
                            checkNotNull(videoRecorder).start()
                            collectorStatus["video"] = "recording"
                            sessionManager.appendCollectorStatus(session, "video", "recording")
                            lifecycleMachine.markRunning()
                            sessionManager.appendVideoEvent(
                                session,
                                VideoEvent(
                                    type = "replacement_runtime_recording_start",
                                    eventTimeMillis = System.currentTimeMillis(),
                                    elapsedRealtimeNanos = SystemClock.elapsedRealtimeNanos(),
                                    bytesRecorded = 0L,
                                    durationNanos = 0L,
                                ),
                            )
                            sessionManager.finalizeManifest(session, "recording")
                            resumeSharedArSession(session)
                            statusListener(
                                SessionUiState(
                                    recording = true,
                                    session = session,
                                    statusText = "${recordingModeLabel(session.recordingConfig.recordingMode)}: guarded replacement runtime で ${session.sessionId} を記録中です。",
                                    toastMessage = "replacement route を有効化しました",
                                ),
                            )
                        }

                        override fun onConfigureFailed(cameraCaptureSession: CameraCaptureSession) {
                            failSharedCameraSession(session, "shared camera capture session の構成に失敗しました。")
                        }
                    },
                    cameraHandler,
                )
            device.createCaptureSession(targets, wrappedSessionCallback, cameraHandler)
        }

        private fun resumeSharedArSession(session: RecordingSession?) {
            val activeSession = sharedArSession ?: return
            val recordingSession = session ?: return
            if (!recordingSession.recordingConfig.arCoreEnabled) {
                return
            }
            runCatching { activeSession.resume() }
                .onSuccess {
                    sharedCameraResumed = true
                    sessionManager.appendCollectorStatus(recordingSession, "arcore", "resumed")
                    poseSampler?.stop()
                    poseSampler =
                        OffscreenArCorePoseSampler(cameraHandler) { frameTimestampNs, trackingState, translation, rotationQuaternion ->
                            val nowNs = SystemClock.elapsedRealtimeNanos()
                            sessionManager.appendArCorePose(
                                recordingSession,
                                ArCorePoseSample(
                                    elapsedRealtimeNanos = nowNs,
                                    wallTimeMillis = System.currentTimeMillis(),
                                    trackingState = trackingState,
                                    translation = translation.toList(),
                                    rotationQuaternion = rotationQuaternion.toList(),
                                ),
                            )
                            recordingSession.arCoreSampleCount += 1
                            sessionManager.appendCollectorStatus(recordingSession, "pose", "sampling")
                            sessionManager.appendCollectorStatus(recordingSession, "arcore", "active")
                            sessionManager.appendFrameTimestamp(
                                recordingSession,
                                FrameTimestamp(
                                    sensorTimestampNs = frameTimestampNs,
                                    elapsedRealtimeNanos = nowNs,
                                    wallTimeMillis = System.currentTimeMillis(),
                                    rotationDegrees = 0,
                                ),
                            )
                        }.also { it.start(activeSession) }
                }
                .onFailure {
                    sessionManager.appendCollectorStatus(recordingSession, "arcore", "resume_failed_${it.javaClass.simpleName}")
                }
        }

        private fun pauseSharedArSession() {
            poseSampler?.stop()
            poseSampler = null
            runCatching { sharedArSession?.pause() }
            sharedCameraResumed = false
        }

        private fun closeRuntime(session: RecordingSession): Map<String, String> {
            closingRuntime = true
            var runtimeStatus = "stopped"
            stopCollectors()
            pauseSharedArSession()
            sessionManager.appendCollectorStatus(session, "pose", "stopped")
            sessionManager.appendCollectorStatus(session, "arcore", "stopped")
            runCatching { captureSession?.stopRepeating() }
            val videoBytes =
                runCatching { videoRecorder?.stopAndRelease() ?: session.videoFile.length() }
                    .getOrElse {
                        runtimeStatus = "error"
                        session.videoFile.length()
                    }
            runCatching { captureSession?.abortCaptures() }
                .onFailure { runtimeStatus = "error" }
            runCatching { captureSession?.close() }
                .onFailure { runtimeStatus = "error" }
            captureSession = null
            runCatching { cameraDevice?.close() }
                .onFailure { runtimeStatus = "error" }
            cameraDevice = null
            runCatching { sharedArSession?.close() }
                .onFailure { runtimeStatus = "error" }
            sharedArSession = null
            videoRecorder = null
            poseSampler = null
            sharedCameraHostResumed = false
            sharedCameraResumed = false
            closingRuntime = false
            sessionManager.appendCollectorStatus(session, "video", if (videoBytes > 0L) "captured" else "empty_output")
            sessionManager.appendCollectorStatus(session, "sharedCamera", "closed")
            sessionManager.appendCollectorStatus(session, "camera2", "closed")
            if (runtimeStatus == "error") {
                sessionManager.appendCollectorStatus(session, "sharedCamera", "closed_with_error")
            }
            sessionManager.appendVideoEvent(
                session,
                VideoEvent(
                    type = "replacement_runtime_recording_finalize",
                    eventTimeMillis = System.currentTimeMillis(),
                    elapsedRealtimeNanos = SystemClock.elapsedRealtimeNanos(),
                    bytesRecorded = videoBytes,
                    durationNanos = (SystemClock.elapsedRealtimeNanos() - session.timebase.sessionStartElapsedRealtimeNanos).coerceAtLeast(0L),
                    cause = if (runtimeStatus == "error") "runtime_close_error" else null,
                ),
            )
            sessionManager.flushSessionOutputs(session)
            return mapOf("runtimeStatus" to runtimeStatus)
        }

        private fun failSharedCameraSession(session: RecordingSession, message: String) {
            lifecycleMachine.fail()
            trialRecordingActive = false
            session.acceptFrameTimestamps = false
            sessionManager.appendCollectorStatus(session, "sharedCamera", "error")
            closeRuntime(session)
            sessionManager.closeSessionOutputs(session)
            sessionManager.finalizeManifest(session, "finalized_with_error")
            replacementPreviewRenderer.stop()
            restoreFrozenPreview(
                session = session,
                statusText = "$message frozen preview を復帰しました。",
                toastMessage = null,
                issue = RecordingIssue(
                    severity = RecordingIssueSeverity.ERROR,
                    message = message,
                    suggestedAction = "route fallback 状態を確認し、必要なら frozen route で再試行してください。",
                ),
            )
        }

        private fun restoreFrozenPreview(
            session: RecordingSession,
            statusText: String,
            toastMessage: String?,
            issue: RecordingIssue? = null,
        ) {
            replacementPreviewRenderer.stop()
            startFrozenPreview(lastPreviewCameraSelector)
            statusListener(
                SessionUiState(
                    recording = false,
                    session = session,
                    statusText = statusText,
                    toastMessage = toastMessage,
                    issue = issue,
                ),
            )
        }
    }

    private inner class ImuLogger : SensorEventListener {
        private var session: RecordingSession? = null
        private var writer: FileWriter? = null
        private val lastLoggedBySensorTypeNs = mutableMapOf<String, Long>()

        fun start(sensorManager: SensorManager, recordingSession: RecordingSession) {
            session = recordingSession
            writer = FileWriter(recordingSession.imuFile, true).apply {
                append("sensor_type,event_timestamp_ns,elapsed_realtime_ns,wall_time_ms,x,y,z,accuracy\n")
                flush()
            }
            listOf(
                sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER),
                sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE),
            ).forEach { sensor ->
                sensor?.let { sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_GAME) }
            }
            lastLoggedBySensorTypeNs.clear()
        }

        fun stop() {
            sensorManager.unregisterListener(this)
            writer?.flush()
            writer?.close()
            writer = null
            session = null
        }

        override fun onSensorChanged(event: SensorEvent) {
            val activeSession = session ?: return
            val activeWriter = writer ?: return
            val nowNs = SystemClock.elapsedRealtimeNanos()
            val lastLoggedNs = lastLoggedBySensorTypeNs[event.sensor.stringType] ?: 0L
            if (nowNs - lastLoggedNs < activeSession.recordingConfig.imuIntervalMs * 1_000_000L) {
                return
            }
            lastLoggedBySensorTypeNs[event.sensor.stringType] = nowNs
            val line = buildString {
                append(event.sensor.stringType)
                append(',')
                append(event.timestamp)
                append(',')
                append(nowNs)
                append(',')
                append(System.currentTimeMillis())
                append(',')
                append(event.values.getOrNull(0) ?: 0f)
                append(',')
                append(event.values.getOrNull(1) ?: 0f)
                append(',')
                append(event.values.getOrNull(2) ?: 0f)
                append(',')
                append(event.accuracy)
                append('\n')
            }
            synchronized(activeWriter) {
                activeWriter.append(line)
            }
            activeSession.sensorSampleCount += 1
        }

        override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) = Unit
    }

    private inner class GnssLogger {
        private val fusedClient = LocationServices.getFusedLocationProviderClient(context)
        private var callback: LocationCallback? = null
        private var session: RecordingSession? = null
        private var writer: FileWriter? = null

        @SuppressLint("MissingPermission")
        fun start(recordingSession: RecordingSession) {
            if (!hasPermission(android.Manifest.permission.ACCESS_FINE_LOCATION)) {
                sessionManager.appendCollectorStatus(recordingSession, "gnss", "permission_denied")
                return
            }
            session = recordingSession
            writer = FileWriter(recordingSession.gnssFile, true).apply {
                append("provider,elapsed_realtime_ns,wall_time_ms,latitude,longitude,altitude,accuracy_m,speed_mps,bearing_deg,vertical_accuracy_m\n")
                flush()
            }
            val intervalMs = recordingSession.recordingConfig.gnssIntervalMs
            val request = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, intervalMs)
                .setMinUpdateIntervalMillis(intervalMs)
                .build()
            callback = object : LocationCallback() {
                override fun onLocationResult(result: LocationResult) {
                    result.locations.forEach { location ->
                        appendLocation(recordingSession, location)
                    }
                }
            }
            callback?.let { fusedClient.requestLocationUpdates(request, it, context.mainLooper) }
            sessionManager.appendCollectorStatus(recordingSession, "gnss", "active")
        }

        fun stop() {
            callback?.let { fusedClient.removeLocationUpdates(it) }
            writer?.flush()
            writer?.close()
            writer = null
            session = null
            callback = null
        }

        private fun appendLocation(session: RecordingSession, location: Location) {
            val activeWriter = writer ?: return
            val line = buildString {
                append(location.provider ?: "unknown")
                append(',')
                append(SystemClock.elapsedRealtimeNanos())
                append(',')
                append(System.currentTimeMillis())
                append(',')
                append(location.latitude)
                append(',')
                append(location.longitude)
                append(',')
                append(location.altitude)
                append(',')
                append(location.accuracy)
                append(',')
                append(location.speed)
                append(',')
                append(location.bearing)
                append(',')
                append(if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) location.verticalAccuracyMeters else "")
                append('\n')
            }
            synchronized(activeWriter) {
                activeWriter.append(line)
            }
            session.gnssSampleCount += 1
        }
    }

    private inner class BleLogger {
        private val bluetoothLeScanner get() = bluetoothManager.adapter?.bluetoothLeScanner
        private var session: RecordingSession? = null
        private var callback: ScanCallback? = null
        private var lastLoggedAtNs: Long = 0L

        @SuppressLint("MissingPermission")
        fun start(recordingSession: RecordingSession) {
            if (!hasPermission(android.Manifest.permission.BLUETOOTH_SCAN) ||
                !hasPermission(android.Manifest.permission.BLUETOOTH_CONNECT)
            ) {
                sessionManager.appendCollectorStatus(recordingSession, "ble", "permission_denied")
                return
            }
            session = recordingSession
            val adapter = bluetoothManager.adapter
            if (adapter == null || !adapter.isEnabled) {
                sessionManager.appendCollectorStatus(recordingSession, "ble", "bluetooth_disabled")
                return
            }
            callback = object : ScanCallback() {
                override fun onScanResult(callbackType: Int, result: ScanResult) {
                    appendResult(recordingSession, callbackType, result)
                }

                override fun onBatchScanResults(results: MutableList<ScanResult>) {
                    results.forEach { appendResult(recordingSession, -1, it) }
                }

                override fun onScanFailed(errorCode: Int) {
                    sessionManager.appendBleEvent(
                        recordingSession,
                        BleEvent(
                            elapsedRealtimeNanos = SystemClock.elapsedRealtimeNanos(),
                            wallTimeMillis = System.currentTimeMillis(),
                            callbackType = "scan_failed",
                            address = null,
                            rssi = null,
                            name = null,
                            manufacturerDataHex = null,
                            errorCode = errorCode,
                        ),
                    )
                    sessionManager.appendCollectorStatus(recordingSession, "ble", "scan_failed_$errorCode")
                }
            }
            bluetoothLeScanner?.startScan(callback)
            sessionManager.appendCollectorStatus(recordingSession, "ble", "active")
        }

        @SuppressLint("MissingPermission")
        fun stop() {
            val activeCallback = callback
            if (activeCallback != null) {
                bluetoothLeScanner?.stopScan(activeCallback)
            }
            callback = null
            session = null
        }

        private fun appendResult(session: RecordingSession, callbackType: Int, result: ScanResult) {
            val nowNs = SystemClock.elapsedRealtimeNanos()
            if (nowNs - lastLoggedAtNs < session.recordingConfig.bleIntervalMs * 1_000_000L) {
                return
            }
            lastLoggedAtNs = nowNs
            val manufacturerData = result.scanRecord?.manufacturerSpecificData
            val firstManufacturer = if (manufacturerData != null && manufacturerData.size() > 0) {
                manufacturerData.valueAt(0)?.joinToString("") { "%02x".format(it) }
            } else {
                null
            }
            sessionManager.appendBleEvent(
                session,
                BleEvent(
                    elapsedRealtimeNanos = nowNs,
                    wallTimeMillis = System.currentTimeMillis(),
                    callbackType = callbackType.toString(),
                    address = result.device?.address,
                    rssi = result.rssi,
                    name = result.scanRecord?.deviceName,
                    manufacturerDataHex = firstManufacturer,
                    errorCode = null,
                ),
            )
            session.bleSampleCount += 1
        }
    }

    private inner class ArCoreLogger : GLSurfaceView.Renderer {
        private val renderHandler = Handler(Looper.getMainLooper())
        private val renderTicker = object : Runnable {
            override fun run() {
                val recordingSession = session
                if (!started || !hostResumed || recordingSession == null) {
                    return
                }
                arCoreGlSurfaceView.requestRender()
                renderHandler.postDelayed(this, recordingSession.recordingConfig.arCoreIntervalMs)
            }
        }
        private var session: RecordingSession? = null
        private var arSession: com.google.ar.core.Session? = null
        private var lastLoggedFrameAtNs: Long = 0L
        private var textureId: Int = 0
        private var textureBound: Boolean = false
        private var hostResumed: Boolean = false
        private var started: Boolean = false

        fun start(recordingSession: RecordingSession) {
            session = recordingSession
            started = true
            val availability = ArCoreApk.getInstance().checkAvailability(context)
            sessionManager.appendCollectorStatus(recordingSession, "arcore", "availability_${availability.name.lowercase(Locale.US)}")
            if (availability.isUnsupported) {
                return
            }
            restartRenderTicker()
        }

        override fun onSurfaceCreated(gl: GL10?, config: EGLConfig?) {
            textureId = createExternalTexture()
        }

        override fun onSurfaceChanged(gl: GL10?, width: Int, height: Int) = Unit

        override fun onDrawFrame(gl: GL10?) {
            val recordingSession = session ?: return
            if (!started || !hostResumed) return

            if (arSession == null) {
                tryCreateSession(recordingSession)
            }

            val activeSession = arSession ?: return
            if (!textureBound && textureId != 0) {
                activeSession.setCameraTextureName(textureId)
                textureBound = true
            }

            try {
                val frame = activeSession.update()
                val nowNs = SystemClock.elapsedRealtimeNanos()
                if (nowNs - lastLoggedFrameAtNs < recordingSession.recordingConfig.arCoreIntervalMs * 1_000_000L) {
                    return
                }
                val camera = frame.camera
                val pose = camera.displayOrientedPose
                sessionManager.appendArCorePose(
                    recordingSession,
                    ArCorePoseSample(
                        elapsedRealtimeNanos = nowNs,
                        wallTimeMillis = System.currentTimeMillis(),
                        trackingState = camera.trackingState.name,
                        translation = pose.translation.toList(),
                        rotationQuaternion = pose.rotationQuaternion.toList(),
                    ),
                )
                recordingSession.arCoreSampleCount += 1
                lastLoggedFrameAtNs = nowNs
                if (recordingSession.arCoreSampleCount == 1L) {
                    sessionManager.appendCollectorStatus(recordingSession, "arcore", "active")
                }
            } catch (error: Exception) {
                if (lastLoggedFrameAtNs == 0L) {
                    sessionManager.appendCollectorStatus(recordingSession, "arcore", "update_failed_${error.javaClass.simpleName}")
                    lastLoggedFrameAtNs = SystemClock.elapsedRealtimeNanos()
                }
            }
        }

        private fun tryCreateSession(recordingSession: RecordingSession) {
            try {
                val createdSession = com.google.ar.core.Session(context)
                createdSession.configure(
                    Config(createdSession).apply {
                        updateMode = Config.UpdateMode.LATEST_CAMERA_IMAGE
                    },
                )
                createdSession.resume()
                arSession = createdSession
                textureBound = false
                sessionManager.appendCollectorStatus(recordingSession, "arcore", "gl_session_ready")
            } catch (error: Exception) {
                sessionManager.appendCollectorStatus(recordingSession, "arcore", "init_failed_${error.javaClass.simpleName}")
                started = false
            }
        }

        fun stop() {
            stopRenderTicker()
            arCoreGlSurfaceView.queueEvent {
                runCatching { arSession?.pause() }
                runCatching { arSession?.close() }
                arSession = null
                session = null
                lastLoggedFrameAtNs = 0L
                textureBound = false
                started = false
            }
        }

        fun onResume() {
            arCoreGlSurfaceView.queueEvent {
                hostResumed = true
                runCatching { arSession?.resume() }
            }
            restartRenderTicker()
        }

        fun onPause() {
            stopRenderTicker()
            arCoreGlSurfaceView.queueEvent {
                hostResumed = false
                runCatching { arSession?.pause() }
            }
        }

        private fun restartRenderTicker() {
            stopRenderTicker()
            val recordingSession = session ?: return
            if (!started || !hostResumed || !recordingSession.recordingConfig.arCoreEnabled) {
                return
            }
            renderHandler.post(renderTicker)
        }

        private fun stopRenderTicker() {
            renderHandler.removeCallbacks(renderTicker)
        }

        private fun createExternalTexture(): Int {
            val textures = IntArray(1)
            GLES20.glGenTextures(1, textures, 0)
            GLES20.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, textures[0])
            GLES20.glTexParameteri(
                GLES11Ext.GL_TEXTURE_EXTERNAL_OES,
                GLES20.GL_TEXTURE_MIN_FILTER,
                GLES20.GL_LINEAR,
            )
            GLES20.glTexParameteri(
                GLES11Ext.GL_TEXTURE_EXTERNAL_OES,
                GLES20.GL_TEXTURE_MAG_FILTER,
                GLES20.GL_LINEAR,
            )
            GLES20.glTexParameteri(
                GLES11Ext.GL_TEXTURE_EXTERNAL_OES,
                GLES20.GL_TEXTURE_WRAP_S,
                GLES20.GL_CLAMP_TO_EDGE,
            )
            GLES20.glTexParameteri(
                GLES11Ext.GL_TEXTURE_EXTERNAL_OES,
                GLES20.GL_TEXTURE_WRAP_T,
                GLES20.GL_CLAMP_TO_EDGE,
            )
            return textures[0]
        }
    }
}

data class SessionUiState(
    val recording: Boolean,
    val session: RecordingSession?,
    val statusText: String,
    val toastMessage: String? = null,
    val issue: RecordingIssue? = null,
)

data class RecordingSession(
    val sessionId: String,
    val sessionDir: File,
    val manifestFile: File,
    val videoFile: File,
    val imuFile: File,
    val gnssFile: File,
    val bleFile: File,
    val arCoreFile: File,
    val frameTimestampsFile: File,
    val videoEventsFile: File,
    val timebase: SessionTimebase,
    val adapterMetadata: SessionAdapterMetadata,
    @Volatile var acceptFrameTimestamps: Boolean = true,
    var sensorSampleCount: Long = 0L,
    var gnssSampleCount: Long = 0L,
    var bleSampleCount: Long = 0L,
    var arCoreSampleCount: Long = 0L,
    var recordingConfig: RecordingConfig = RecordingConfig(),
) {
    fun listOutputFiles(): List<File> = listOf(
        manifestFile,
        videoFile,
        imuFile,
        gnssFile,
        bleFile,
        arCoreFile,
        frameTimestampsFile,
        videoEventsFile,
    ).filter { it.exists() }

    fun activeStreamSummary(): String =
        "imu=$sensorSampleCount gps=$gnssSampleCount ble=$bleSampleCount ar=$arCoreSampleCount"
}

data class RecordingConfig(
    val videoFrameLogIntervalMs: Long = 100L,
    val imuIntervalMs: Long = 20L,
    val gnssIntervalMs: Long = 1000L,
    val bleIntervalMs: Long = 2000L,
    val arCoreIntervalMs: Long = 2000L,
    val bleEnabled: Boolean = true,
    val arCoreEnabled: Boolean = true,
    val recordingMode: RecordingMode = RecordingMode.STANDARD_HANDHELD,
)

data class SessionTimebase(
    val sessionStartWallTimeMs: Long,
    val sessionStartElapsedRealtimeNanos: Long,
)

data class FrameTimestamp(
    val sensorTimestampNs: Long,
    val elapsedRealtimeNanos: Long,
    val wallTimeMillis: Long,
    val rotationDegrees: Int,
)

data class VideoEvent(
    val type: String,
    val eventTimeMillis: Long,
    val elapsedRealtimeNanos: Long,
    val recordingStats: androidx.camera.video.RecordingStats? = null,
    val bytesRecorded: Long? = null,
    val durationNanos: Long? = null,
    val outputUri: Uri? = null,
    val error: String? = null,
    val cause: String? = null,
)

data class BleEvent(
    val elapsedRealtimeNanos: Long,
    val wallTimeMillis: Long,
    val callbackType: String,
    val address: String?,
    val rssi: Int?,
    val name: String?,
    val manufacturerDataHex: String?,
    val errorCode: Int?,
)

data class ArCorePoseSample(
    val elapsedRealtimeNanos: Long,
    val wallTimeMillis: Long,
    val trackingState: String,
    val translation: List<Float>,
    val rotationQuaternion: List<Float>,
)

class SessionManager(
    private val context: Context,
    private val routeResolution: RouteResolution,
) {
    private val timestampFormat = SimpleDateFormat("yyyyMMdd-HHmmss", Locale.US)
    private val sessionWriters = ConcurrentHashMap<String, SessionWriters>()

    fun createSession(): RecordingSession {
        val startedWall = System.currentTimeMillis()
        val startedMono = SystemClock.elapsedRealtimeNanos()
        val sessionId = "session-${timestampFormat.format(Date(startedWall))}"
        val root = File(
            context.getExternalFilesDir(Environment.DIRECTORY_DOCUMENTS),
            "sessions/$sessionId",
        )
        root.mkdirs()

        return RecordingSession(
            sessionId = sessionId,
            sessionDir = root,
            manifestFile = File(root, "session_manifest.json"),
            videoFile = File(root, "video.mp4"),
            imuFile = File(root, "imu.csv"),
            gnssFile = File(root, "gnss.csv"),
            bleFile = File(root, "ble_scan.jsonl"),
            arCoreFile = File(root, "arcore_pose.jsonl"),
            frameTimestampsFile = File(root, "video_frame_timestamps.csv"),
            videoEventsFile = File(root, "video_events.jsonl"),
            timebase = SessionTimebase(startedWall, startedMono),
            adapterMetadata = GuardedUpstreamTrialContract.buildSessionAdapterMetadata(routeResolution),
        )
    }

    fun writeInitialManifest(session: RecordingSession) {
        sessionWriters.putIfAbsent(session.sessionId, SessionWriters.openFor(session))
        session.manifestFile.writeText(
            JSONObject()
                .put("sessionId", session.sessionId)
                .put("status", "initialized")
                .put("deviceModel", Build.MODEL)
                .put("recordingRoot", session.sessionDir.absolutePath)
                .put(
                    "timebase",
                    JSONObject()
                        .put("sessionStartWallTimeMs", session.timebase.sessionStartWallTimeMs)
                        .put("sessionStartElapsedRealtimeNanos", session.timebase.sessionStartElapsedRealtimeNanos),
                )
                .put("recordingMode", session.recordingConfig.recordingMode.modeId)
                .put("recordingModeLabel", recordingModeLabel(session.recordingConfig.recordingMode))
                .put("recordingConfig", recordingConfigJson(session.recordingConfig))
                .put("modeBehavior", modeBehaviorJson(session.recordingConfig))
                .put("sessionAdapter", GuardedUpstreamTrialContract.sessionAdapterMetadataJson(session.adapterMetadata))
                .put("guardedUpstreamTrial", GuardedUpstreamTrialContract.guardedUpstreamTrialJson(routeResolution))
                .put(
                    "streams",
                    JSONArray()
                        .put(JSONObject().put("name", "video").put("file", session.videoFile.name).put("frameTimestampsFile", session.frameTimestampsFile.name))
                        .put(JSONObject().put("name", "imu").put("file", session.imuFile.name))
                        .put(JSONObject().put("name", "gnss").put("file", session.gnssFile.name))
                        .put(JSONObject().put("name", "ble").put("file", session.bleFile.name))
                        .put(JSONObject().put("name", "arcore").put("file", session.arCoreFile.name)),
                )
                .put("collectorStatus", JSONObject())
                .toString(2),
        )
    }

    fun finalizeManifest(session: RecordingSession, status: String) {
        val manifest = JSONObject(
            session.manifestFile.takeIf { it.exists() }?.readText()
                ?: JSONObject().put("sessionId", session.sessionId).toString(),
        )
        manifest.put("status", status)
        manifest.put("imuSampleCount", session.sensorSampleCount)
        manifest.put("gnssSampleCount", session.gnssSampleCount)
        manifest.put("bleSampleCount", session.bleSampleCount)
        manifest.put("arCoreSampleCount", session.arCoreSampleCount)
        manifest.put("recordingMode", session.recordingConfig.recordingMode.modeId)
        manifest.put("recordingModeLabel", recordingModeLabel(session.recordingConfig.recordingMode))
        manifest.put("recordingConfig", recordingConfigJson(session.recordingConfig))
        manifest.put("modeBehavior", modeBehaviorJson(session.recordingConfig))
        writeManifestWithResolvedFileSizes(session, manifest)
    }

    fun flushSessionOutputs(session: RecordingSession) {
        sessionWriters[session.sessionId]?.flush()
    }

    fun closeSessionOutputs(session: RecordingSession) {
        sessionWriters.remove(session.sessionId)?.close()
    }

    fun appendCollectorStatus(session: RecordingSession, collector: String, status: String) {
        val manifest = JSONObject(session.manifestFile.readText())
        val statusObject = manifest.optJSONObject("collectorStatus") ?: JSONObject()
        statusObject.put(collector, status)
        manifest.put("collectorStatus", statusObject)
        session.manifestFile.writeText(manifest.toString(2))
    }

    fun appendFrameTimestamp(session: RecordingSession, frameTimestamp: FrameTimestamp) {
        if (!session.acceptFrameTimestamps) {
            return
        }
        val writers = sessionWriters.getOrPut(session.sessionId) { SessionWriters.openFor(session) }
        val sessionElapsed = frameTimestamp.elapsedRealtimeNanos - session.timebase.sessionStartElapsedRealtimeNanos
        synchronized(writers.frameTimestampsWriter) {
            writers.frameTimestampsWriter.append(
                "${frameTimestamp.sensorTimestampNs},${frameTimestamp.elapsedRealtimeNanos},${frameTimestamp.wallTimeMillis},${frameTimestamp.rotationDegrees},$sessionElapsed\n",
            )
        }
    }

    private fun writeManifestWithResolvedFileSizes(session: RecordingSession, manifest: JSONObject) {
        val firstPassFiles =
            JSONArray().apply {
                session.listOutputFiles().forEach { file ->
                    put(JSONObject().put("name", file.name).put("sizeBytes", file.length()))
                }
            }
        manifest.put("files", firstPassFiles)
        session.manifestFile.writeText(manifest.toString(2))

        val secondPassFiles =
            JSONArray().apply {
                session.listOutputFiles().forEach { file ->
                    put(
                        JSONObject()
                            .put("name", file.name)
                            .put("sizeBytes", if (file == session.manifestFile) session.manifestFile.length() else file.length()),
                    )
                }
            }
        manifest.put("files", secondPassFiles)
        session.manifestFile.writeText(manifest.toString(2))
    }

    fun appendVideoEvent(session: RecordingSession, event: VideoEvent) {
        val writers = sessionWriters.getOrPut(session.sessionId) { SessionWriters.openFor(session) }
        val payload = JSONObject()
            .put("type", event.type)
            .put("eventTimeMillis", event.eventTimeMillis)
            .put("elapsedRealtimeNanos", event.elapsedRealtimeNanos)
            .put("bytesRecorded", event.bytesRecorded ?: event.recordingStats?.numBytesRecorded ?: 0L)
            .put("durationNanos", event.durationNanos ?: event.recordingStats?.recordedDurationNanos ?: 0L)
            .put("outputUri", event.outputUri?.toString())
            .put("error", event.error)
            .put("cause", event.cause)
        synchronized(writers.videoEventsWriter) {
            writers.videoEventsWriter.append("${payload}\n")
        }
    }

    fun appendBleEvent(session: RecordingSession, event: BleEvent) {
        val writers = sessionWriters.getOrPut(session.sessionId) { SessionWriters.openFor(session) }
        val payload = JSONObject()
            .put("elapsedRealtimeNanos", event.elapsedRealtimeNanos)
            .put("wallTimeMillis", event.wallTimeMillis)
            .put("callbackType", event.callbackType)
            .put("address", event.address)
            .put("rssi", event.rssi)
            .put("name", event.name)
            .put("manufacturerDataHex", event.manufacturerDataHex)
            .put("errorCode", event.errorCode)
        synchronized(writers.bleWriter) {
            writers.bleWriter.append("${payload}\n")
        }
    }

    fun appendArCorePose(session: RecordingSession, sample: ArCorePoseSample) {
        val writers = sessionWriters.getOrPut(session.sessionId) { SessionWriters.openFor(session) }
        val payload = JSONObject()
            .put("elapsedRealtimeNanos", sample.elapsedRealtimeNanos)
            .put("wallTimeMillis", sample.wallTimeMillis)
            .put("trackingState", sample.trackingState)
            .put("translation", JSONArray(sample.translation))
            .put("rotationQuaternion", JSONArray(sample.rotationQuaternion))
        synchronized(writers.arCoreWriter) {
            writers.arCoreWriter.append("${payload}\n")
        }
    }

    fun findLatestSession(): RecordingSession? {
        val sessionsRoot = File(
            context.getExternalFilesDir(Environment.DIRECTORY_DOCUMENTS),
            "sessions",
        )
        val latestDir = sessionsRoot.listFiles { file -> file.isDirectory && file.name.startsWith("session-") }
            ?.maxByOrNull { it.name }
            ?: return null
        val manifestFile = File(latestDir, "session_manifest.json")
        val manifest = manifestFile.takeIf { it.exists() }?.readText()?.let(::JSONObject)
        val timebase = manifest?.optJSONObject("timebase")
        val adapterMetadata =
            GuardedUpstreamTrialContract.sessionAdapterMetadataFromJson(manifest?.optJSONObject("sessionAdapter"))
                ?: GuardedUpstreamTrialContract.buildSessionAdapterMetadata(routeResolution)
        return RecordingSession(
            sessionId = latestDir.name,
            sessionDir = latestDir,
            manifestFile = manifestFile,
            videoFile = File(latestDir, "video.mp4"),
            imuFile = File(latestDir, "imu.csv"),
            gnssFile = File(latestDir, "gnss.csv"),
            bleFile = File(latestDir, "ble_scan.jsonl"),
            arCoreFile = File(latestDir, "arcore_pose.jsonl"),
            frameTimestampsFile = File(latestDir, "video_frame_timestamps.csv"),
            videoEventsFile = File(latestDir, "video_events.jsonl"),
            timebase = SessionTimebase(
                sessionStartWallTimeMs = timebase?.optLong("sessionStartWallTimeMs") ?: latestDir.lastModified(),
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

    private fun recordingConfigJson(config: RecordingConfig): JSONObject =
        JSONObject()
            .put("videoFrameLogIntervalMs", config.videoFrameLogIntervalMs)
            .put("imuIntervalMs", config.imuIntervalMs)
            .put("gnssIntervalMs", config.gnssIntervalMs)
            .put("bleIntervalMs", config.bleIntervalMs)
            .put("arCoreIntervalMs", config.arCoreIntervalMs)
            .put("bleEnabled", config.bleEnabled)
            .put("arCoreEnabled", config.arCoreEnabled)
            .put("recordingMode", config.recordingMode.modeId)

    private fun modeBehaviorJson(config: RecordingConfig): JSONObject =
        JSONObject()
            .put("displayLabel", recordingModeLabel(config.recordingMode))
            .put(
                "optionalSensorPolicy",
                if (config.recordingMode == RecordingMode.POCKET_RECORDING) {
                    "low_frequency_confirmation"
                } else {
                    "operator_selected"
                },
            )
            .put("videoFrameLogIntervalMs", config.videoFrameLogIntervalMs)
            .put("bleIntervalMs", config.bleIntervalMs)
            .put("arCoreIntervalMs", config.arCoreIntervalMs)

    private fun recordingModeLabel(mode: RecordingMode): String =
        when (mode) {
            RecordingMode.STANDARD_HANDHELD -> "通常計測"
            RecordingMode.POCKET_RECORDING -> "ポケット収納計測"
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

    private data class SessionWriters(
        val frameTimestampsWriter: BufferedWriter,
        val videoEventsWriter: BufferedWriter,
        val bleWriter: BufferedWriter,
        val arCoreWriter: BufferedWriter,
    ) {
        fun flush() {
            synchronized(frameTimestampsWriter) { frameTimestampsWriter.flush() }
            synchronized(videoEventsWriter) { videoEventsWriter.flush() }
            synchronized(bleWriter) { bleWriter.flush() }
            synchronized(arCoreWriter) { arCoreWriter.flush() }
        }

        fun close() {
            flush()
            synchronized(frameTimestampsWriter) { frameTimestampsWriter.close() }
            synchronized(videoEventsWriter) { videoEventsWriter.close() }
            synchronized(bleWriter) { bleWriter.close() }
            synchronized(arCoreWriter) { arCoreWriter.close() }
        }

        companion object {
            fun openFor(session: RecordingSession): SessionWriters {
                val frameWriter = FileWriter(session.frameTimestampsFile, true).buffered().apply {
                    if (session.frameTimestampsFile.length() == 0L) {
                        append("camera_sensor_timestamp_ns,elapsed_realtime_ns,wall_time_ms,rotation_degrees,session_elapsed_ns\n")
                    }
                }
                val videoWriter = FileWriter(session.videoEventsFile, true).buffered()
                val bleWriter = FileWriter(session.bleFile, true).buffered()
                val arCoreWriter = FileWriter(session.arCoreFile, true).buffered()
                return SessionWriters(frameWriter, videoWriter, bleWriter, arCoreWriter)
            }
        }
    }
}
