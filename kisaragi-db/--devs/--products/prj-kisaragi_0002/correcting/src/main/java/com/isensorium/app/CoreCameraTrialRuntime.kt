package com.isensorium.app

import android.graphics.ImageFormat
import android.graphics.Bitmap
import android.media.Image
import android.media.ImageReader
import android.media.MediaCodec
import android.media.MediaCodecInfo
import android.media.MediaFormat
import android.media.MediaMuxer
import android.opengl.EGL14
import android.opengl.EGLConfig
import android.opengl.EGLContext
import android.opengl.EGLDisplay
import android.opengl.EGLSurface
import android.opengl.GLES11Ext
import android.opengl.GLES20
import android.os.Handler
import android.os.SystemClock
import android.util.Size
import android.view.Surface
import android.util.Log
import com.google.ar.core.Session
import com.google.ar.core.TrackingState
import com.google.ar.core.exceptions.NotYetAvailableException
import java.io.File
import java.nio.ByteBuffer

enum class TrialSharedCameraLifecycleState {
    IDLE,
    PREVIEW_READY,
    STARTING,
    RUNNING,
    STOPPING,
    STOPPED,
    ERROR,
}

class TrialSharedCameraLifecycleMachine {
    var state: TrialSharedCameraLifecycleState = TrialSharedCameraLifecycleState.IDLE
        private set

    fun markPreviewReady() {
        if (
            state == TrialSharedCameraLifecycleState.IDLE ||
            state == TrialSharedCameraLifecycleState.STOPPED ||
            state == TrialSharedCameraLifecycleState.ERROR
        ) {
            state = TrialSharedCameraLifecycleState.PREVIEW_READY
        }
    }

    fun beginStart() {
        require(state == TrialSharedCameraLifecycleState.PREVIEW_READY || state == TrialSharedCameraLifecycleState.STOPPED) {
            "Cannot start from $state"
        }
        state = TrialSharedCameraLifecycleState.STARTING
    }

    fun markRunning() {
        require(state == TrialSharedCameraLifecycleState.STARTING) {
            "Cannot mark running from $state"
        }
        state = TrialSharedCameraLifecycleState.RUNNING
    }

    fun beginStop() {
        require(state == TrialSharedCameraLifecycleState.RUNNING || state == TrialSharedCameraLifecycleState.STARTING) {
            "Cannot stop from $state"
        }
        state = TrialSharedCameraLifecycleState.STOPPING
    }

    fun markStopped() {
        require(state == TrialSharedCameraLifecycleState.STOPPING) {
            "Cannot mark stopped from $state"
        }
        state = TrialSharedCameraLifecycleState.STOPPED
    }

    fun fail() {
        state = TrialSharedCameraLifecycleState.ERROR
    }
}

