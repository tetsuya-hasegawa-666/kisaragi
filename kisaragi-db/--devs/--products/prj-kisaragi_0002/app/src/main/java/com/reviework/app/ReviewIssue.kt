package com.reviework.app

enum class ReviewIssueSeverity {
    INFO,
    WARNING,
    ERROR,
}

data class ReviewIssue(
    val severity: ReviewIssueSeverity,
    val code: String,
    val message: String,
    val suggestedAction: String,
)
