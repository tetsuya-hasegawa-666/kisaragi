# correcting script source inventory

この文書は `correcting_script_manifest.json` を正として、`correcting` の local product script / source inventory を示す。

- 目的は、`HAUB` の correct 用一覧表から local product 側の実体へ迷わず降りることである。
- `correcting` 側は最適化前でも現状のまま記載し、後段で責務再編する時は manifest と同時に更新する。
- 詳細列は `role`、`key data names`、`reference directories`、`main outputs / handoff` を固定し、`modeling` 側の inventory 思想と揃える。

## Source Inventory

| token | source_file | kind | heading | role | key functions / classes | key data names | reference directories | main outputs / handoff | docs_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CR-01 | `src/main/java/com/isensorium/app/MainActivity.kt` | `kotlin` | correcting UI orchestration | recording、data-check、保存先同期、転送、session 一覧を 1 画面で束ねる | MainActivity, buildSummaryText, renderButtons, refreshState, refreshSummaries | currentSession, latestDataCheckResult, selectedTransferGroupsState, transferDestinationDocumentUri, frameRecordEveryNUpdatesState, saveOnlyWhenTrackingState | correcting/src/main/res/layout, session_root, trajectreview/, Google Drive destination | record start/stop UI, data-check trigger, zip transfer trigger, stored session selection | `DOC-R01-01` |
| CR-02 | `src/main/java/com/isensorium/app/MainScreenController.kt` | `kotlin` | correcting form normalization | recording form を config へ正規化し、issue と status 文言を返す | MainScreenFormState, SessionPresentation, RecordingConfigResolution, MainScreenController, buildRecordingConfig, resolveRecordingConfig, buildModeSummary, buildPermissionDeniedIssue, buildRouteChangeBlockedIssue, buildRefreshIssue, buildPreviewStartIssue, buildSessionStartIssue, buildRefreshExecutionIssue, buildSessionPresentation, buildInitialStatus, buildRefreshStatus, buildRouteSwitchToast | MainScreenFormState, RecordingConfigResolution, SessionPresentation, RecordingConfig | correcting/src/main/res/values, MainActivity state | RecordingConfig, RecordingIssue, status summary | `DOC-R02-01` |
| CR-03 | `src/main/java/com/isensorium/app/RecordingCoordinator.kt` | `kotlin` | correcting session lifecycle | preview、recording、collector、session manifest 書込、flush/close を束ねる | RecordingCoordinator, SessionUiState, RecordingSession, RecordingConfig, SessionTimebase, FrameTimestamp, VideoEvent, BleEvent, ArCorePoseSample, SessionManager, isRecording, updateRecordingConfig, findLatestSession, startPreview, startSession, stopSession, shutdown, onHostResume, onHostPause, start, stop, setRotationDegrees, onFrame, onResume, onPause, listOutputFiles, activeStreamSummary, createSession, writeInitialManifest, finalizeManifest, flushSessionOutputs, closeSessionOutputs, appendCollectorStatus, appendFrameTimestamp, writeFrameRecordDiagnostics, appendVideoEvent, appendBleEvent, appendArCorePose, flush, close, openFor | RecordingSession, RecordingConfig, SessionManager, frame_record.jsonl, session_manifest.json, video.mp4, imu.csv, gnss.csv, ble_scan.jsonl, video_frame_timestamps.csv, video_events.jsonl | session_root, trajectreview/image, trajectreview/ | session files, frame_record.jsonl, trajectreview/image, session_manifest.json | `DOC-R03-01` |
| CR-04 | `src/main/java/com/isensorium/app/CoreCameraTrialRuntime.kt` | `kotlin` | core camera trial runtime | shared-camera trial、video encoder、offscreen ARCore pose sampler の runtime を持つ | TrialSharedCameraLifecycleState, TrialSharedCameraLifecycleMachine, TrialCpuImageVideoRecorder, OffscreenArCorePoseFrame, FrameRecordSamplerDiagnostics, OffscreenArCorePoseSampler, markPreviewReady, beginStart, markRunning, beginStop, markStopped, fail, prepare, start, setPreviewListener, stopAndRelease, release, requestSample, stop | TrialSharedCameraLifecycleMachine, TrialCpuImageVideoRecorder, OffscreenArCorePoseSampler, FrameRecordSamplerDiagnostics, OffscreenArCorePoseFrame | session_root, video output, ARCore session | video frame timestamps, sample diagnostics, preview callback, frame sampler result | `DOC-R04-01` |
| CR-05 | `src/main/java/com/isensorium/app/FrameRecordImageIo.kt` | `kotlin` | frame record image persistence | camera image snapshot、JPEG persist、save queue を分離する | SavedFrameImage, FrameImagePlanePayload, FrameImagePayload, FrameImageSnapshotter, FrameImagePersister, Yuv420FrameImageSnapshotter, JpegFrameImagePersister, FrameRecordImageSaveQueue, snapshot, persist, start, stop, enqueue, captureFrameImagePayload, saveFrameRecordImage | SavedFrameImage, FrameImagePayload, FrameImagePlanePayload, FrameRecordImageSaveQueue | trajectreview/image, session_root | upright JPEG, saved image metadata, save queue diagnostics | `DOC-R05-01` |
| CR-06 | `src/main/java/com/isensorium/app/FrameRecordOrientation.kt` | `kotlin` | frame orientation normalization | raw frame を upright 基準へそろえ、intrinsics と geometry を同時補正する | NormalizedFrameImageGeometry, NormalizedFrameIntrinsics, FrameRecordOrientationPolicy, normalizedGeometry, normalizeImageIntrinsics, rotateNv21Clockwise90 | NormalizedFrameImageGeometry, NormalizedFrameIntrinsics, FrameRecordOrientationPolicy, POLICY_ID, ROTATION_CLOCKWISE_DEGREES | frame_record.jsonl, trajectreview/image | upright geometry, normalized intrinsics, NV21 rotated payload | `DOC-R06-01` |
| CR-07 | `src/main/java/com/isensorium/app/CorrectingDataCheckService.kt` | `kotlin` | data-check and handoff artifact | session を読み、derived artifact と modeling handoff 契約を生成する | CorrectingDataCheckResult, CorrectingDataCheckService, run, exportImages, inspect, selectTransferImageFrameIndexes | CorrectingDataCheckResult, input_readiness.json, sensor_quality.json, frame_pose_index.csv, camera_calibration_summary.json, member_identity_map.json, session_package.json, space_handoff_manifest.json | session_root, trajectreview/, trajectreview/image | data-check result, derived artifact set, modeling-ready handoff manifest | `DOC-R07-01` |
| CR-08 | `src/main/java/com/isensorium/app/PcTransferService.kt` | `kotlin` | pc transfer packaging | PC target discovery、zip packaging、HTTP upload を行う | PcTransferResult, PcTransferTarget, PcTransferService, discoverTargets, transferCheckedSession | PcTransferTarget, PcTransferResult, DEFAULT_BOOTSTRAP_PORT, DEFAULT_TRANSFER_PORT | session_root, pc-transfer inbox, local subnet | session zip, uploaded session, selectable PC target list | `DOC-R08-01` |
| CR-09 | `src/main/java/com/isensorium/app/GuardedUpstreamTrial.kt` | `kotlin` | route gate contract | frozen route と shared-camera trial route の切替境界を固定する | CameraStackRoute, RouteResolution, SessionAdapterMetadata, GuardedUpstreamTrialContract, fromRouteId, resolve, buildSessionAdapterMetadata, sessionAdapterMetadataJson, sessionAdapterMetadataFromJson, guardedUpstreamTrialJson | CameraStackRoute, RouteResolution, SessionAdapterMetadata, preservedOperations, requiredArtifacts | session_manifest.json, frame_record.jsonl, trajectreview/image | route resolution, session adapter metadata, guarded trial JSON | `DOC-R09-01` |
| CR-10 | `src/main/java/com/isensorium/app/RecordingMode.kt` | `kotlin` | recording mode enum | handheld / pocket recording の mode 境界を固定する | RecordingMode, fromModeId | RecordingMode, STANDARD_HANDHELD, POCKET_RECORDING | MainScreenController, MainActivity | mode selection, modeId normalization | `DOC-R10-01` |
| CR-11 | `src/main/java/com/isensorium/app/RecordingIssue.kt` | `kotlin` | recording issue contract | UI に返す severity / message / suggestedAction を共通化する | RecordingIssueSeverity, RecordingIssue | RecordingIssueSeverity, RecordingIssue | MainScreenController, MainActivity | issue severity, user-facing issue payload | `DOC-R11-01` |
| CR-12 | `scripts/capture_preview_log.ps1` | `powershell` | preview log capture | preview logcat を短時間採取し、recording 前後の挙動を切り出す | - | DurationSeconds, adb, isensorium-preview, AndroidRuntime | adb logcat, preview runtime | terminal log output, preview diagnostic capture | `DOC-R12-01` |
| CR-13 | `scripts/pc-transfer-bootstrap.ps1` | `powershell` | pc transfer bootstrap responder | UDP bootstrap を受け、receiver 起動と READY 応答を返す | Test-SameSubnet24, Get-LocalIpv4Address, Start-ReceiverIfNeeded | BootstrapPort, TransferPort, IdleSeconds, TargetRoot | local subnet, pc-transfer inbox, receiver script | READY bootstrap reply, receiver process launch | `DOC-R13-01` |
| CR-14 | `scripts/pc-transfer-receiver.ps1` | `powershell` | pc transfer receiver | HTTP upload を受けて zip を保存し、session root へ展開する | Read-HttpRequest, Write-HttpJson, Expand-ZipToTarget | Port, TargetRoot, IdleSeconds, sessionId, zipPath | pc-transfer inbox, expanded session root | stored zip, expanded session directory, health response | `DOC-R14-01` |
| CR-15 | `scripts/run_short_session_harness.ps1` | `powershell` | short session harness | ADB で短時間 start/stop を繰り返し、session 生成を簡易確認する | Invoke-Adb | AdbPath, Runs, RecordSeconds, TapX, TapY, PackageName, ActivityName | adb shell, /sdcard/Android/data/.../sessions | short recording loop, recent sessions listing | `DOC-R15-01` |