class TrialCpuImageVideoRecorder(
    private val outputFile: File,
    private val recordingSize: Size,
    private val callbackHandler: Handler,
    private val targetFrameRate: Int = 10,
) {
    private val logTag = "isensorium-preview"
    private val minFrameIntervalNs = 1_000_000_000L / targetFrameRate
    private var previewListener: ((Bitmap, Long) -> Unit)? = null
    private var previewFrameIntervalNs: Long = 200_000_000L
    private var lastPreviewTimestampNs = Long.MIN_VALUE
    private var lastPreviewLogNs = Long.MIN_VALUE

    private var imageReader: ImageReader? = null
    private var codec: MediaCodec? = null
    private var muxer: MediaMuxer? = null
    private var bufferInfo: MediaCodec.BufferInfo? = null
    private var trackIndex = -1
    private var muxerStarted = false
    private var encoderStarted = false
    private var recording = false
    private var startSensorTimestampNs: Long? = null
    private var lastAcceptedTimestampNs = Long.MIN_VALUE

    val surface: Surface
        get() = checkNotNull(imageReader?.surface) { "ImageReader is not prepared." }

    fun prepare() {
        outputFile.parentFile?.mkdirs()
        if (outputFile.exists()) {
            outputFile.delete()
        }
        imageReader?.close()
        imageReader = ImageReader.newInstance(
            recordingSize.width,
            recordingSize.height,
            ImageFormat.YUV_420_888,
            3,
        ).apply {
            setOnImageAvailableListener({ reader ->
                val image = reader.acquireLatestImage() ?: return@setOnImageAvailableListener
                handleImage(image)
            }, callbackHandler)
        }
        releaseEncoder()
        startSensorTimestampNs = null
        lastAcceptedTimestampNs = Long.MIN_VALUE
        lastPreviewTimestampNs = Long.MIN_VALUE
        lastPreviewLogNs = Long.MIN_VALUE
        recording = false
    }

    fun start() {
        initializeEncoder()
        recording = true
    }

    fun setPreviewListener(listener: ((Bitmap, Long) -> Unit)?, previewFps: Int = 5) {
        previewListener = listener
        val fps = previewFps.coerceAtLeast(1)
        previewFrameIntervalNs = 1_000_000_000L / fps
        lastPreviewTimestampNs = Long.MIN_VALUE
        lastPreviewLogNs = Long.MIN_VALUE
    }

    fun stopAndRelease(): Long {
        recording = false
        finishEncoding()
        imageReader?.close()
        imageReader = null
        startSensorTimestampNs = null
        lastAcceptedTimestampNs = Long.MIN_VALUE
        return outputFile.length()
    }

    fun release() {
        recording = false
        releaseEncoder()
        imageReader?.close()
        imageReader = null
        startSensorTimestampNs = null
        lastAcceptedTimestampNs = Long.MIN_VALUE
    }

    private fun handleImage(image: Image) {
        image.use { current ->
            if (!recording) {
                return
            }
            val timestampNs = current.timestamp
            if (timestampNs <= 0L) {
                return
            }
            if (lastAcceptedTimestampNs != Long.MIN_VALUE && timestampNs - lastAcceptedTimestampNs < minFrameIntervalNs) {
                return
            }
            val startTimestamp = startSensorTimestampNs ?: timestampNs.also { startSensorTimestampNs = it }
            val frameBytes = yuv420888ToI420(current)
            queueFrame(
                frameData = frameBytes,
                presentationTimeUs = ((timestampNs - startTimestamp) / 1_000L).coerceAtLeast(0L),
            )
            lastAcceptedTimestampNs = timestampNs
            maybeEmitPreview(current, timestampNs)
        }
    }

    private fun maybeEmitPreview(image: Image, timestampNs: Long) {
        val listener = previewListener ?: return
        if (lastPreviewTimestampNs != Long.MIN_VALUE &&
            timestampNs - lastPreviewTimestampNs < previewFrameIntervalNs
        ) {
            return
        }
        val bitmap = runCatching { yuv420888ToBitmap(image) }.getOrNull()
        if (bitmap == null) {
            val nowNs = SystemClock.elapsedRealtimeNanos()
            if (lastPreviewLogNs == Long.MIN_VALUE || nowNs - lastPreviewLogNs > 2_000_000_000L) {
                lastPreviewLogNs = nowNs
                Log.d(logTag, "preview frame dropped: bitmap decode failed")
            }
            return
        }
        lastPreviewTimestampNs = timestampNs
        listener.invoke(bitmap, timestampNs)
        val nowNs = SystemClock.elapsedRealtimeNanos()
        if (lastPreviewLogNs == Long.MIN_VALUE || nowNs - lastPreviewLogNs > 2_000_000_000L) {
            lastPreviewLogNs = nowNs
            Log.d(logTag, "preview frame emitted: ${bitmap.width}x${bitmap.height}")
        }
    }

    private fun initializeEncoder() {
        if (encoderStarted) {
            return
        }
        val activeCodec = MediaCodec.createEncoderByType(MediaFormat.MIMETYPE_VIDEO_AVC)
        val format = MediaFormat.createVideoFormat(
            MediaFormat.MIMETYPE_VIDEO_AVC,
            recordingSize.width,
            recordingSize.height,
        ).apply {
            setInteger(MediaFormat.KEY_COLOR_FORMAT, MediaCodecInfo.CodecCapabilities.COLOR_FormatYUV420Flexible)
            setInteger(MediaFormat.KEY_BIT_RATE, recordingSize.width * recordingSize.height * 4)
            setInteger(MediaFormat.KEY_FRAME_RATE, targetFrameRate)
            setInteger(MediaFormat.KEY_I_FRAME_INTERVAL, 1)
        }
        val activeMuxer = MediaMuxer(outputFile.absolutePath, MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4)
        activeCodec.configure(format, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE)
        activeCodec.start()
        codec = activeCodec
        muxer = activeMuxer
        bufferInfo = MediaCodec.BufferInfo()
        trackIndex = -1
        muxerStarted = false
        encoderStarted = true
    }

    private fun queueFrame(
        frameData: ByteArray,
        presentationTimeUs: Long,
    ) {
        val activeCodec = codec ?: return
        drainCodec(activeCodec, endOfStream = false)
        val inputIndex = activeCodec.dequeueInputBuffer(0L)
        if (inputIndex < 0) {
            logCodecDrop("encoder input buffer unavailable")
            return
        }
        activeCodec.getInputBuffer(inputIndex)?.apply {
            clear()
            put(frameData)
        } ?: run {
            logCodecDrop("encoder input buffer missing")
            return
        }
        activeCodec.queueInputBuffer(inputIndex, 0, frameData.size, presentationTimeUs, 0)
        drainCodec(activeCodec, endOfStream = false)
    }

    private fun finishEncoding() {
        val activeCodec = codec ?: return
        drainCodec(activeCodec, endOfStream = false)
        val presentationTimeUs =
            ((lastAcceptedTimestampNs - (startSensorTimestampNs ?: lastAcceptedTimestampNs)) / 1_000L).coerceAtLeast(0L)
        var eosQueued = false
        repeat(10) {
            val inputIndex = activeCodec.dequeueInputBuffer(TIMEOUT_US)
            if (inputIndex >= 0) {
                activeCodec.queueInputBuffer(
                    inputIndex,
                    0,
                    0,
                    presentationTimeUs,
                    MediaCodec.BUFFER_FLAG_END_OF_STREAM,
                )
                eosQueued = true
                return@repeat
            }
            drainCodec(activeCodec, endOfStream = false)
        }
        if (!eosQueued) {
            logCodecDrop("encoder EOS queue retry exceeded")
        }
        drainCodec(activeCodec, endOfStream = true)
        releaseEncoder()
    }

    private fun drainCodec(
        activeCodec: MediaCodec,
        endOfStream: Boolean,
    ) {
        val activeMuxer = muxer ?: return
        val activeBufferInfo = bufferInfo ?: return
        val stopDeadlineNs =
            if (endOfStream) {
                SystemClock.elapsedRealtimeNanos() + STOP_DRAIN_TIMEOUT_NS
            } else {
                Long.MAX_VALUE
            }
        while (true) {
            val outputIndex = activeCodec.dequeueOutputBuffer(activeBufferInfo, TIMEOUT_US)
            when {
                outputIndex == MediaCodec.INFO_TRY_AGAIN_LATER && !endOfStream -> return
                outputIndex == MediaCodec.INFO_TRY_AGAIN_LATER -> {
                    if (SystemClock.elapsedRealtimeNanos() >= stopDeadlineNs) {
                        logCodecDrop("encoder EOS drain timeout")
                        return
                    }
                    continue
                }
                outputIndex == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED -> {
                    if (!muxerStarted) {
                        trackIndex = activeMuxer.addTrack(activeCodec.outputFormat)
                        activeMuxer.start()
                        muxerStarted = true
                    }
                }
                outputIndex >= 0 -> {
                    val outputBuffer = activeCodec.getOutputBuffer(outputIndex) ?: break
                    if (activeBufferInfo.size > 0 && muxerStarted && trackIndex >= 0) {
                        outputBuffer.position(activeBufferInfo.offset)
                        outputBuffer.limit(activeBufferInfo.offset + activeBufferInfo.size)
                        activeMuxer.writeSampleData(trackIndex, outputBuffer, activeBufferInfo)
                    }
                    activeCodec.releaseOutputBuffer(outputIndex, false)
                    if ((activeBufferInfo.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM) != 0) {
                        return
                    }
                }
            }
        }
    }

    private fun releaseEncoder() {
        val activeCodec = codec
        val activeMuxer = muxer
        codec = null
        muxer = null
        bufferInfo = null
        encoderStarted = false
        if (activeCodec != null) {
            runCatching { activeCodec.stop() }
            activeCodec.release()
        }
        if (activeMuxer != null) {
            if (muxerStarted && trackIndex >= 0) {
                runCatching { activeMuxer.stop() }
            }
            activeMuxer.release()
        }
        trackIndex = -1
        muxerStarted = false
    }

    private fun logCodecDrop(reason: String) {
        val nowNs = SystemClock.elapsedRealtimeNanos()
        if (lastPreviewLogNs == Long.MIN_VALUE || nowNs - lastPreviewLogNs > 2_000_000_000L) {
            lastPreviewLogNs = nowNs
            Log.w(logTag, "video frame dropped: $reason")
        }
    }

    private fun yuv420888ToI420(image: Image): ByteArray {
        val width = image.width
        val height = image.height
        val ySize = width * height
        val uvSize = width * height / 4
        val output = ByteArray(ySize + uvSize * 2)
        copyPlane(image.planes[0], width, height, output, 0)
        copyPlane(image.planes[1], width / 2, height / 2, output, ySize)
        copyPlane(image.planes[2], width / 2, height / 2, output, ySize + uvSize)
        return output
    }

    private fun yuv420888ToBitmap(image: Image): Bitmap? {
        val width = image.width
        val height = image.height
        val yPlane = image.planes.getOrNull(0) ?: return null
        val uPlane = image.planes.getOrNull(1) ?: return null
        val vPlane = image.planes.getOrNull(2) ?: return null

        val yBuffer = yPlane.buffer.duplicate()
        val uBuffer = uPlane.buffer.duplicate()
        val vBuffer = vPlane.buffer.duplicate()
        val yRowStride = yPlane.rowStride
        val yPixelStride = yPlane.pixelStride
        val uvRowStride = uPlane.rowStride
        val uvPixelStride = uPlane.pixelStride

        val out = IntArray(width * height)
        var outIndex = 0
        var row = 0
        while (row < height) {
            val yRowOffset = row * yRowStride
            val uvRowOffset = (row / 2) * uvRowStride
            var col = 0
            while (col < width) {
                val y = (yBuffer.get(yRowOffset + col * yPixelStride).toInt() and 0xFF)
                val uvOffset = uvRowOffset + (col / 2) * uvPixelStride
                val u = (uBuffer.get(uvOffset).toInt() and 0xFF) - 128
                val v = (vBuffer.get(uvOffset).toInt() and 0xFF) - 128
                val c = y - 16
                val r = (298 * c + 409 * v + 128) shr 8
                val g = (298 * c - 100 * u - 208 * v + 128) shr 8
                val b = (298 * c + 516 * u + 128) shr 8
                val cr = r.coerceIn(0, 255)
                val cg = g.coerceIn(0, 255)
                val cb = b.coerceIn(0, 255)
                out[outIndex++] = (0xFF shl 24) or (cr shl 16) or (cg shl 8) or cb
                col++
            }
            row++
        }
        return Bitmap.createBitmap(out, width, height, Bitmap.Config.ARGB_8888)
    }


    private fun copyPlane(
        plane: Image.Plane,
        width: Int,
        height: Int,
        output: ByteArray,
        outputOffset: Int,
    ) {
        val buffer = plane.buffer
        val rowStride = plane.rowStride
        val pixelStride = plane.pixelStride
        var outputIndex = outputOffset
        val rowData = ByteArray(rowStride)
        for (row in 0 until height) {
            val length = if (pixelStride == 1) width else (width - 1) * pixelStride + 1
            buffer.position(row * rowStride)
            buffer.get(rowData, 0, length)
            var column = 0
            while (column < width) {
                output[outputIndex++] = rowData[column * pixelStride]
                column += 1
            }
        }
    }
    private companion object {
        const val TIMEOUT_US = 10_000L
        const val STOP_DRAIN_TIMEOUT_NS = 5_000_000_000L
    }
}

