package com.isensorium.app

import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Test

class FrameRecordOrientationPolicyTest {

    @Test
    fun normalizeImageIntrinsicsRotatesClockwise90() {
        val normalized =
            FrameRecordOrientationPolicy.normalizeImageIntrinsics(
                focalLength = listOf(1200f, 900f),
                principalPoint = listOf(640f, 360f),
                dimensions = listOf(1280, 720),
            )

        requireNotNull(normalized)
        assertEquals(listOf(900f, 1200f), normalized.focalLength)
        assertEquals(listOf(359f, 640f), normalized.principalPoint)
        assertEquals(listOf(720, 1280), normalized.dimensions)
    }

    @Test
    fun rotateNv21Clockwise90RotatesLumaAndChroma() {
        val source =
            byteArrayOf(
                0, 1,
                2, 3,
                4, 5,
                6, 7,
                8, 9,
                10, 11,
            )

        val rotated = FrameRecordOrientationPolicy.rotateNv21Clockwise90(source, width = 2, height = 4)

        assertArrayEquals(
            byteArrayOf(
                6, 4, 2, 0,
                7, 5, 3, 1,
                10, 11, 8, 9,
            ),
            rotated,
        )
    }
}
