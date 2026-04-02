package com.isensorium.app

import android.graphics.ImageFormat
import android.graphics.Rect
import android.graphics.YuvImage
import android.media.Image
import android.os.Handler
import android.os.HandlerThread
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.FileOutputStream
import java.util.ArrayDeque

data class SavedFrameImage(
    val fileName: String,
    val width: Int,
    val height: Int,
    val rawWidth: Int,
    val rawHeight: Int,
    val rotationClockwiseDegrees: Int,
)

data class FrameImagePlanePayload(
    val bytes: ByteArray,
    val rowStride: Int,
    val pixelStride: Int,
)

data class FrameImagePayload(
    val width: Int,
    val height: Int,
    val format: Int,
    val planes: List<FrameImagePlanePayload>,
)

interface FrameImageSnapshotter {
    fun snapshot(image: Image): FrameImagePayload
}

interface FrameImagePersister {
    fun persist(
        payload: FrameImagePayload,
        outputDir: File,
        timestampNs: Long,
    ): SavedFrameImage
}

object Yuv420FrameImageSnapshotter : FrameImageSnapshotter {
    override fun snapshot(image: Image): FrameImagePayload {
        require(image.format == ImageFormat.YUV_420_888) {
            "Expected YUV_420_888 image but was ${image.format}"
        }
        val planes =
            image.planes.map { plane ->
                val buffer = plane.buffer.duplicate()
                val bytes = ByteArray(buffer.remaining())
                buffer.get(bytes)
                FrameImagePlanePayload(
                    bytes = bytes,
                    rowStride = plane.rowStride,
                    pixelStride = plane.pixelStride,
                )
            }
        return FrameImagePayload(
            width = image.width,
            height = image.height,
            format = image.format,
            planes = planes,
        )
    }
}

object JpegFrameImagePersister : FrameImagePersister {
    override fun persist(
        payload: FrameImagePayload,
        outputDir: File,
        timestampNs: Long,
    ): SavedFrameImage {
        require(payload.format == ImageFormat.YUV_420_888) {
            "Expected YUV_420_888 payload but was ${payload.format}"
        }
        outputDir.mkdirs()
        val fileName = "frame_${timestampNs}.jpg"
        val outputFile = File(outputDir, fileName)
        val geometry = FrameRecordOrientationPolicy.normalizedGeometry(payload.width, payload.height)
        val normalizedNv21 = FrameRecordOrientationPolicy.rotateNv21Clockwise90(payload.toNv21(), payload.width, payload.height)
        val yuvImage =
            YuvImage(
                normalizedNv21,
                ImageFormat.NV21,
                geometry.normalizedWidth,
                geometry.normalizedHeight,
                null,
            )
        val jpegBytes =
            ByteArrayOutputStream(normalizedNv21.size).use { output ->
                check(
                    yuvImage.compressToJpeg(
                        Rect(0, 0, geometry.normalizedWidth, geometry.normalizedHeight),
                        JPEG_QUALITY,
                        output,
                    ),
                ) {
                    "Failed to encode frame image as JPEG."
                }
                output.toByteArray()
            }
        FileOutputStream(outputFile).use { output -> output.write(jpegBytes) }
        return SavedFrameImage(
            fileName = fileName,
            width = geometry.normalizedWidth,
            height = geometry.normalizedHeight,
            rawWidth = geometry.rawWidth,
            rawHeight = geometry.rawHeight,
            rotationClockwiseDegrees = geometry.rotationClockwiseDegrees,
        )
    }

    private fun FrameImagePayload.toNv21(): ByteArray {
        val ySize = width * height
        val uvSize = ySize / 2
        val output = ByteArray(ySize + uvSize)
        val yPlane = planes.getOrNull(0) ?: error("Y plane is missing.")
        val uPlane = planes.getOrNull(1) ?: error("U plane is missing.")
        val vPlane = planes.getOrNull(2) ?: error("V plane is missing.")
        copyPlane(yPlane, width, height, output, 0, 1)
        copyPlane(vPlane, width / 2, height / 2, output, ySize, 2)
        copyPlane(uPlane, width / 2, height / 2, output, ySize + 1, 2)
        return output
    }

