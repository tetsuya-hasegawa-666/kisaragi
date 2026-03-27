package com.isensorium.app;

import org.json.JSONObject;
import org.junit.Assert;
import org.junit.Test;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;

public class CorrectingDataCheckServiceSmokeTest {

    @Test
    public void runProducesDerivedArtifactsAndCorrections() throws Exception {
        File root = Files.createTempDirectory("correcting-smoke").toFile();
        Files.write(
            new File(root, "session_manifest.json").toPath(),
            """
            {
              "sessionId": "session-20260326-193000",
              "status": "finalized",
              "deviceModel": "SO-53B",
              "timebase": {
                "sessionStartWallTimeMs": 1000,
                "sessionStartElapsedRealtimeNanos": 2000
              },
              "collectorStatus": {
                "imu": "recording",
                "ble": "disabled",
                "arcore": "disabled"
              },
              "recordingConfig": {
                "recordingMode": "STANDARD_HANDHELD"
              }
            }
            """.trim().getBytes(StandardCharsets.UTF_8)
        );
        Files.write(new File(root, "video.mp4").toPath(), new byte[] {1, 2, 3});
        Files.write(
            new File(root, "video_frame_timestamps.csv").toPath(),
            (
                "camera_sensor_timestamp_ns,elapsed_realtime_ns,wall_time_ms,rotation_degrees,session_elapsed_ns\n" +
                "11,2100,1010,0,100\n" +
                "12,2200,1020,0,200\n"
            ).getBytes(StandardCharsets.UTF_8)
        );
        Files.write(
            new File(root, "imu.csv").toPath(),
            (
                "elapsed_realtime_ns,timestamp_ns,ax\n" +
                "2100,2100,0.1\n" +
                "2200,2200,0.2\n"
            ).getBytes(StandardCharsets.UTF_8)
        );
        Files.write(
            new File(root, "arcore_pose.jsonl").toPath(),
            (
                "{\"sessionId\":\"session-20260326-193000\",\"recordIndex\":1,\"frameTimestampNs\":11,\"captureTimestampNs\":11,\"elapsedRealtimeNanos\":2105,\"trackingState\":\"TRACKING\",\"pose\":{\"tx\":0.1,\"ty\":0.2,\"tz\":0.3,\"qx\":0.0,\"qy\":0.0,\"qz\":0.0,\"qw\":1.0},\"imageIntrinsics\":{\"fx\":1000.0,\"fy\":1001.0,\"cx\":500.0,\"cy\":501.0,\"width\":1920,\"height\":1080},\"textureIntrinsics\":{\"fx\":998.0,\"fy\":999.0,\"cx\":500.0,\"cy\":500.0,\"width\":1920,\"height\":1080},\"lensDistortion\":{\"coefficients\":[0.1,0.01,0.0,0.0,0.0],\"model\":\"android_lens_distortion\"}}\n"
            ).getBytes(StandardCharsets.UTF_8)
        );

        CorrectingDataCheckResult result = new CorrectingDataCheckService().run(root);

        Assert.assertFalse(result.getReadyForDiagnose());
        Assert.assertTrue(result.getRecommendedCorrections().stream().anyMatch(it -> it.contains("BLE")));
        Assert.assertTrue(new File(root, "trajectreview/sensor_quality.json").exists());
        Assert.assertTrue(new File(root, "trajectreview/camera_calibration_summary.json").exists());
        Assert.assertEquals(1, result.getCalibrationFrameCount());

        JSONObject quality = new JSONObject(new String(Files.readAllBytes(new File(root, "trajectreview/sensor_quality.json").toPath()), StandardCharsets.UTF_8));
        Assert.assertEquals("session-20260326-193000", quality.getString("sessionId"));
        Assert.assertTrue(quality.getJSONObject("scores").getDouble("imageIntrinsicsCoverageRatio") > 0.0);
        Assert.assertTrue(quality.has("timeAlignmentDeltaMs"));

        JSONObject calibration = new JSONObject(new String(Files.readAllBytes(new File(root, "trajectreview/camera_calibration_summary.json").toPath()), StandardCharsets.UTF_8));
        Assert.assertEquals("session_fixed", calibration.getString("intrinsicsModeCandidate"));
        Assert.assertTrue(calibration.getJSONArray("recommendedModelingRoutes").length() >= 1);
    }
}
