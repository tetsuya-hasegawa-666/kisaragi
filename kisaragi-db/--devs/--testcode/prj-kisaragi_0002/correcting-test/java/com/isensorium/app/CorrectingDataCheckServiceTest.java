package com.isensorium.app;

import org.json.JSONObject;
import org.junit.Assert;
import org.junit.Test;

import java.io.File;
import java.nio.file.Files;

public class CorrectingDataCheckServiceTest {

    @Test
    public void runWritesDerivedOutputsAndMarksReadyWhenRequiredInputsExist() throws Exception {
        File sessionDir = createSessionDir(true, true);

        CorrectingDataCheckResult result = new CorrectingDataCheckService().run(sessionDir);

        Assert.assertTrue(result.getReadyForDiagnose());
        Assert.assertTrue(result.getReadyForSpaceReconstruction());
        Assert.assertTrue(new File(sessionDir, "trajectreview/session_package.json").exists());
        Assert.assertTrue(new File(sessionDir, "trajectreview/sensor_quality.json").exists());
        Assert.assertTrue(new File(sessionDir, "trajectreview/space_handoff_manifest.json").exists());

        JSONObject handoff = new JSONObject(Files.readString(new File(sessionDir, "trajectreview/space_handoff_manifest.json").toPath()));
        Assert.assertTrue(handoff.getBoolean("readyForSpaceReconstruction"));
    }

    @Test
    public void runReportsBlockersAndRecommendedCorrectionsWhenBtOrPoseIsWeak() throws Exception {
        File sessionDir = createSessionDir(false, false);

        CorrectingDataCheckResult result = new CorrectingDataCheckService().run(sessionDir);

        Assert.assertFalse(result.getReadyForDiagnose());
        Assert.assertFalse(result.getReadyForSpaceReconstruction());
        Assert.assertTrue(result.getMissingRequiredInputs().contains("bt"));
        Assert.assertTrue(result.getRecommendedCorrections().stream().anyMatch(it -> it.contains("BLE")));
        Assert.assertTrue(result.getRecommendedCorrections().stream().anyMatch(it -> it.contains("ARCore pose coverage")));
        Assert.assertEquals("session-20260326-120000", result.getSessionId());
    }

    private File createSessionDir(boolean includeBt, boolean includePose) throws Exception {
        File root = Files.createTempDirectory("correcting-data-check").toFile();
        Files.writeString(
            new File(root, "session_manifest.json").toPath(),
            """
            {
              "sessionId": "session-20260326-120000",
              "status": "finalized",
              "deviceModel": "SO-53B",
              "timebase": {
                "sessionStartWallTimeMs": 1000,
                "sessionStartElapsedRealtimeNanos": 2000
              },
              "collectorStatus": {
                "imu": "recording",
                "ble": "%s",
                "arcore": "%s"
              },
              "recordingConfig": {
                "recordingMode": "STANDARD_HANDHELD"
              }
            }
            """.formatted(includeBt ? "recording" : "disabled", includePose ? "recording" : "disabled").trim()
        );
        Files.write(new File(root, "video.mp4").toPath(), new byte[] {1, 2, 3});
        Files.writeString(
            new File(root, "video_frame_timestamps.csv").toPath(),
            "camera_sensor_timestamp_ns,elapsed_realtime_ns,wall_time_ms,rotation_degrees,session_elapsed_ns\n" +
                "11,2100,1010,0,100\n" +
                "12,2200,1020,0,200\n"
        );
        Files.writeString(
            new File(root, "imu.csv").toPath(),
            "elapsed_realtime_ns,timestamp_ns,ax\n" +
                "2100,2100,0.1\n" +
                "2200,2200,0.2\n"
        );
        Files.writeString(
            new File(root, "gnss.csv").toPath(),
            "elapsed_realtime_ns,timestamp_ns,lat\n" +
                "2100,2100,35.0\n"
        );
        Files.writeString(new File(root, "video_events.jsonl").toPath(), "{\"type\":\"recording_finalize\"}\n");
        if (includeBt) {
            Files.writeString(
                new File(root, "ble_scan.jsonl").toPath(),
                "{\"elapsedRealtimeNanos\":2100,\"address\":\"AA:BB\",\"deviceId\":\"worker-01\"}\n" +
                    "{\"elapsedRealtimeNanos\":2200,\"address\":\"AA:BB\",\"deviceId\":\"worker-01\"}\n"
            );
        }
        if (includePose) {
            Files.writeString(
                new File(root, "arcore_pose.jsonl").toPath(),
                "{\"elapsedRealtimeNanos\":2100,\"trackingState\":\"TRACKING\",\"translation\":[0,0,0],\"rotationQuaternion\":[0,0,0,1]}\n" +
                    "{\"elapsedRealtimeNanos\":2200,\"trackingState\":\"TRACKING\",\"translation\":[0,0,0],\"rotationQuaternion\":[0,0,0,1]}\n"
            );
        }
        return root;
    }
}
