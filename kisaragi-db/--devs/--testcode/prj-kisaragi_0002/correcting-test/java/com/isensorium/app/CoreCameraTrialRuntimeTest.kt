package com.isensorium.app

import org.junit.Assert.assertEquals
import org.junit.Test

class CoreCameraTrialRuntimeTest {

    @Test
    fun lifecycleMachineTransitionsThroughHappyPath() {
        val machine = TrialSharedCameraLifecycleMachine()

        machine.markPreviewReady()
        machine.beginStart()
        machine.markRunning()
        machine.beginStop()
        machine.markStopped()

        assertEquals(TrialSharedCameraLifecycleState.STOPPED, machine.state)
    }

    @Test
    fun lifecycleMachineCanRecoverFromFailureToPreviewReady() {
        val machine = TrialSharedCameraLifecycleMachine()

        machine.markPreviewReady()
        machine.beginStart()
        machine.fail()
        machine.markPreviewReady()

        assertEquals(TrialSharedCameraLifecycleState.PREVIEW_READY, machine.state)
    }
}
