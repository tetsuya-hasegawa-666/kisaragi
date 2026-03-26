package com.reviework.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ReviewScreenControllerTest {

    private val controller = ReviewScreenController()

    private fun snapshot(
        workerVisibility: WorkerVisibility = WorkerVisibility.SUFFICIENT,
        workerImuDeviceCount: Int = 2,
        colmapReady: Boolean = true,
        relinkMode: RelinkMode = RelinkMode.RELINKED,
        sameTimeHighlights: List<TimelineHighlight> = listOf(TimelineHighlight("00:45", "主カメラと worker-01 が接近")),
    ): ReviewContractSnapshot =
        ReviewContractSnapshot(
            intake =
                SessionIntakeReport(
                    frames = 1240,
                    usableFrames = 1092,
                    tracking = "partial",
                    mainVideoReady = true,
                    mainImuReady = true,
                    workerImuDeviceCount = workerImuDeviceCount,
                    workerVisibility = workerVisibility,
                    optionalPoseReady = true,
                    optionalGnssReady = false,
                ),
            space =
                SpaceReviewSummary(
                    coordinateSystem = "arcore_local",
                    mainCameraPathReady = true,
                    colmapReadyForDensification = colmapReady,
                    spaceQuality = "0.78",
                    weakArea = "主カメラ coverage が薄い",
                ),
            trajectory =
                TrajectoryReviewSummary(
                    workerPathCount = 2,
                    trajectoryQuality = "0.64",
                    relinkDecisions = listOf(RelinkDecision("worker-01", 0.42, 7, 2.4, relinkMode)),
                    attentionPoints = listOf(AttentionPoint("00:42-00:49", "worker-01 の visual relink confidence が閾値未満")),
                    sameTimeHighlights = sameTimeHighlights,
                ),
            artifact =
                ReviewArtifactSummary(
                    generatedBy = "Assembly",
                    viewerMode = "read-only",
                    supports3dgsControls = true,
                    supportsSameTimeHighlights = true,
                ),
        )

    @Test
    fun initialStateStartsFromIntake() {
        val state = controller.initialState()

        assertEquals(ReviewPhase.INTAKE, state.thinStatus.phase)
        assertEquals("入力セッションを選択", state.nextActionTitle)
    }

    @Test
    fun correctingModelingAndReviewingModesExposeDifferentWorkflowRanges() {
        val correcting = controller.statesForMode(AppWorkflowMode.CORRECTING)
        val modeling = controller.statesForMode(AppWorkflowMode.MODELING)
        val reviewing = controller.statesForMode(AppWorkflowMode.REVIEWING)

        assertEquals(listOf(ReviewPhase.INTAKE, ReviewPhase.DIAGNOSE, ReviewPhase.DIAGNOSE), correcting.map { it.thinStatus.phase })
        assertEquals(listOf(ReviewPhase.DIAGNOSE, ReviewPhase.RUN, ReviewPhase.VERIFY), modeling.map { it.thinStatus.phase })
        assertEquals(listOf(ReviewPhase.VERIFY, ReviewPhase.REVIEW), reviewing.map { it.thinStatus.phase })
    }

    @Test
    fun diagnoseStateReportsWorkerVisibilityShortage() {
        val state = controller.diagnoseState(snapshot(workerVisibility = WorkerVisibility.INSUFFICIENT))

        assertEquals(ReviewPhase.DIAGNOSE, state.thinStatus.phase)
        assertTrue(controller.formatThinStatus(state).contains("worker_visibility=insufficient"))
        assertTrue(controller.formatThinStatus(state).contains("worker_visibility_insufficient"))
    }

    @Test
    fun readyStateBlocksUntilWorkerInputIsReady() {
        val blocked = controller.readyState(snapshot(workerImuDeviceCount = 0))
        val ready = controller.readyState(snapshot())

        assertEquals("入力条件を見直す", blocked.nextActionTitle)
        assertEquals("処理を開始", ready.nextActionTitle)
    }

    @Test
    fun colmapBlockedStateStops3dgs() {
        val state = controller.colmapBlockedState(snapshot(colmapReady = false))
        val formatted = controller.formatThinStatus(state)

        assertEquals("入力条件を見直す", state.nextActionTitle)
        assertTrue(formatted.contains("colmap=blocked"))
        assertTrue(formatted.contains("3dgs=blocked"))
    }

    @Test
    fun verifyStateShowsQualityAndSameTimeHighlights() {
        val state = controller.verifyState(snapshot())
        val formatted = controller.formatThinStatus(state)

        assertEquals(ReviewPhase.VERIFY, state.thinStatus.phase)
        assertTrue(formatted.contains("quality: space=0.78 trajectory=0.64"))
        assertTrue(formatted.contains("coordinate_system=arcore_local"))
        assertTrue(formatted.contains("worker_paths=2"))
        assertTrue(formatted.contains("same_time_highlights: 1"))
    }

    @Test
    fun reviewStateEmitsAttentionPointsAndSameTimeHighlights() {
        val state = controller.reviewState(snapshot())
        val formatted = controller.formatAttentionPoints(state)

        assertEquals(ReviewPhase.REVIEW, state.thinStatus.phase)
        assertTrue(formatted.contains("visual relink confidence"))
        assertTrue(formatted.contains("same_time:"))
        assertTrue(formatted.contains("主カメラと worker-01 が接近"))
    }

    @Test
    fun verifyStateFlagsRelinkUncertaintyWhenObservedIsNotMaintained() {
        val state = controller.verifyState(snapshot(relinkMode = RelinkMode.BRIDGED))

        assertTrue(controller.formatThinStatus(state).contains("relink_insufficient"))
    }

    @Test
    fun artifactBoundarySummaryStatesAssemblyOwnership() {
        val summary = controller.artifactBoundarySummary(snapshot())

        assertTrue(summary.contains("generated_by=Assembly"))
        assertTrue(summary.contains("viewer_mode=read-only"))
        assertTrue(summary.contains("same_time_highlights=true"))
    }
}
