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
    private val frames = mutableListOf<VideoFrame>()
    private val frameLock = Any()
    private var previewListener: ((Bitmap, Long) -> Unit)? = null
    private var previewFrameIntervalNs: Long = 200_000_000L
    private var lastPreviewTimestampNs = Long.MIN_VALUE
    private var lastPreviewLogNs = Long.MIN_VALUE

    private var imageReader: ImageReader? = null
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
        synchronized(frameLock) {
            frames.clear()
        }
        startSensorTimestampNs = null
        lastAcceptedTimestampNs = Long.MIN_VALUE
        lastPreviewTimestampNs = Long.MIN_VALUE
        recording = false
    }

    fun start() {
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
        val capturedFrames = synchronized(frameLock) { frames.toList() }
        if (capturedFrames.isNotEmpty()) {
            encodeFrames(capturedFrames)
        }
        imageReader?.close()
        imageReader = null
        synchronized(frameLock) {
            frames.clear()
        }
        startSensorTimestampNs = null
        lastAcceptedTimestampNs = Long.MIN_VALUE
        return outputFile.length()
    }

    fun release() {
        recording = false
        imageReader?.close()
        imageReader = null
        synchronized(frameLock) {
            frames.clear()
        }
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
            synchronized(frameLock) {
                frames += VideoFrame(
                    presentationTimeUs = ((timestampNs - startTimestamp) / 1_000L).coerceAtLeast(0L),
                    data = frameBytes,
                )
            }
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

    private fun encodeFrames(capturedFrames: List<VideoFrame>) {
        val codec = MediaCodec.createEncoderByType(MediaFormat.MIMETYPE_VIDEO_AVC)
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
        val bufferInfo = MediaCodec.BufferInfo()
        val muxer = MediaMuxer(outputFile.absolutePath, MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4)
        var trackIndex = -1
        var muxerStarted = false

        try {
            codec.configure(format, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE)
            codec.start()

            for (frame in capturedFrames) {
                val inputIndex = codec.dequeueInputBuffer(TIMEOUT_US)
                if (inputIndex >= 0) {
                    codec.getInputBuffer(inputIndex)?.apply {
                        clear()
                        put(frame.data)
                    }
                    codec.queueInputBuffer(inputIndex, 0, frame.data.size, frame.presentationTimeUs, 0)
                }
                val drainState = drainCodec(codec, muxer, bufferInfo, trackIndex, muxerStarted)
                trackIndex = drainState.trackIndex
                muxerStarted = drainState.muxerStarted
            }

            val eosInputIndex = codec.dequeueInputBuffer(TIMEOUT_US)
            if (eosInputIndex >= 0) {
                codec.queueInputBuffer(
                    eosInputIndex,
                    0,
                    0,
                    capturedFrames.last().presentationTimeUs,
                    MediaCodec.BUFFER_FLAG_END_OF_STREAM,
                )
            }
            val drainState = drainCodec(codec, muxer, bufferInfo, trackIndex, muxerStarted, endOfStream = true)
            trackIndex = drainState.trackIndex
            muxerStarted = drainState.muxerStarted
        } finally {
            runCatching { codec.stop() }
            codec.release()
            if (muxerStarted && trackIndex >= 0) {
                runCatching { muxer.stop() }
            }
            muxer.release()
        }
    }

    private fun drainCodec(
        codec: MediaCodec,
        muxer: MediaMuxer,
        bufferInfo: MediaCodec.BufferInfo,
        initialTrackIndex: Int,
        initialMuxerStarted: Boolean,
        endOfStream: Boolean = false,
    ): DrainState {
        var trackIndex = initialTrackIndex
        var muxerStarted = initialMuxerStarted
        while (true) {
            val outputIndex = codec.dequeueOutputBuffer(bufferInfo, TIMEOUT_US)
            when {
                outputIndex == MediaCodec.INFO_TRY_AGAIN_LATER && !endOfStream -> return DrainState(trackIndex, muxerStarted)
                outputIndex == MediaCodec.INFO_TRY_AGAIN_LATER -> continue
                outputIndex == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED -> {
                    if (!muxerStarted) {
                        trackIndex = muxer.addTrack(codec.outputFormat)
                        muxer.start()
                        muxerStarted = true
                    }
                }
                outputIndex >= 0 -> {
                    val outputBuffer = codec.getOutputBuffer(outputIndex) ?: break
                    if (bufferInfo.size > 0 && muxerStarted && trackIndex >= 0) {
                        outputBuffer.position(bufferInfo.offset)
                        outputBuffer.limit(bufferInfo.offset + bufferInfo.size)
                        muxer.writeSampleData(trackIndex, outputBuffer, bufferInfo)
                    }
                    codec.releaseOutputBuffer(outputIndex, false)
                    if ((bufferInfo.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM) != 0) {
                        return DrainState(trackIndex, muxerStarted)
                    }
                }
            }
        }
        return DrainState(trackIndex, muxerStarted)
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

    private data class VideoFrame(
        val presentationTimeUs: Long,
        val data: ByteArray,
    )

    private data class DrainState(
        val trackIndex: Int,
        val muxerStarted: Boolean,
    )

    private companion object {
        const val TIMEOUT_US = 10_000L
    }
}

class OffscreenArCorePoseSampler(
    private val handler: Handler,
    private val onPose: (Long, String, FloatArray, FloatArray) -> Unit,
) {
    private var session: Session? = null
    private var running = false
    private var lastFrameTimestampNs = -1L

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
                        val camera = frame.camera
                        val pose = camera.pose
                        onPose(
                            timestampNs,
                            camera.trackingState.name,
                            pose.translation,
                            pose.rotationQuaternion,
                        )
                        lastFrameTimestampNs = timestampNs
                    }
                }
            }
            handler.postDelayed(this, SAMPLE_INTERVAL_MS)
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

    private companion object {
        const val SAMPLE_INTERVAL_MS = 33L
    }
}