## Function And Class Inventory

| name | token | heading | docs_id |
| --- | --- | --- | --- |
| MainActivity | CR-01 | correcting UI orchestration | `DOC-R01-01` |
| buildSummaryText | CR-01 | correcting UI orchestration | `DOC-R01-01` |
| renderButtons | CR-01 | correcting UI orchestration | `DOC-R01-01` |
| refreshState | CR-01 | correcting UI orchestration | `DOC-R01-01` |
| refreshSummaries | CR-01 | correcting UI orchestration | `DOC-R01-01` |
| MainScreenFormState | CR-02 | correcting form normalization | `DOC-R02-01` |
| SessionPresentation | CR-02 | correcting form normalization | `DOC-R02-01` |
| RecordingConfigResolution | CR-02 | correcting form normalization | `DOC-R02-01` |
| MainScreenController | CR-02 | correcting form normalization | `DOC-R02-01` |
| buildRecordingConfig | CR-02 | correcting form normalization | `DOC-R02-01` |
| resolveRecordingConfig | CR-02 | correcting form normalization | `DOC-R02-01` |
| buildModeSummary | CR-02 | correcting form normalization | `DOC-R02-01` |
| buildPermissionDeniedIssue | CR-02 | correcting form normalization | `DOC-R02-01` |
| buildRouteChangeBlockedIssue | CR-02 | correcting form normalization | `DOC-R02-01` |
| buildRefreshIssue | CR-02 | correcting form normalization | `DOC-R02-01` |
| buildPreviewStartIssue | CR-02 | correcting form normalization | `DOC-R02-01` |
| buildSessionStartIssue | CR-02 | correcting form normalization | `DOC-R02-01` |
| buildRefreshExecutionIssue | CR-02 | correcting form normalization | `DOC-R02-01` |
| buildSessionPresentation | CR-02 | correcting form normalization | `DOC-R02-01` |
| buildInitialStatus | CR-02 | correcting form normalization | `DOC-R02-01` |
| buildRefreshStatus | CR-02 | correcting form normalization | `DOC-R02-01` |
| buildRouteSwitchToast | CR-02 | correcting form normalization | `DOC-R02-01` |
| RecordingCoordinator | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| SessionUiState | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| RecordingSession | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| RecordingConfig | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| SessionTimebase | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| FrameTimestamp | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| VideoEvent | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| BleEvent | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| ArCorePoseSample | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| SessionManager | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| isRecording | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| updateRecordingConfig | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| findLatestSession | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| startPreview | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| startSession | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| stopSession | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| shutdown | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| onHostResume | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| onHostPause | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| start | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| stop | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| setRotationDegrees | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| onFrame | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| onResume | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| onPause | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| listOutputFiles | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| activeStreamSummary | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| createSession | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| writeInitialManifest | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| finalizeManifest | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| flushSessionOutputs | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| closeSessionOutputs | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| appendCollectorStatus | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| appendFrameTimestamp | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| writeFrameRecordDiagnostics | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| appendVideoEvent | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| appendBleEvent | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| appendArCorePose | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| flush | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| close | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| openFor | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| TrialSharedCameraLifecycleState | CR-04 | core camera trial runtime | `DOC-R04-01` |
| TrialSharedCameraLifecycleMachine | CR-04 | core camera trial runtime | `DOC-R04-01` |
| TrialCpuImageVideoRecorder | CR-04 | core camera trial runtime | `DOC-R04-01` |
| OffscreenArCorePoseFrame | CR-04 | core camera trial runtime | `DOC-R04-01` |
| FrameRecordSamplerDiagnostics | CR-04 | core camera trial runtime | `DOC-R04-01` |
| OffscreenArCorePoseSampler | CR-04 | core camera trial runtime | `DOC-R04-01` |
| markPreviewReady | CR-04 | core camera trial runtime | `DOC-R04-01` |
| beginStart | CR-04 | core camera trial runtime | `DOC-R04-01` |
| markRunning | CR-04 | core camera trial runtime | `DOC-R04-01` |
| beginStop | CR-04 | core camera trial runtime | `DOC-R04-01` |
| markStopped | CR-04 | core camera trial runtime | `DOC-R04-01` |
| fail | CR-04 | core camera trial runtime | `DOC-R04-01` |
| prepare | CR-04 | core camera trial runtime | `DOC-R04-01` |
| start | CR-04 | core camera trial runtime | `DOC-R04-01` |
| setPreviewListener | CR-04 | core camera trial runtime | `DOC-R04-01` |
| stopAndRelease | CR-04 | core camera trial runtime | `DOC-R04-01` |
| release | CR-04 | core camera trial runtime | `DOC-R04-01` |
| requestSample | CR-04 | core camera trial runtime | `DOC-R04-01` |
| stop | CR-04 | core camera trial runtime | `DOC-R04-01` |
| SavedFrameImage | CR-05 | frame record image persistence | `DOC-R05-01` |
| FrameImagePlanePayload | CR-05 | frame record image persistence | `DOC-R05-01` |
| FrameImagePayload | CR-05 | frame record image persistence | `DOC-R05-01` |
| FrameImageSnapshotter | CR-05 | frame record image persistence | `DOC-R05-01` |
| FrameImagePersister | CR-05 | frame record image persistence | `DOC-R05-01` |
| Yuv420FrameImageSnapshotter | CR-05 | frame record image persistence | `DOC-R05-01` |
| JpegFrameImagePersister | CR-05 | frame record image persistence | `DOC-R05-01` |
| FrameRecordImageSaveQueue | CR-05 | frame record image persistence | `DOC-R05-01` |
| snapshot | CR-05 | frame record image persistence | `DOC-R05-01` |
| persist | CR-05 | frame record image persistence | `DOC-R05-01` |
| start | CR-05 | frame record image persistence | `DOC-R05-01` |
| stop | CR-05 | frame record image persistence | `DOC-R05-01` |
| enqueue | CR-05 | frame record image persistence | `DOC-R05-01` |
| captureFrameImagePayload | CR-05 | frame record image persistence | `DOC-R05-01` |
| saveFrameRecordImage | CR-05 | frame record image persistence | `DOC-R05-01` |
| NormalizedFrameImageGeometry | CR-06 | frame orientation normalization | `DOC-R06-01` |
| NormalizedFrameIntrinsics | CR-06 | frame orientation normalization | `DOC-R06-01` |
| FrameRecordOrientationPolicy | CR-06 | frame orientation normalization | `DOC-R06-01` |
| normalizedGeometry | CR-06 | frame orientation normalization | `DOC-R06-01` |
| normalizeImageIntrinsics | CR-06 | frame orientation normalization | `DOC-R06-01` |
| rotateNv21Clockwise90 | CR-06 | frame orientation normalization | `DOC-R06-01` |
| CorrectingDataCheckResult | CR-07 | data-check and handoff artifact | `DOC-R07-01` |
| CorrectingDataCheckService | CR-07 | data-check and handoff artifact | `DOC-R07-01` |
| run | CR-07 | data-check and handoff artifact | `DOC-R07-01` |
| exportImages | CR-07 | data-check and handoff artifact | `DOC-R07-01` |
| inspect | CR-07 | data-check and handoff artifact | `DOC-R07-01` |
| selectTransferImageFrameIndexes | CR-07 | data-check and handoff artifact | `DOC-R07-01` |
| PcTransferResult | CR-08 | pc transfer packaging | `DOC-R08-01` |
| PcTransferTarget | CR-08 | pc transfer packaging | `DOC-R08-01` |
| PcTransferService | CR-08 | pc transfer packaging | `DOC-R08-01` |
| discoverTargets | CR-08 | pc transfer packaging | `DOC-R08-01` |
| transferCheckedSession | CR-08 | pc transfer packaging | `DOC-R08-01` |
| CameraStackRoute | CR-09 | route gate contract | `DOC-R09-01` |
| RouteResolution | CR-09 | route gate contract | `DOC-R09-01` |
| SessionAdapterMetadata | CR-09 | route gate contract | `DOC-R09-01` |
| GuardedUpstreamTrialContract | CR-09 | route gate contract | `DOC-R09-01` |
| fromRouteId | CR-09 | route gate contract | `DOC-R09-01` |
| resolve | CR-09 | route gate contract | `DOC-R09-01` |
| buildSessionAdapterMetadata | CR-09 | route gate contract | `DOC-R09-01` |
| sessionAdapterMetadataJson | CR-09 | route gate contract | `DOC-R09-01` |
| sessionAdapterMetadataFromJson | CR-09 | route gate contract | `DOC-R09-01` |
| guardedUpstreamTrialJson | CR-09 | route gate contract | `DOC-R09-01` |
| RecordingMode | CR-10 | recording mode enum | `DOC-R10-01` |
| fromModeId | CR-10 | recording mode enum | `DOC-R10-01` |
| RecordingIssueSeverity | CR-11 | recording issue contract | `DOC-R11-01` |
| RecordingIssue | CR-11 | recording issue contract | `DOC-R11-01` |
| Test-SameSubnet24 | CR-13 | pc transfer bootstrap responder | `DOC-R13-01` |
| Get-LocalIpv4Address | CR-13 | pc transfer bootstrap responder | `DOC-R13-01` |
| Start-ReceiverIfNeeded | CR-13 | pc transfer bootstrap responder | `DOC-R13-01` |
| Read-HttpRequest | CR-14 | pc transfer receiver | `DOC-R14-01` |
| Write-HttpJson | CR-14 | pc transfer receiver | `DOC-R14-01` |
| Expand-ZipToTarget | CR-14 | pc transfer receiver | `DOC-R14-01` |
| Invoke-Adb | CR-15 | short session harness | `DOC-R15-01` |

