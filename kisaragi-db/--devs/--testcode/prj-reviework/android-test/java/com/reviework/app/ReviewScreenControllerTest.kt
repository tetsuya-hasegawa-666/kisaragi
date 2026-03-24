package com.reviework.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ReviewScreenControllerTest {

    private val controller = ReviewScreenController()

    @Test
    fun initialStateStartsFromIntake() {
        val state = controller.initialState()

        assertEquals(ReviewPhase.INTAKE, state.thinStatus.phase)
        assertEquals("データフォルダを選択", state.nextActionTitle)
    }

    @Test
    fun runningStateUsesWaitActionAndCurrentStep() {
        val state = controller.stateAt(3)

        assertEquals("完了を待つ", state.nextActionTitle)
        assertTrue(controller.formatThinStatus(state).contains("current_step: COLMAP / feature matching 42%"))
    }

    @Test
    fun reviewStateEmitsAttentionPoints() {
        val state = controller.stateAt(controller.lastIndex())

        assertEquals(ReviewPhase.REVIEW, state.thinStatus.phase)
        assertTrue(controller.formatAttentionPoints(state).contains("visual relink confidence"))
    }
}
