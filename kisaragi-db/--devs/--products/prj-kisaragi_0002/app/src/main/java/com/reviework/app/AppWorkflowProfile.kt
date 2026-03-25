package com.reviework.app

enum class AppWorkflowMode {
    CORRECTING,
    MODELING,
    REVIEWING,
    INTEGRATED,
}

data class AppWorkflowProfile(
    val mode: AppWorkflowMode,
    val roleLabel: String,
    val scopeSummary: String,
    val coveredPhases: String,
    val showExtractionCard: Boolean,
)

fun appWorkflowProfileFromBuildConfig(): AppWorkflowProfile {
    val mode =
        when (BuildConfig.APP_MODE.lowercase()) {
            "correcting" -> AppWorkflowMode.CORRECTING
            "modeling" -> AppWorkflowMode.MODELING
            "reviewing" -> AppWorkflowMode.REVIEWING
            else -> AppWorkflowMode.INTEGRATED
        }

    return when (mode) {
        AppWorkflowMode.CORRECTING ->
            AppWorkflowProfile(
                mode = mode,
                roleLabel = BuildConfig.APP_ROLE_LABEL,
                scopeSummary = BuildConfig.APP_SCOPE_SUMMARY,
                coveredPhases = "input_packaging / diagnose / correction",
                showExtractionCard = true,
            )
        AppWorkflowMode.MODELING ->
            AppWorkflowProfile(
                mode = mode,
                roleLabel = BuildConfig.APP_ROLE_LABEL,
                scopeSummary = BuildConfig.APP_SCOPE_SUMMARY,
                coveredPhases = "space_reconstruction / trajectory_reconstruction",
                showExtractionCard = false,
            )
        AppWorkflowMode.REVIEWING ->
            AppWorkflowProfile(
                mode = mode,
                roleLabel = BuildConfig.APP_ROLE_LABEL,
                scopeSummary = BuildConfig.APP_SCOPE_SUMMARY,
                coveredPhases = "verify / review / same_time_highlight",
                showExtractionCard = false,
            )
        AppWorkflowMode.INTEGRATED ->
            AppWorkflowProfile(
                mode = mode,
                roleLabel = BuildConfig.APP_ROLE_LABEL,
                scopeSummary = BuildConfig.APP_SCOPE_SUMMARY,
                coveredPhases = "correcting / modeling / reviewing",
                showExtractionCard = true,
            )
    }
}
