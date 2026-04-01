package com.isensorium.app

import android.graphics.Bitmap
import android.media.Image
import java.io.File
import java.io.FileOutputStream

data class SavedFrameImage(
    val fileName: String,
    val width: Int,
    val height: Int,
)

fun saveFrameRecordImage(
    image: Image,
    outputDir: File,
    timestampNs: Long,
): SavedFrameImage {
    outputDir.mkdirs()
    val fileName = "frame_${timestampNs}.jpg"
    val outputFile = File(outputDir, fileName)
    val bitmap = yuv420888ToBitmap(image) ?: error("frame image を bitmap へ変換できません。")
    FileOutputStream(outputFile).use { output ->
        bitmap.compress(Bitmap.CompressFormat.JPEG, 90, output)
    }
    bitmap.recycle()
    return SavedFrameImage(
        fileName = fileName,
        width = image.width,
        height = image.height,
    )
}

fun yuv420888ToBitmap(image: Image): Bitmap? {
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
            val y = yBuffer.get(yRowOffset + col * yPixelStride).toInt() and 0xFF
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
            col += 1
        }
        row += 1
    }
    return Bitmap.createBitmap(out, width, height, Bitmap.Config.ARGB_8888)
}

inline fun <T> Image.useImage(block: (Image) -> T): T =
    try {
        block(this)
    } finally {
        close()
    }
