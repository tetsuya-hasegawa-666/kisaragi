package com.isensorium.app

enum class RecordingIssueSeverity {
    INFO,
    WARNING,
    ERROR,
}

data class RecordingIssue(
    val severity: RecordingIssueSeverity,
    val message: String,
    val suggestedAction: String,
)
