package com.reviework.app

enum class ReviewPhase {
    INTAKE,
    DIAGNOSE,
    RUN,
    VERIFY,
    REVIEW,
}

enum class PipelineState {
    EMPTY,
    READY,
    RUNNING,
    OK,
    PENDING,
    BLOCKED,
}

enum class WorkerVisibility {
    SUFFICIENT,
    PARTIAL,
    INSUFFICIENT,
}

enum class RelinkMode {
    OBSERVED,
    RELINKED,
    BRIDGED,
    LOST,
}

data class PipelineStatus(
    val preprocess: PipelineState = PipelineState.EMPTY,
    val colmap: PipelineState = PipelineState.EMPTY,
    val gs3d: PipelineState = PipelineState.EMPTY,
    val trajectory: PipelineState = PipelineState.EMPTY,
)

data class DataHealth(
    val frames: Int = 0,
    val usable: Int? = null,
    val tracking: String? = null,
    val workerVisibility: String? = null,
    val workerImuDevices: Int? = null,
)

data class QualityStatus(
    val space: String? = null,
    val trajectory: String? = null,
    val coordinateSystem: String? = null,
    val workerPathCount: Int? = null,
)

data class AttentionPoint(
    val timeRange: String,
    val reason: String,
)

data class TimelineHighlight(
    val timeRange: String,
    val description: String,
)

data class SessionIntakeReport(
    val frames: Int,
    val usableFrames: Int,
    val tracking: String,
    val mainVideoReady: Boolean,
    val mainImuReady: Boolean,
    val workerImuDeviceCount: Int,
    val workerVisibility: WorkerVisibility,
    val optionalPoseReady: Boolean,
    val optionalGnssReady: Boolean,
)

data class SpaceReviewSummary(
    val coordinateSystem: String,
    val mainCameraPathReady: Boolean,
    val colmapReadyForDensification: Boolean,
    val spaceQuality: String,
    val weakArea: String? = null,
)

data class RelinkDecision(
    val workerId: String,
    val visualMatchConfidence: Double,
    val timeGapSeconds: Int,
    val anchorProximityMeters: Double,
    val mode: RelinkMode,
)

data class TrajectoryReviewSummary(
    val workerPathCount: Int,
    val trajectoryQuality: String,
    val relinkDecisions: List<RelinkDecision>,
    val attentionPoints: List<AttentionPoint>,
    val sameTimeHighlights: List<TimelineHighlight>,
)

data class ReviewArtifactSummary(
    val generatedBy: String,
    val viewerMode: String,
    val supports3dgsControls: Boolean,
    val supportsSameTimeHighlights: Boolean,
)

data class ReviewContractSnapshot(
    val intake: SessionIntakeReport,
    val space: SpaceReviewSummary,
    val trajectory: TrajectoryReviewSummary,
    val artifact: ReviewArtifactSummary,
)

data class ReviewThinStatus(
    val phase: ReviewPhase,
    val pipeline: PipelineStatus = PipelineStatus(),
    val dataHealth: DataHealth = DataHealth(),
    val quality: QualityStatus = QualityStatus(),
    val issues: List<ReviewIssue> = emptyList(),
    val activeStepLabel: String? = null,
)

data class ReviewScreenState(
    val nextActionTitle: String,
    val nextActionReason: String,
    val thinStatus: ReviewThinStatus,
    val attentionPoints: List<AttentionPoint> = emptyList(),
    val sameTimeHighlights: List<TimelineHighlight> = emptyList(),
)