## Variable Inventory

| name | token | heading | docs_id |
| --- | --- | --- | --- |
| currentSession | CR-01 | correcting UI orchestration | `DOC-R01-01` |
| latestDataCheckResult | CR-01 | correcting UI orchestration | `DOC-R01-01` |
| selectedTransferGroupsState | CR-01 | correcting UI orchestration | `DOC-R01-01` |
| transferDestinationDocumentUri | CR-01 | correcting UI orchestration | `DOC-R01-01` |
| frameRecordEveryNUpdatesState | CR-01 | correcting UI orchestration | `DOC-R01-01` |
| saveOnlyWhenTrackingState | CR-01 | correcting UI orchestration | `DOC-R01-01` |
| MainScreenFormState | CR-02 | correcting form normalization | `DOC-R02-01` |
| RecordingConfigResolution | CR-02 | correcting form normalization | `DOC-R02-01` |
| SessionPresentation | CR-02 | correcting form normalization | `DOC-R02-01` |
| RecordingConfig | CR-02 | correcting form normalization | `DOC-R02-01` |
| RecordingSession | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| RecordingConfig | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| SessionManager | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| frame_record.jsonl | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| session_manifest.json | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| video.mp4 | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| imu.csv | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| gnss.csv | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| ble_scan.jsonl | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| video_frame_timestamps.csv | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| video_events.jsonl | CR-03 | correcting session lifecycle | `DOC-R03-01` |
| TrialSharedCameraLifecycleMachine | CR-04 | core camera trial runtime | `DOC-R04-01` |
| TrialCpuImageVideoRecorder | CR-04 | core camera trial runtime | `DOC-R04-01` |
| OffscreenArCorePoseSampler | CR-04 | core camera trial runtime | `DOC-R04-01` |
| FrameRecordSamplerDiagnostics | CR-04 | core camera trial runtime | `DOC-R04-01` |
| OffscreenArCorePoseFrame | CR-04 | core camera trial runtime | `DOC-R04-01` |
| SavedFrameImage | CR-05 | frame record image persistence | `DOC-R05-01` |
| FrameImagePayload | CR-05 | frame record image persistence | `DOC-R05-01` |
| FrameImagePlanePayload | CR-05 | frame record image persistence | `DOC-R05-01` |
| FrameRecordImageSaveQueue | CR-05 | frame record image persistence | `DOC-R05-01` |
| NormalizedFrameImageGeometry | CR-06 | frame orientation normalization | `DOC-R06-01` |
| NormalizedFrameIntrinsics | CR-06 | frame orientation normalization | `DOC-R06-01` |
| FrameRecordOrientationPolicy | CR-06 | frame orientation normalization | `DOC-R06-01` |
| POLICY_ID | CR-06 | frame orientation normalization | `DOC-R06-01` |
| ROTATION_CLOCKWISE_DEGREES | CR-06 | frame orientation normalization | `DOC-R06-01` |
| CorrectingDataCheckResult | CR-07 | data-check and handoff artifact | `DOC-R07-01` |
| input_readiness.json | CR-07 | data-check and handoff artifact | `DOC-R07-01` |
| sensor_quality.json | CR-07 | data-check and handoff artifact | `DOC-R07-01` |
| frame_pose_index.csv | CR-07 | data-check and handoff artifact | `DOC-R07-01` |
| camera_calibration_summary.json | CR-07 | data-check and handoff artifact | `DOC-R07-01` |
| member_identity_map.json | CR-07 | data-check and handoff artifact | `DOC-R07-01` |
| session_package.json | CR-07 | data-check and handoff artifact | `DOC-R07-01` |
| space_handoff_manifest.json | CR-07 | data-check and handoff artifact | `DOC-R07-01` |
| PcTransferTarget | CR-08 | pc transfer packaging | `DOC-R08-01` |
| PcTransferResult | CR-08 | pc transfer packaging | `DOC-R08-01` |
| DEFAULT_BOOTSTRAP_PORT | CR-08 | pc transfer packaging | `DOC-R08-01` |
| DEFAULT_TRANSFER_PORT | CR-08 | pc transfer packaging | `DOC-R08-01` |
| CameraStackRoute | CR-09 | route gate contract | `DOC-R09-01` |
| RouteResolution | CR-09 | route gate contract | `DOC-R09-01` |
| SessionAdapterMetadata | CR-09 | route gate contract | `DOC-R09-01` |
| preservedOperations | CR-09 | route gate contract | `DOC-R09-01` |
| requiredArtifacts | CR-09 | route gate contract | `DOC-R09-01` |
| RecordingMode | CR-10 | recording mode enum | `DOC-R10-01` |
| STANDARD_HANDHELD | CR-10 | recording mode enum | `DOC-R10-01` |
| POCKET_RECORDING | CR-10 | recording mode enum | `DOC-R10-01` |
| RecordingIssueSeverity | CR-11 | recording issue contract | `DOC-R11-01` |
| RecordingIssue | CR-11 | recording issue contract | `DOC-R11-01` |
| DurationSeconds | CR-12 | preview log capture | `DOC-R12-01` |
| adb | CR-12 | preview log capture | `DOC-R12-01` |
| isensorium-preview | CR-12 | preview log capture | `DOC-R12-01` |
| AndroidRuntime | CR-12 | preview log capture | `DOC-R12-01` |
| BootstrapPort | CR-13 | pc transfer bootstrap responder | `DOC-R13-01` |
| TransferPort | CR-13 | pc transfer bootstrap responder | `DOC-R13-01` |
| IdleSeconds | CR-13 | pc transfer bootstrap responder | `DOC-R13-01` |
| TargetRoot | CR-13 | pc transfer bootstrap responder | `DOC-R13-01` |
| Port | CR-14 | pc transfer receiver | `DOC-R14-01` |
| TargetRoot | CR-14 | pc transfer receiver | `DOC-R14-01` |
| IdleSeconds | CR-14 | pc transfer receiver | `DOC-R14-01` |
| sessionId | CR-14 | pc transfer receiver | `DOC-R14-01` |
| zipPath | CR-14 | pc transfer receiver | `DOC-R14-01` |
| AdbPath | CR-15 | short session harness | `DOC-R15-01` |
| Runs | CR-15 | short session harness | `DOC-R15-01` |
| RecordSeconds | CR-15 | short session harness | `DOC-R15-01` |
| TapX | CR-15 | short session harness | `DOC-R15-01` |
| TapY | CR-15 | short session harness | `DOC-R15-01` |
| PackageName | CR-15 | short session harness | `DOC-R15-01` |
| ActivityName | CR-15 | short session harness | `DOC-R15-01` |