data class OffscreenArCorePoseFrame(
    val updateIndex: Long,
    val frameTimestampNs: Long,
    val captureTimestampNs: Long,
    val trackingState: String,
    val trackingFailureReason: String?,
    val translation: FloatArray,
    val rotationQuaternion: FloatArray,
    val imageFocalLength: List<Float> = emptyList(),
    val imagePrincipalPoint: List<Float> = emptyList(),
    val imageDimensions: List<Int> = emptyList(),
    val textureFocalLength: List<Float> = emptyList(),
    val texturePrincipalPoint: List<Float> = emptyList(),
    val textureDimensions: List<Int> = emptyList(),
    val imageIntrinsicsRequested: Boolean = false,
    val imageIntrinsicsSucceeded: Boolean = false,
    val imageIntrinsicsFailureReason: String? = null,
    val textureIntrinsicsRequested: Boolean = false,
    val textureIntrinsicsSucceeded: Boolean = false,
    val textureIntrinsicsFailureReason: String? = null,
    val imageFileName: String,
)

class OffscreenArCorePoseSampler(
    private val handler: Handler,
    private val sampleIntervalMs: Long,
    private val imageOutputDir: File,
    private val frameRecordEveryNUpdates: Int,
    private val saveOnlyWhenTracking: Boolean,
    private val onPose: (OffscreenArCorePoseFrame) -> Unit,
) {
    private var session: Session? = null
    private var running = false
    private var lastFrameTimestampNs = -1L
    private var updateIndex = 0L

    private var eglDisplay: EGLDisplay = EGL14.EGL_NO_DISPLAY
    private var eglContext: EGLContext = EGL14.EGL_NO_CONTEXT
    private var eglSurface: EGLSurface = EGL14.EGL_NO_SURFACE
    private var cameraTextureId = 0

    private val samplingRunnable = object : Runnable {
        override fun run() {
            if (!running) {
                return
            }
            val arSession = session
            if (arSession != null) {
                runCatching {
                    makeCurrent()
                    val frame = arSession.update()
                    val timestampNs = frame.timestamp
                    if (timestampNs > 0L && timestampNs != lastFrameTimestampNs) {
                        updateIndex += 1
                        val camera = frame.camera
                        if ((updateIndex % frameRecordEveryNUpdates.coerceAtLeast(1).toLong()) != 0L) {
                            lastFrameTimestampNs = timestampNs
                            return@runCatching
                        }
                        if (saveOnlyWhenTracking && camera.trackingState != TrackingState.TRACKING) {
                            lastFrameTimestampNs = timestampNs
                            return@runCatching
                        }
                        val savedImage =
                            try {
                                frame.acquireCameraImage().useImage { image ->
                                    saveFrameRecordImage(
                                        image = image,
                                        outputDir = imageOutputDir,
                                        timestampNs = timestampNs,
                                    )
                                }
                            } catch (_: NotYetAvailableException) {
                                lastFrameTimestampNs = timestampNs
                                return@runCatching
                            } catch (_: Exception) {
                                lastFrameTimestampNs = timestampNs
                                return@runCatching
                            }
                        val pose = camera.pose
                        val imageIntrinsicsResult = runCatching { camera.imageIntrinsics }
                        val textureIntrinsicsResult = runCatching { camera.textureIntrinsics }
                        val imageIntrinsics = imageIntrinsicsResult.getOrNull()
                        val textureIntrinsics = textureIntrinsicsResult.getOrNull()
                        onPose(
                            OffscreenArCorePoseFrame(
                                updateIndex = updateIndex,
                                frameTimestampNs = timestampNs,
                                captureTimestampNs = runCatching { frame.androidCameraTimestamp }.getOrDefault(timestampNs),
                                trackingState = camera.trackingState.name,
                                trackingFailureReason = runCatching { camera.trackingFailureReason.name }.getOrNull(),
                                translation = pose.translation,
                                rotationQuaternion = pose.rotationQuaternion,
                                imageFocalLength = imageIntrinsics?.focalLength?.toList() ?: emptyList(),
                                imagePrincipalPoint = imageIntrinsics?.principalPoint?.toList() ?: emptyList(),
                                imageDimensions = imageIntrinsics?.imageDimensions?.toList() ?: emptyList(),
                                textureFocalLength = textureIntrinsics?.focalLength?.toList() ?: emptyList(),
                                texturePrincipalPoint = textureIntrinsics?.principalPoint?.toList() ?: emptyList(),
                                textureDimensions = textureIntrinsics?.imageDimensions?.toList() ?: emptyList(),
                                imageIntrinsicsRequested = true,
                                imageIntrinsicsSucceeded = imageIntrinsics != null,
                                imageIntrinsicsFailureReason = imageIntrinsicsResult.exceptionOrNull()?.javaClass?.simpleName,
                                textureIntrinsicsRequested = true,
                                textureIntrinsicsSucceeded = textureIntrinsics != null,
                                textureIntrinsicsFailureReason = textureIntrinsicsResult.exceptionOrNull()?.javaClass?.simpleName,
                                imageFileName = savedImage.fileName,
                            ),
                        )
                        lastFrameTimestampNs = timestampNs
                    }
                }
            }
            handler.postDelayed(this, sampleIntervalMs.coerceAtLeast(33L))
        }
    }

    fun start(session: Session) {
        if (running) {
            return
        }
        running = true
        this.session = session
        handler.post {
            if (!running) {
                return@post
            }
            initializeGl(session)
            updateIndex = 0L
            handler.post(samplingRunnable)
        }
    }

    fun stop() {
        running = false
        handler.removeCallbacks(samplingRunnable)
        handler.post {
            releaseGl()
            session = null
            lastFrameTimestampNs = -1L
            updateIndex = 0L
        }
    }

    private fun initializeGl(session: Session) {
        eglDisplay = EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY)
        check(eglDisplay != EGL14.EGL_NO_DISPLAY) { "Unable to acquire EGL display for ARCore pose sampling." }
        val eglVersion = IntArray(2)
        check(EGL14.eglInitialize(eglDisplay, eglVersion, 0, eglVersion, 1)) {
            "Unable to initialize EGL for ARCore pose sampling."
        }

        val config = chooseConfig()
        eglContext = EGL14.eglCreateContext(
            eglDisplay,
            config,
            EGL14.EGL_NO_CONTEXT,
            intArrayOf(EGL14.EGL_CONTEXT_CLIENT_VERSION, 2, EGL14.EGL_NONE),
            0,
        )
        check(eglContext != EGL14.EGL_NO_CONTEXT) { "Unable to create EGL context for ARCore pose sampling." }

        eglSurface = EGL14.eglCreatePbufferSurface(
            eglDisplay,
            config,
            intArrayOf(EGL14.EGL_WIDTH, 1, EGL14.EGL_HEIGHT, 1, EGL14.EGL_NONE),
            0,
        )
        check(eglSurface != EGL14.EGL_NO_SURFACE) { "Unable to create EGL surface for ARCore pose sampling." }
        makeCurrent()

        val textureIds = IntArray(1)
        GLES20.glGenTextures(1, textureIds, 0)
        cameraTextureId = textureIds[0]
        GLES20.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, cameraTextureId)
        GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR)
        GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR)
        session.setCameraTextureNames(intArrayOf(cameraTextureId))
    }

    private fun chooseConfig(): EGLConfig {
        val configs = arrayOfNulls<EGLConfig>(1)
        val configCount = IntArray(1)
        val attributes = intArrayOf(
            EGL14.EGL_RENDERABLE_TYPE, EGL14.EGL_OPENGL_ES2_BIT,
            EGL14.EGL_SURFACE_TYPE, EGL14.EGL_PBUFFER_BIT,
            EGL14.EGL_RED_SIZE, 8,
            EGL14.EGL_GREEN_SIZE, 8,
            EGL14.EGL_BLUE_SIZE, 8,
            EGL14.EGL_ALPHA_SIZE, 8,
            EGL14.EGL_NONE,
        )
        check(EGL14.eglChooseConfig(eglDisplay, attributes, 0, configs, 0, configs.size, configCount, 0)) {
            "Unable to choose EGL config for ARCore pose sampling."
        }
        return checkNotNull(configs[0]) { "No EGL config available for ARCore pose sampling." }
    }

    private fun makeCurrent() {
        check(EGL14.eglMakeCurrent(eglDisplay, eglSurface, eglSurface, eglContext)) {
            "Unable to make EGL context current for ARCore pose sampling."
        }
    }

    private fun releaseGl() {
        if (cameraTextureId != 0) {
            GLES20.glDeleteTextures(1, intArrayOf(cameraTextureId), 0)
            cameraTextureId = 0
        }
        if (eglDisplay != EGL14.EGL_NO_DISPLAY) {
            EGL14.eglMakeCurrent(
                eglDisplay,
                EGL14.EGL_NO_SURFACE,
                EGL14.EGL_NO_SURFACE,
                EGL14.EGL_NO_CONTEXT,
            )
        }
        if (eglSurface != EGL14.EGL_NO_SURFACE) {
            EGL14.eglDestroySurface(eglDisplay, eglSurface)
            eglSurface = EGL14.EGL_NO_SURFACE
        }
        if (eglContext != EGL14.EGL_NO_CONTEXT) {
            EGL14.eglDestroyContext(eglDisplay, eglContext)
            eglContext = EGL14.EGL_NO_CONTEXT
        }
        if (eglDisplay != EGL14.EGL_NO_DISPLAY) {
            EGL14.eglTerminate(eglDisplay)
            eglDisplay = EGL14.EGL_NO_DISPLAY
        }
    }
}
