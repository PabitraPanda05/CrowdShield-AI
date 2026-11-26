import {
  Camera,
  Activity,
  Eye,
  Gauge,
  MonitorPlay,
  Users,
  Video,
  Clock3,
  CheckCircle2,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

function format(value, digits = 1) {
  if (
    value === null ||
    value === undefined ||
    Number.isNaN(Number(value))
  ) {
    return "—";
  }

  return Number(value).toFixed(digits);
}

function StatCard({ icon, label, value, suffix = "" }) {
  return (
    <div className="cs-module-stat">
      <div className="cs-module-stat-icon">
        {icon}
      </div>

      <div>
        <span>{label}</span>

        <strong>
          {value}
          {suffix && <small>{suffix}</small>}
        </strong>
      </div>
    </div>
  );
}

function InfoRow({ label, value }) {
  return (
    <div className="cs-module-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}


function flowUnitVector(direction) {
  const vectors = {
    EAST: [1, 0],
    WEST: [-1, 0],
    NORTH: [0, -1],
    SOUTH: [0, 1],
    NORTH_EAST: [Math.SQRT1_2, -Math.SQRT1_2],
    NORTH_WEST: [-Math.SQRT1_2, -Math.SQRT1_2],
    SOUTH_EAST: [Math.SQRT1_2, Math.SQRT1_2],
    SOUTH_WEST: [-Math.SQRT1_2, Math.SQRT1_2],
  };

  return vectors[direction] || null;
}

function CrowdOverlay({ frame, camera }) {
  const previousCenters = useRef(new Map());
  const frameWidth = Number(
    frame?.frame_width || camera?.width || 1280
  );
  const frameHeight = Number(
    frame?.frame_height || camera?.height || 720
  );

  const tracks = Array.isArray(frame?.tracks) ? frame.tracks : [];
  const metrics = frame?.crowd || {};
  const zones = Array.isArray(metrics.potential_bottleneck_zones)
    ? metrics.potential_bottleneck_zones
    : [];
  const dominantVector = flowUnitVector(
    metrics.dominant_flow_direction
  );

  // Frame-based density estimate: count tracked person centres in each 4x4 cell.
  // This is a visual occupancy estimate, not people per square metre.
  const densityGridSize = 4;
  const densityCounts = Array.from(
    { length: densityGridSize * densityGridSize },
    () => 0
  );

  tracks.forEach((track) => {
    const cx = Number(
      track.center_x ?? (Number(track.x1) + Number(track.x2)) / 2
    );
    const cy = Number(
      track.center_y ?? (Number(track.y1) + Number(track.y2)) / 2
    );

    if (!Number.isFinite(cx) || !Number.isFinite(cy)) return;

    const col = Math.max(
      0,
      Math.min(densityGridSize - 1, Math.floor((cx / frameWidth) * densityGridSize))
    );
    const row = Math.max(
      0,
      Math.min(densityGridSize - 1, Math.floor((cy / frameHeight) * densityGridSize))
    );
    densityCounts[row * densityGridSize + col] += 1;
  });

  const maxCellDensity = Math.max(1, ...densityCounts);
  const densityCells = densityCounts
    .map((count, index) => ({
      count,
      row: Math.floor(index / densityGridSize),
      col: index % densityGridSize,
    }))
    .filter((cell) => cell.count > 0);

  const movement = tracks.map((track) => {
    const id = String(track.track_id ?? "");
    const centerX = Number(
      track.center_x ?? (Number(track.x1) + Number(track.x2)) / 2
    );
    const centerY = Number(
      track.center_y ?? (Number(track.y1) + Number(track.y2)) / 2
    );

    const previous = previousCenters.current.get(id);
    let dx = 0;
    let dy = 0;
    let reverse = false;

    if (previous) {
      dx = centerX - previous.x;
      dy = centerY - previous.y;

      if (dominantVector && Math.hypot(dx, dy) > 2) {
        const dot = dx * dominantVector[0] + dy * dominantVector[1];
        reverse = dot < 0;
      }
    }

    return { id, centerX, centerY, dx, dy, reverse };
  });

  useEffect(() => {
    const next = new Map();

    tracks.forEach((track) => {
      const id = String(track.track_id ?? "");
      if (!id) return;

      const x = Number(
        track.center_x ?? (Number(track.x1) + Number(track.x2)) / 2
      );
      const y = Number(
        track.center_y ?? (Number(track.y1) + Number(track.y2)) / 2
      );

      if (Number.isFinite(x) && Number.isFinite(y)) {
        next.set(id, { x, y });
      }
    });

    previousCenters.current = next;
  }, [frame?.frame_number, tracks]);

  if (!frame || !tracks.length || frameWidth <= 0 || frameHeight <= 0) {
    return null;
  }

  return (
    <svg
      className="cs-crowd-overlay"
      viewBox={`0 0 ${frameWidth} ${frameHeight}`}
      preserveAspectRatio="xMidYMid meet"
      aria-label="Crowd detection and tracking overlay"
    >
      {/* Live flow summary: direction is the backend's crowd-level estimate. */}
      <g className="cs-flow-summary">
        <rect x="14" y="14" width="270" height="72" rx="9" className="cs-flow-summary-bg" />
        <text x="28" y="42" className="cs-flow-summary-title">
          CROWD FLOW
        </text>
        <text x="28" y="68" className="cs-flow-summary-value">
          {String(metrics.dominant_flow_direction || "UNKNOWN").replaceAll("_", " ")}
        </text>
        <text x="270" y="42" textAnchor="end" className="cs-flow-summary-count">
          {Number(metrics.moving_tracks || 0)} MOVING
        </text>
        <text x="270" y="68" textAnchor="end" className="cs-flow-summary-count cs-flow-summary-reverse">
          {Number(metrics.reverse_flow_count || 0)} REVERSE
        </text>
      </g>

      {/* 4 × 4 tracked-person density heatmap. Stronger cells contain more tracks. */}
      <g className="cs-density-heatmap" pointerEvents="none">
        {densityCells.map((cell) => {
          const intensity = cell.count / maxCellDensity;
          const fill =
            intensity >= 0.75
              ? "rgba(239, 68, 68, 0.38)"
              : intensity >= 0.4
                ? "rgba(249, 115, 22, 0.32)"
                : "rgba(250, 204, 21, 0.22)";
          const cellWidth = frameWidth / densityGridSize;
          const cellHeight = frameHeight / densityGridSize;
          const x = cell.col * cellWidth;
          const y = cell.row * cellHeight;

          return (
            <g key={`density-${cell.row}-${cell.col}`}>
              <rect
                x={x}
                y={y}
                width={cellWidth}
                height={cellHeight}
                fill={fill}
                className="cs-density-cell"
              />
              <text
                x={x + cellWidth - 12}
                y={y + 24}
                textAnchor="end"
                className="cs-density-count"
              >
                {cell.count}
              </text>
            </g>
          );
        })}
      </g>

      {/* 4 × 4 analysis grid */}
      {Array.from({ length: 3 }, (_, index) => (
        <g key={`grid-${index}`}>
          <line
            x1={(frameWidth / 4) * (index + 1)}
            y1="0"
            x2={(frameWidth / 4) * (index + 1)}
            y2={frameHeight}
            className="cs-overlay-grid-line"
          />
          <line
            x1="0"
            y1={(frameHeight / 4) * (index + 1)}
            x2={frameWidth}
            y2={(frameHeight / 4) * (index + 1)}
            className="cs-overlay-grid-line"
          />
        </g>
      ))}

      {/* Bottleneck regions use the normalized region from the AI pipeline. */}
      {zones.map((zone, index) => {
        const region = zone.region || {};
        const x = Number(region.x_start) * frameWidth;
        const y = Number(region.y_start) * frameHeight;
        const width =
          (Number(region.x_end) - Number(region.x_start)) * frameWidth;
        const height =
          (Number(region.y_end) - Number(region.y_start)) * frameHeight;

        if (![x, y, width, height].every(Number.isFinite)) return null;

        return (
          <g key={`bottleneck-${index}`}>
            <rect
              x={x}
              y={y}
              width={width}
              height={height}
              className="cs-overlay-bottleneck"
            />
            <text x={x + 8} y={y + 22} className="cs-overlay-zone-label">
              BOTTLENECK · {zone.person_count ?? "—"} PEOPLE
            </text>
          </g>
        );
      })}

      {/* Track boxes, IDs and short motion vectors. */}
      {tracks.map((track, index) => {
        const x1 = Number(track.x1);
        const y1 = Number(track.y1);
        const x2 = Number(track.x2);
        const y2 = Number(track.y2);
        if (![x1, y1, x2, y2].every(Number.isFinite)) return null;

        const boxWidth = Math.max(0, x2 - x1);
        const boxHeight = Math.max(0, y2 - y1);
        const motion = movement[index];
        const arrowLength = Math.hypot(motion.dx, motion.dy);
        const showArrow = arrowLength > 1.5;
        const arrowScale = showArrow
          ? Math.min(1, 58 / arrowLength)
          : 0;
        const arrowX = motion.centerX + motion.dx * arrowScale;
        const arrowY = motion.centerY + motion.dy * arrowScale;

        return (
          <g key={`track-${track.track_id ?? index}`}>
            <rect
              x={x1}
              y={y1}
              width={boxWidth}
              height={boxHeight}
              className={
                motion.reverse
                  ? "cs-overlay-box cs-overlay-box-reverse"
                  : "cs-overlay-box"
              }
            />
            <rect
              x={x1}
              y={Math.max(0, y1 - 27)}
              width="104"
              height="25"
              rx="4"
              className={
                motion.reverse
                  ? "cs-overlay-tag cs-overlay-tag-reverse"
                  : "cs-overlay-tag"
              }
            />
            <text
              x={x1 + 7}
              y={Math.max(17, y1 - 10)}
              className="cs-overlay-tag-text"
            >
              ID {track.track_id ?? "—"}
            </text>

            {showArrow && (
              <line
                x1={motion.centerX}
                y1={motion.centerY}
                x2={arrowX}
                y2={arrowY}
                className={
                  motion.reverse
                    ? "cs-overlay-arrow cs-overlay-arrow-reverse"
                    : "cs-overlay-arrow"
                }
                markerEnd={
                  motion.reverse
                    ? "url(#cs-arrow-reverse)"
                    : "url(#cs-arrow)"
                }
              />
            )}
          </g>
        );
      })}

      <g className="cs-overlay-legend" transform={`translate(14 ${frameHeight - 22})`}>
        <rect x="0" y="-25" width="390" height="34" rx="6" className="cs-overlay-legend-bg" />
        <line x1="12" y1="-8" x2="42" y2="-8" className="cs-overlay-arrow" markerEnd="url(#cs-arrow)" />
        <text x="51" y="-3" className="cs-overlay-legend-text">Flow</text>
        <line x1="112" y1="-8" x2="142" y2="-8" className="cs-overlay-arrow-reverse" markerEnd="url(#cs-arrow-reverse)" />
        <text x="151" y="-3" className="cs-overlay-legend-text">Reverse estimate</text>
        <rect x="264" y="-15" width="12" height="12" rx="2" fill="rgba(250, 204, 21, 0.8)" />
        <text x="282" y="-3" className="cs-overlay-legend-text">Density</text>
      </g>

      <defs>
        <marker
          id="cs-arrow"
          markerWidth="7"
          markerHeight="7"
          refX="5"
          refY="3"
          orient="auto"
        >
          <path d="M0,0 L6,3 L0,6" className="cs-overlay-arrow-head" />
        </marker>
        <marker
          id="cs-arrow-reverse"
          markerWidth="7"
          markerHeight="7"
          refX="5"
          refY="3"
          orient="auto"
        >
          <path d="M0,0 L6,3 L0,6" className="cs-overlay-arrow-head-reverse" />
        </marker>
      </defs>
    </svg>
  );
}

function HealthRow({ name, ok }) {
  return (
    <div className="cs-health-item">
      {ok ? (
        <CheckCircle2
          size={17}
          color="#2dd4bf"
        />
      ) : (
        <Activity
          size={17}
          color="#64748b"
        />
      )}

      <div>
        <strong>{name}</strong>

        <span>
          {ok ? "Available" : "Unavailable"}
        </span>
      </div>
    </div>
  );
}

function CameraIntelligence({
  cameras = [],
  crowd = null,
  selectedCameraId,
  setSelectedCameraId,
  cameraIntelligence = null,
}) {
  const [webcamFrameUrl, setWebcamFrameUrl] = useState("");
  const [liveFrameData, setLiveFrameData] = useState(null);

  /*
   * Keep the user's selected camera during API refreshes.
   *
   * If the API temporarily returns an empty camera list,
   * do not reset the current selection.
   *
   * If the selected camera still exists, keep it selected.
   *
   * Only choose a fallback camera when the current selection
   * no longer exists.
   */
  useEffect(() => {
    setSelectedCameraId((currentId) => {
      if (cameras.length === 0) {
        return currentId;
      }

      const currentCameraExists = cameras.some(
        (item) => item.camera_id === currentId
      );

      if (currentCameraExists) {
        return currentId;
      }

      const preferredCamera =
        cameras.find(
          (item) =>
            item.live_stream &&
            item.status === "RUNNING"
        ) ||
        cameras[0];

      return preferredCamera?.camera_id || null;
    });
  }, [cameras, setSelectedCameraId]);

  const selectedCamera =
  cameras.find(
    (item) => item.camera_id === selectedCameraId
  ) ||
  cameras[0] ||
  {};

const camera =
  cameraIntelligence?.camera_id === selectedCameraId
    ? {
        ...selectedCamera,
        ...cameraIntelligence,
      }
    : selectedCamera;

  /*
   * Display the exact latest frame processed by the AI worker for BOTH
   * webcam and RTSP cameras. This is important: an RTSP iframe is a
   * separate player with its own buffering/delay, so its video can be
   * out of sync with the track coordinates returned by /status.
   *
   * The /frame endpoint reuses the already-running camera worker; it
   * does not open another camera connection or run YOLO again.
   */
  useEffect(() => {
    const supportedLiveSource = ["webcam", "rtsp", "ip_camera"].includes(
      camera.source_type
    );

    if (!camera.camera_id || !camera.live_stream || !supportedLiveSource) {
      setWebcamFrameUrl("");
      return;
    }

    let cancelled = false;
    let requestInProgress = false;

    const updateFrame = async () => {
      if (requestInProgress || cancelled) return;
      requestInProgress = true;

      try {
        // The image endpoint returns the newest frame from the same
        // camera worker that supplies latest_frame.tracks to the overlay.
        const nextUrl =
          `http://127.0.0.1:8000/api/cameras/${camera.camera_id}/frame?t=${Date.now()}`;

        if (!cancelled) setWebcamFrameUrl(nextUrl);
      } finally {
        requestInProgress = false;
      }
    };

    updateFrame();
    const interval = window.setInterval(updateFrame, 250);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [camera.camera_id, camera.live_stream, camera.source_type]);

  const isLive = Boolean(camera.live_stream);
  // Prefer the freshly polled backend frame over the parent camera-list snapshot.
  const overlayFrame = liveFrameData || camera.latest_frame || null;

  /*
   * Poll the backend's existing camera worker for the newest processed frame.
   * The video/image preview and AI metadata are separate HTTP responses, so
   * refreshing only the preview URL would leave SVG boxes stuck on old tracks.
   */
  useEffect(() => {
    setLiveFrameData(null);

    if (
      !camera.camera_id ||
      !camera.live_stream ||
      !["webcam", "rtsp", "ip_camera"].includes(camera.source_type)
    ) {
      return;
    }

    let cancelled = false;
    let requestInProgress = false;

    const refreshLatestFrame = async () => {
      if (requestInProgress) return;
      requestInProgress = true;

      try {
        const response = await fetch(
          `http://127.0.0.1:8000/api/cameras/${camera.camera_id}/status?t=${Date.now()}`,
          { cache: "no-store" }
        );

        if (!response.ok) {
          throw new Error(`Camera status request failed: ${response.status}`);
        }

        const payload = await response.json();
        const cameraData = payload?.data || payload?.camera || payload;
        const latest = cameraData?.latest_frame;

        if (!cancelled && latest && typeof latest === "object") {
          setLiveFrameData(latest);
        }
      } catch (error) {
        // Keep the last good frame visible; transient polling errors are harmless.
        console.warn("CrowdShield overlay refresh:", error.message);
      } finally {
        requestInProgress = false;
      }
    };

    refreshLatestFrame();
    const timer = window.setInterval(refreshLatestFrame, 250);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [camera.camera_id, camera.live_stream, camera.source_type]);

  const status =
    camera.status ||
    (isLive ? "CONNECTING" : "RECORDED_REPLAY");

  const sourceLabel = isLive
    ? camera.source_type === "webcam"
      ? "LIVE WEBCAM"
      : camera.source_type === "rtsp"
        ? "LIVE RTSP"
        : "LIVE CAMERA"
    : "RECORDED";

  const currentPeople =
    camera.latest_person_count ??
    camera.latest_frame?.person_count ??
    crowd?.people_count ??
    crowd?.latest_people_count ??
    "—";

  // Crowd-intelligence metrics are returned inside latest_frame.crowd.
  // Keep fallbacks for parent-level data to remain compatible with
  // the existing dashboard data shape.
  const crowdMetrics =
    camera.latest_frame?.crowd ||
    camera.crowd ||
    crowd ||
    {};

  const dominantFlow =
    crowdMetrics.dominant_flow_direction || "UNKNOWN";

  const reverseFlowCount =
    crowdMetrics.reverse_flow_count ?? 0;

  const reverseFlowRatio =
    Number(crowdMetrics.reverse_flow_ratio ?? 0) * 100;

  const flowCoherence =
    Number(crowdMetrics.flow_coherence ?? 0) * 100;

  const bottleneckCount =
    crowdMetrics.potential_bottleneck_count ?? 0;

  const bottleneckZones = Array.isArray(
    crowdMetrics.potential_bottleneck_zones
  )
    ? crowdMetrics.potential_bottleneck_zones
    : [];

  const duration =
    camera.duration_sec ??
    "—";

  const frameCount =
    camera.frame_count ??
    "—";

  const fps =
    camera.fps ??
    "—";

  const width =
    camera.width ??
    "—";

  const height =
    camera.height ??
    "—";

  const sourceValue = isLive
    ? sourceLabel
    : camera.source_file || "people.mp4.mp4";

  const cameraSourceOk = isLive
    ? status === "RUNNING"
    : Boolean(camera.camera_id);

  const detectionOk =
    camera.latest_person_count !== null &&
    camera.latest_person_count !== undefined;

  const trackingOk =
    camera.latest_frame !== null &&
    camera.latest_frame !== undefined;

  const crowdIntelligenceOk =
    camera.latest_risk !== null &&
    camera.latest_risk !== undefined;

  return (
    <div className="cs-module-page">

      {/* HERO */}

      <div className="cs-module-hero">

        <div>

          <div className="cs-kicker">
            OPERATIONS / CAMERA INTELLIGENCE
          </div>

          <h2>Camera Intelligence</h2>

          <p>
            Production perception and live or recorded
            camera analysis from the centralized CrowdShield AI pipeline.
          </p>

        </div>

        <div className="cs-module-status">
          <Video size={16} />
          {status}
        </div>

      </div>


      {/* CAMERA SELECTOR */}

      <section className="cs-module-grid cs-module-grid-2">

        <div className="cs-panel">

          <div className="cs-panel-header">

            <div className="cs-panel-title">

              <div className="cs-panel-icon">
                <Camera size={17} />
              </div>

              <div>
                <h3>Available Cameras</h3>

                <p>
                  Select a registered perception source
                </p>
              </div>

            </div>

          </div>

          <div className="cs-panel-body">

            {cameras.length > 0 ? (
              <>

                <select
                  value={selectedCameraId || ""}
                  onChange={(event) =>
                    setSelectedCameraId(event.target.value)
                  }
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    borderRadius: "8px",
                    border:
                      "1px solid rgba(148, 163, 184, 0.25)",
                    background: "rgba(15, 23, 42, 0.8)",
                    color: "inherit",
                    fontSize: "14px",
                    outline: "none",
                    cursor: "pointer",
                    marginBottom: "14px",
                  }}
                >

                  {cameras.map((item) => (
                    <option
                      key={item.camera_id}
                      value={item.camera_id}
                    >
                      {item.camera_id} —{" "}
                      {item.camera_name || item.camera_id}

                      {item.live_stream
                        ? ` — ${item.status || "CONNECTING"}`
                        : " — RECORDED"}
                    </option>
                  ))}

                </select>


                <div className="cs-module-list">

                  {cameras.map((item) => (
                    <div
                      key={item.camera_id}
                      onClick={() =>
                        setSelectedCameraId(item.camera_id)
                      }
                      style={{
                        cursor: "pointer",
                        borderRadius: "8px",
                        outline:
                          item.camera_id === selectedCameraId
                            ? "1px solid rgba(45, 212, 191, 0.45)"
                            : "none",
                      }}
                    >

                      <InfoRow
                        label={item.camera_id}
                        value={
                          item.live_stream
                            ? `${item.camera_name || item.camera_id} — ${item.status || "CONNECTING"}`
                            : `${item.camera_name || item.camera_id} — RECORDED`
                        }
                      />

                    </div>
                  ))}

                </div>

              </>
            ) : (

              <div className="cs-module-list">

                <InfoRow
                  label="Camera"
                  value="No camera data"
                />

              </div>

            )}

          </div>

        </div>


        {/* CONNECTION STATUS */}

        <div className="cs-panel">

          <div className="cs-panel-header">

            <div className="cs-panel-title">

              <div className="cs-panel-icon">
                <Activity size={17} />
              </div>

              <div>

                <h3>Connection Status</h3>

                <p>
                  Current selected camera state
                </p>

              </div>

            </div>

            <span className="cs-panel-action">
              {sourceLabel}
            </span>

          </div>


          <div className="cs-panel-body">

            <div className="cs-health">

              <HealthRow
                name="Camera Source"
                ok={cameraSourceOk}
              />

              <HealthRow
                name="Person Detection"
                ok={detectionOk}
              />

              <HealthRow
                name="Tracking"
                ok={trackingOk}
              />

              <HealthRow
                name="Crowd Intelligence"
                ok={crowdIntelligenceOk}
              />

            </div>


            <div className="cs-disclaimer">

              <Eye size={13} />

              {isLive
                ? "Live camera monitoring. Human oversight required."
                : "Recorded replay analysis. Human oversight required."}

            </div>

          </div>

        </div>

      </section>


      {/* CAMERA PREVIEW */}

      <section
        className="cs-panel"
        style={{
          marginBottom: "20px",
        }}
      >

        <div className="cs-panel-header">

          <div className="cs-panel-title">

            <div className="cs-panel-icon">
              <Video size={17} />
            </div>

            <div>

              <h3>Camera Preview</h3>

              <p>
                {isLive
                  ? "Live perception source"
                  : "Recorded video source"}
              </p>

            </div>

          </div>

          <span className="cs-panel-action">
            {sourceLabel}
          </span>

        </div>


        <div
          className="cs-panel-body"
          style={{
            padding: 0,
            overflow: "hidden",
            background: "#000",
          }}
        >

          <div
            style={{
              position: "relative",
              width: "100%",
              aspectRatio: "16 / 9",
              background: "#000",
              overflow: "hidden",
            }}
          >

            {/* RECORDED VIDEO */}

            {!isLive ? (

              <video
                key={camera.camera_id}
                controls
                playsInline
                preload="metadata"
                src={`http://127.0.0.1:8000/api/cameras/${camera.camera_id}/video`}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "contain",
                  display: "block",
                  background: "#000",
                }}
              />

            ) : camera.source_type === "webcam" ? (

              /* WEBCAM */

              webcamFrameUrl ? (

                <img
                  src={webcamFrameUrl}
                  alt={`${camera.camera_name || camera.camera_id} live webcam`}
                  style={{
                    width: "100%",
                    height: "100%",
                    objectFit: "contain",
                    display: "block",
                    background: "#000",
                  }}
                />

              ) : (

                <div
                  style={{
                    width: "100%",
                    height: "100%",
                    minHeight: "300px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#94a3b8",
                    background: "#000",
                  }}
                >
                  Connecting to webcam...
                </div>

              )

            ) : ["rtsp", "ip_camera"].includes(camera.source_type) ? (

              /* RTSP / IP CAMERA — use the backend's processed frame.
                 Do not use the MediaMTX iframe here: its independent
                 playback buffer can drift away from the AI track frame. */

              webcamFrameUrl ? (
                <img
                  src={webcamFrameUrl}
                  alt={`${camera.camera_name || camera.camera_id} synchronized live camera frame`}
                  style={{
                    width: "100%",
                    height: "100%",
                    objectFit: "contain",
                    display: "block",
                    background: "#000",
                  }}
                />
              ) : (
                <div
                  style={{
                    width: "100%",
                    height: "100%",
                    minHeight: "300px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#94a3b8",
                    background: "#000",
                  }}
                >
                  Connecting to RTSP camera...
                </div>
              )

            ) : (

              <div
                style={{
                  width: "100%",
                  height: "100%",
                  minHeight: "300px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#94a3b8",
                  background: "#000",
                }}
              >
                Camera preview unavailable
              </div>

            )}

            {/* SVG overlays use the same source-frame coordinate system as the AI tracks. */}
            {isLive && overlayFrame && (
              <CrowdOverlay frame={overlayFrame} camera={camera} />
            )}

          </div>

        </div>

      </section>


      {/* TOP STATS */}

      <section className="cs-module-grid cs-module-grid-4">

        <StatCard
          icon={<Camera size={19} />}
          label="CAMERA"
          value={camera.camera_id || "—"}
        />

        <StatCard
          icon={<MonitorPlay size={19} />}
          label="SOURCE"
          value={sourceLabel}
        />

        <StatCard
          icon={<Gauge size={19} />}
          label="FRAME RATE"
          value={format(fps, 0)}
          suffix=" FPS"
        />

        <StatCard
          icon={<Users size={19} />}
          label="CURRENT PEOPLE"
          value={currentPeople}
        />

      </section>


      {/* CROWD FLOW AND BOTTLENECK INTELLIGENCE */}

      <section
        className="cs-panel"
        style={{ marginBottom: "20px" }}
      >
        <div className="cs-panel-header">
          <div className="cs-panel-title">
            <div className="cs-panel-icon">
              <Activity size={17} />
            </div>

            <div>
              <h3>Crowd Flow & Bottleneck Intelligence</h3>
              <p>
                Directional movement and potential congestion indicators
                for the selected camera
              </p>
            </div>
          </div>

          <span className="cs-panel-action">
            {camera.latest_frame ? "LATEST FRAME" : "WAITING FOR FRAME"}
          </span>
        </div>

        <div className="cs-panel-body">
          <section className="cs-module-grid cs-module-grid-4">
            <StatCard
              icon={<Activity size={19} />}
              label="DOMINANT FLOW"
              value={dominantFlow}
            />

            <StatCard
              icon={<Users size={19} />}
              label="REVERSE-FLOW TRACKS"
              value={reverseFlowCount}
            />

            <StatCard
              icon={<Gauge size={19} />}
              label="REVERSE-FLOW RATIO"
              value={format(reverseFlowRatio, 1)}
              suffix="%"
            />

            <StatCard
              icon={<Activity size={19} />}
              label="FLOW COHERENCE"
              value={format(flowCoherence, 1)}
              suffix="%"
            />
          </section>

          <div style={{ marginTop: "18px" }}>
            <div className="cs-module-list">
              <InfoRow
                label="Moving Tracks"
                value={crowdMetrics.moving_tracks ?? "—"}
              />

              <InfoRow
                label="Potential Bottlenecks"
                value={bottleneckCount}
              />
            </div>
          </div>

          <div style={{ marginTop: "18px" }}>
            <h4 style={{ margin: "0 0 12px" }}>
              Potential Bottleneck Zones
            </h4>

            {bottleneckZones.length > 0 ? (
              <div className="cs-module-list">
                {bottleneckZones.map((zone, index) => (
                  <div
                    key={`${zone.grid_row ?? "r"}-${zone.grid_col ?? "c"}-${index}`}
                    className="cs-panel"
                    style={{ padding: "12px", marginBottom: "10px" }}
                  >
                    <InfoRow
                      label="Zone"
                      value={`Row ${zone.grid_row ?? "—"}, Column ${zone.grid_col ?? "—"}`}
                    />

                    <InfoRow
                      label="People in zone"
                      value={zone.person_count ?? "—"}
                    />

                    <InfoRow
                      label="Mean speed"
                      value={
                        zone.mean_speed_px_per_sec !== undefined
                          ? `${format(zone.mean_speed_px_per_sec, 1)} px/sec`
                          : "—"
                      }
                    />
                  </div>
                ))}
              </div>
            ) : (
              <div className="cs-disclaimer">
                <Eye size={13} />
                No potential bottleneck zones detected in the latest frame.
              </div>
            )}
          </div>

          <div className="cs-disclaimer" style={{ marginTop: "14px" }}>
            <Eye size={13} />
            These are image-space indicators. They are not calibrated
            physical speeds or confirmed real-world bottlenecks.
          </div>
        </div>
      </section>


      {/* CAMERA DETAILS */}

      <section className="cs-module-grid cs-module-grid-2">

        {/* CAMERA SOURCE */}

        <div className="cs-panel">

          <div className="cs-panel-header">

            <div className="cs-panel-title">

              <div className="cs-panel-icon">
                <Camera size={17} />
              </div>

              <div>

                <h3>Camera Source</h3>

                <p>
                  Configured perception source
                </p>

              </div>

            </div>

            <span className="cs-panel-action">
              {sourceLabel}
            </span>

          </div>


          <div className="cs-panel-body">

            <div className="cs-module-list">

              <InfoRow
                label="Camera ID"
                value={camera.camera_id || "—"}
              />

              <InfoRow
                label="Camera Name"
                value={camera.camera_name || "—"}
              />

              <InfoRow
                label="Source Type"
                value={camera.source_type || "—"}
              />

              <InfoRow
                label="Status"
                value={status}
              />

              <InfoRow
                label="Resolution"
                value={
                  width !== "—" && height !== "—"
                    ? `${width} × ${height}`
                    : "—"
                }
              />

              <InfoRow
                label="Frame Rate"
                value={
                  fps !== "—"
                    ? `${format(fps, 0)} FPS`
                    : "—"
                }
              />

              <InfoRow
                label="Frames"
                value={frameCount}
              />

              {!isLive && (
                <InfoRow
                  label="Duration"
                  value={
                    duration !== "—"
                      ? `${format(duration, 2)} sec`
                      : "—"
                  }
                />
              )}

            </div>

          </div>

        </div>


        {/* LATEST AI STATE */}

        <div className="cs-panel">

          <div className="cs-panel-header">

            <div className="cs-panel-title">

              <div className="cs-panel-icon">
                <Activity size={17} />
              </div>

              <div>

                <h3>Latest AI State</h3>

                <p>
                  Production perception output
                </p>

              </div>

            </div>

          </div>


          <div className="cs-panel-body">

            <div className="cs-module-list">

              <InfoRow
                label="People Detected"
                value={
                  camera.latest_person_count ?? "—"
                }
              />

              <InfoRow
                label="Risk Level"
                value={
                  camera.latest_risk
                    ?.operational_risk_level ||
                  "—"
                }
              />

              <InfoRow
                label="Risk Score"
                value={
                  camera.latest_risk
                    ?.operational_risk_score !==
                  undefined
                    ? format(
                        camera.latest_risk
                          .operational_risk_score,
                        2
                      )
                    : "—"
                }
              />

              <InfoRow
                label="Dominant Factor"
                value={
                  camera.latest_risk
                    ?.dominant_risk_factor ||
                  "—"
                }
              />

              <InfoRow
                label="Response"
                value={
                  camera.latest_response
                    ?.response_action ||
                  "—"
                }
              />

            </div>

          </div>

        </div>

      </section>


      {/* SOURCE SUMMARY */}

      <section className="cs-module-grid cs-module-grid-3">

        <StatCard
          icon={<Video size={19} />}
          label="VIDEO SOURCE"
          value={sourceValue}
        />

        <StatCard
          icon={<Clock3 size={19} />}
          label="DURATION"
          value={
            !isLive && duration !== "—"
              ? format(duration, 2)
              : "—"
          }
          suffix={
            !isLive
              ? " sec"
              : ""
          }
        />

        <StatCard
          icon={<Activity size={19} />}
          label="FRAME RECORDS"
          value={frameCount}
        />

      </section>

    </div>
  );
}

export default CameraIntelligence;