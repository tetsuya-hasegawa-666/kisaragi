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
)

data class QualityStatus(
    val space: String? = null,
    val trajectory: String? = null,
)

data class AttentionPoint(
    val timeRange: String,
    val reason: String,
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
)
