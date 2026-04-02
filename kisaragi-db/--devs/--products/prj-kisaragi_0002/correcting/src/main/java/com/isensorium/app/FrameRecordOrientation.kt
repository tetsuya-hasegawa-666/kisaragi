package com.isensorium.app

data class NormalizedFrameImageGeometry(
    val rawWidth: Int,
    val rawHeight: Int,
    val normalizedWidth: Int,
    val normalizedHeight: Int,
    val rotationClockwiseDegrees: Int,
)

data class NormalizedFrameIntrinsics(
    val focalLength: List<Float>,
    val principalPoint: List<Float>,
    val dimensions: List<Int>,
)

object FrameRecordOrientationPolicy {
    const val POLICY_ID = "rotate_right_90_upright"
    const val ROTATION_CLOCKWISE_DEGREES = 90

    fun normalizedGeometry(rawWidth: Int, rawHeight: Int): NormalizedFrameImageGeometry {
        require(rawWidth > 0) { "rawWidth must be positive." }
        require(rawHeight > 0) { "rawHeight must be positive." }
        return NormalizedFrameImageGeometry(
            rawWidth = rawWidth,
            rawHeight = rawHeight,
            normalizedWidth = rawHeight,
            normalizedHeight = rawWidth,
            rotationClockwiseDegrees = ROTATION_CLOCKWISE_DEGREES,
        )
    }

    fun normalizeImageIntrinsics(
        focalLength: List<Float>,
        principalPoint: List<Float>,
        dimensions: List<Int>,
    ): NormalizedFrameIntrinsics? {
        if (focalLength.size < 2 || principalPoint.size < 2 || dimensions.size < 2) {
            return null
        }
        val geometry = normalizedGeometry(dimensions[0], dimensions[1])
        val fx = focalLength[0]
        val fy = focalLength[1]
        val cx = principalPoint[0]
        val cy = principalPoint[1]
        return NormalizedFrameIntrinsics(
            focalLength = listOf(fy, fx),
            principalPoint = listOf((geometry.rawHeight - 1).toFloat() - cy, cx),
            dimensions = listOf(geometry.normalizedWidth, geometry.normalizedHeight),
        )
    }

    fun rotateNv21Clockwise90(
        source: ByteArray,
        width: Int,
        height: Int,
    ): ByteArray {
        require(width > 0) { "width must be positive." }
        require(height > 0) { "height must be positive." }
        val frameSize = width * height
        require(source.size >= frameSize * 3 / 2) {
            "NV21 payload is smaller than expected for ${width}x${height}."
        }
        val rotated = ByteArray(frameSize * 3 / 2)
        var outputIndex = 0
        for (x in 0 until width) {
            for (y in height - 1 downTo 0) {
                rotated[outputIndex++] = source[y * width + x]
            }
        }
        var chromaIndex = frameSize
        for (x in 0 until width step 2) {
            for (y in height / 2 - 1 downTo 0) {
                val offset = frameSize + y * width + x
                rotated[chromaIndex++] = source[offset]
                rotated[chromaIndex++] = source[offset + 1]
            }
        }
        return rotated
    }
}