    private fun copyPlane(
        plane: FrameImagePlanePayload,
        width: Int,
        height: Int,
        output: ByteArray,
        outputOffset: Int,
        outputPixelStride: Int,
    ) {
        var outputIndex = outputOffset
        for (row in 0 until height) {
            val rowOffset = row * plane.rowStride
            for (col in 0 until width) {
                output[outputIndex] = plane.bytes[rowOffset + col * plane.pixelStride]
                outputIndex += outputPixelStride
            }
        }
    }

    private const val JPEG_QUALITY = 60
}

class FrameRecordImageSaveQueue(
    private val outputDir: File,
    queueName: String,
    private val persister: FrameImagePersister = JpegFrameImagePersister,
) {
    private val workerThread = HandlerThread(queueName)
    private val queueLock = Object()
    private var workerHandler: Handler? = null
    private val pendingJobs = ArrayDeque<PendingFrameImageSave>()
    private var draining = false

    fun start() {
        if (!workerThread.isAlive) {
            workerThread.start()
            workerHandler = Handler(workerThread.looper)
        }
    }

    fun stop() {
        val deadlineMs = System.currentTimeMillis() + STOP_WAIT_TIMEOUT_MS
        synchronized(queueLock) {
            while (draining || pendingJobs.isNotEmpty()) {
                val remainingMs = deadlineMs - System.currentTimeMillis()
                if (remainingMs <= 0L) {
                    break
                }
                queueLock.wait(remainingMs.coerceAtMost(100L))
            }
        }
        if (workerThread.isAlive) {
            workerThread.quitSafely()
        }
        workerHandler = null
    }

    fun enqueue(
        payload: FrameImagePayload,
        timestampNs: Long,
        onSaved: (SavedFrameImage) -> Unit,
    ): Boolean {
        val handler = workerHandler ?: return false
        synchronized(queueLock) {
            if (pendingJobs.size >= MAX_PENDING_JOBS) {
                return false
            }
            pendingJobs.addLast(PendingFrameImageSave(payload, timestampNs, onSaved))
            if (!draining) {
                draining = true
                handler.post(::drainNext)
            }
        }
        return true
    }

    private fun drainNext() {
        val job =
            synchronized(queueLock) {
                if (pendingJobs.isEmpty()) {
                    draining = false
                    queueLock.notifyAll()
                    null
                } else {
                    pendingJobs.removeFirst()
                }
            }
                ?: return
        val saved = persister.persist(job.payload, outputDir, job.timestampNs)
        job.onSaved(saved)
        synchronized(queueLock) {
            if (pendingJobs.isEmpty()) {
                draining = false
                queueLock.notifyAll()
            } else {
                workerHandler?.post(::drainNext)
            }
        }
    }

    private data class PendingFrameImageSave(
        val payload: FrameImagePayload,
        val timestampNs: Long,
        val onSaved: (SavedFrameImage) -> Unit,
    )

    private companion object {
        const val MAX_PENDING_JOBS = 8
        const val STOP_WAIT_TIMEOUT_MS = 5_000L
    }
}

fun captureFrameImagePayload(
    image: Image,
    snapshotter: FrameImageSnapshotter = Yuv420FrameImageSnapshotter,
): FrameImagePayload = snapshotter.snapshot(image)

fun saveFrameRecordImage(
    image: Image,
    outputDir: File,
    timestampNs: Long,
    snapshotter: FrameImageSnapshotter = Yuv420FrameImageSnapshotter,
    persister: FrameImagePersister = JpegFrameImagePersister,
): SavedFrameImage {
    val payload = snapshotter.snapshot(image)
    return persister.persist(payload, outputDir, timestampNs)
}

inline fun <T> Image.useImage(block: (Image) -> T): T =
    try {
        block(this)
    } finally {
        close()
    }
