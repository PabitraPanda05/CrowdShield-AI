import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";

import {
  Activity,
  AlertTriangle,
  Gauge,
  Users,
  Zap,
  CalendarRange,
  RefreshCw,
  MapPin,
} from "lucide-react";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";


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


function percent(value) {
  if (
    value === null ||
    value === undefined ||
    Number.isNaN(Number(value))
  ) {
    return "—";
  }

  return `${(Number(value) * 100).toFixed(1)}%`;
}


export default function CrowdAnalytics({
  selectedCameraId,
  cameraIntelligence,
}) {
  const [history, setHistory] = useState([]);

  // Persisted SQLite history (separate from the live rolling samples above).
  const [persistedSnapshots, setPersistedSnapshots] = useState([]);
  const [historicalSummary, setHistoricalSummary] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [timeRange, setTimeRange] = useState("1h");
  const [lastHistoryUpdate, setLastHistoryUpdate] = useState(null);


  /*
   * Build a camera-specific rolling history from the
   * live intelligence endpoint.
   *
   * We intentionally do NOT use the old global CSV-based
   * crowd analytics data here because it has no camera_id.
   */
  useEffect(() => {
    if (!cameraIntelligence) {
      return;
    }

    const frame = cameraIntelligence.latest_frame || {};
    const crowd = frame.crowd || {};
    const risk = cameraIntelligence.latest_risk || {};

    const frameNumber = Number(
      frame.frame_number ?? 0
    );

    const timestamp = Number(
      frame.timestamp_seconds ?? 0
    );

    const sample = {
      frameNumber,
      timestamp,
      people: Number(
        cameraIntelligence.latest_person_count ??
          frame.person_count ??
          crowd.person_count ??
          0
      ),
      crowdLoad: Number(
        risk.crowd_load ?? 0
      ),
      movementLoad: Number(
        risk.movement_load ?? 0
      ),
      spatialLoad: Number(
        risk.spatial_load ?? 0
      ),
      growthLoad: Number(
        risk.growth_load ?? 0
      ),
      persistenceLoad: Number(
        risk.persistence_load ?? 0
      ),
      movementEvent: Number(
        risk.movement_event_signal ?? 0
      ),
      riskScore: Number(
        risk.operational_risk_score ?? 0
      ),
      meanSpeed: Number(
        crowd.mean_speed_px_per_sec ?? 0
      ),
      maxSpeed: Number(
        crowd.max_speed_px_per_sec ?? 0
      ),
      movingTracks: Number(
        crowd.moving_tracks ?? 0
      ),
    };


    if (
      !Number.isFinite(sample.frameNumber) ||
      sample.frameNumber <= 0
    ) {
      return;
    }


    setHistory((previous) => {
      const existingIndex = previous.findIndex(
        (item) =>
          item.frameNumber === sample.frameNumber
      );


      if (existingIndex >= 0) {
        const updated = [...previous];
        updated[existingIndex] = sample;
        return updated;
      }


      return [
        ...previous,
        sample,
      ].slice(-30);
    });

  }, [cameraIntelligence]);


  /*
   * Derive historical chart and summary data at component scope.
   * React hooks must never be called inside an effect or callback.
   */
  const historicalChartData = useMemo(
    () =>
      persistedSnapshots.map((item) => ({
        name: item.captured_at
          ? new Date(item.captured_at).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            })
          : `#${item.snapshot_id}`,
        people: Number(item.person_count || 0),
        risk: Number(item.risk_score || 0),
        riskLevel: item.risk_level || "UNKNOWN",
      })),
    [persistedSnapshots]
  );

  const riskDistribution = useMemo(() => {
    const distribution = historicalSummary?.risk_distribution || {};
    return ["LOW", "MODERATE", "HIGH", "CRITICAL"].map((level) => ({
      level,
      count: Number(distribution[level] || 0),
    }));
  }, [historicalSummary]);

  const hotspotZones = useMemo(() => {
    const zones = historicalSummary?.hotspot_zones || [];
    const values = new Map(
      zones.map((item) => [item.zone, Number(item.total_occupancy || 0)])
    );

    return Array.from({ length: 16 }, (_, index) => {
      const row = Math.floor(index / 4) + 1;
      const column = (index % 4) + 1;
      const zone = `r${row}c${column}`;
      return { zone, value: values.get(zone) || 0 };
    });
  }, [historicalSummary]);

  const maxHotspotValue = Math.max(
    1,
    ...hotspotZones.map((item) => item.value)
  );

  const historicalPeak = historicalSummary?.peak_person_count;
  const historicalAverage = historicalSummary?.average_person_count;
  const historicalAverageRisk = historicalSummary?.average_risk_score;

  /*
   * Load persisted SQLite snapshots and summary for the selected camera.
   * The API is polled every 10 seconds; camera workers continue sampling
   * independently every 5 seconds.
   */
  useEffect(() => {
    if (!selectedCameraId) {
      setPersistedSnapshots([]);
      setHistoricalSummary(null);
      setHistoryError("");
      setHistoryLoading(false);
      return undefined;
    }

    let cancelled = false;

    const loadHistoricalData = async (showLoading = false) => {
      if (showLoading && !cancelled) {
        setHistoryLoading(true);
      }

      try {
        const now = new Date();
        let startTime = null;

        if (timeRange !== "all") {
          const durationMs = {
            "1h": 60 * 60 * 1000,
            "6h": 6 * 60 * 60 * 1000,
            "24h": 24 * 60 * 60 * 1000,
          }[timeRange];

          startTime = new Date(now.getTime() - durationMs).toISOString();
        }

        const filters = {
          cameraId: selectedCameraId,
          startTime,
          endTime: now.toISOString(),
        };

        const [historyResponse, summaryResponse] = await Promise.all([
          api.crowdHistory(filters),
          api.crowdHistorySummary(filters),
        ]);

        if (cancelled) return;

        if (historyResponse?.status !== "success") {
          throw new Error(
            historyResponse?.message || "Unable to load crowd history."
          );
        }

        const rows = Array.isArray(historyResponse.data)
          ? historyResponse.data
          : [];

        setPersistedSnapshots(
          rows.slice().sort(
            (a, b) =>
              new Date(a.captured_at).getTime() -
              new Date(b.captured_at).getTime()
          )
        );

        setHistoricalSummary(
          summaryResponse?.status === "success"
            ? summaryResponse.data || null
            : null
        );
        setHistoryError("");
        setLastHistoryUpdate(new Date());
      } catch (error) {
        if (!cancelled) {
          setHistoryError(
            error.message || "Unable to load historical analytics."
          );
        }
      } finally {
        if (!cancelled && showLoading) {
          setHistoryLoading(false);
        }
      }
    };

    loadHistoricalData(true);
    const intervalId = window.setInterval(
      () => loadHistoricalData(false),
      10000
    );

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [selectedCameraId, timeRange]);

  /*
   * Reset camera-specific history when the user switches
   * to another camera.
   */
  useEffect(() => {
    setHistory([]);
    setPersistedSnapshots([]);
    setHistoricalSummary(null);
  }, [selectedCameraId]);


  const latestFrame =
    cameraIntelligence?.latest_frame || {};

  const latestCrowd =
    latestFrame.crowd || {};

  const latestRisk =
    cameraIntelligence?.latest_risk || {};

  const latestResponse =
    cameraIntelligence?.latest_response || {};


  const currentPeople =
    Number(
      cameraIntelligence?.latest_person_count ??
        latestFrame.person_count ??
        0
    );


  const currentCrowdLoad =
    Number(
      latestRisk.crowd_load ?? 0
    );


  const currentMovementLoad =
    Number(
      latestRisk.movement_load ?? 0
    );


  const currentSpatialLoad =
    Number(
      latestRisk.spatial_load ?? 0
    );


  const currentGrowthLoad =
    Number(
      latestRisk.growth_load ?? 0
    );


  const currentPersistenceLoad =
    Number(
      latestRisk.persistence_load ?? 0
    );


  const currentRisk =
    Number(
      latestRisk.operational_risk_score ?? 0
    );


  const currentRiskLevel =
    latestRisk.operational_risk_level ||
    "UNKNOWN";


  const meanSpeed =
    Number(
      latestCrowd.mean_speed_px_per_sec ?? 0
    );


  const maxSpeed =
    Number(
      latestCrowd.max_speed_px_per_sec ?? 0
    );


  const movingTracks =
    Number(
      latestCrowd.moving_tracks ?? 0
    );


  const movementEventActive =
    Number(
      latestRisk.movement_event_signal ?? 0
    ) > 0;


  const stats = useMemo(() => {
    if (!history.length) {
      return {
        averagePeople: currentPeople,
        maxPeople: currentPeople,
        averageCrowdLoad: currentCrowdLoad,
        averageMovementLoad: currentMovementLoad,
        averageSpatialLoad: currentSpatialLoad,
        movementEvents: movementEventActive ? 1 : 0,
      };
    }


    const averagePeople =
      history.reduce(
        (sum, item) =>
          sum + Number(item.people || 0),
        0
      ) / history.length;


    const maxPeople = Math.max(
      ...history.map(
        (item) =>
          Number(item.people || 0)
      )
    );


    const averageCrowdLoad =
      history.reduce(
        (sum, item) =>
          sum + Number(item.crowdLoad || 0),
        0
      ) / history.length;


    const averageMovementLoad =
      history.reduce(
        (sum, item) =>
          sum + Number(item.movementLoad || 0),
        0
      ) / history.length;


    const averageSpatialLoad =
      history.reduce(
        (sum, item) =>
          sum + Number(item.spatialLoad || 0),
        0
      ) / history.length;


    const movementEvents =
      history.filter(
        (item) =>
          Number(item.movementEvent || 0) > 0
      ).length;


    return {
      averagePeople,
      maxPeople,
      averageCrowdLoad,
      averageMovementLoad,
      averageSpatialLoad,
      movementEvents,
    };

  }, [
    history,
    currentPeople,
    currentCrowdLoad,
    currentMovementLoad,
    currentSpatialLoad,
    movementEventActive,
  ]);


  const chartData = useMemo(() => {
    return history.map((item, index) => ({
      name:
        item.timestamp > 0
          ? `${item.timestamp.toFixed(1)}s`
          : `F${item.frameNumber || index + 1}`,

      crowd:
        Number(item.crowdLoad || 0),

      movement:
        Number(item.movementLoad || 0),

      spatial:
        Number(item.spatialLoad || 0),

      growth:
        Number(item.growthLoad || 0),

      people:
        Number(item.people || 0),

      risk:
        Number(item.riskScore || 0),

      speed:
        Number(item.meanSpeed || 0),
    }));
  }, [history]);


  const latestChartData = useMemo(() => {
    return chartData.slice(-20);
  }, [chartData]);


  if (!selectedCameraId) {
    return (
      <div className="cs-module">

        <div className="cs-module-hero">

          <div className="cs-module-icon">
            <Users size={28} />
          </div>

          <div>

            <div className="cs-module-kicker">
              OPERATIONS / CROWD ANALYTICS
            </div>

            <h2>Crowd Analytics</h2>

            <p>
              Select a camera to view camera-specific
              crowd intelligence.
            </p>

          </div>

        </div>

      </div>
    );
  }


  return (
    <div className="cs-module">

      {/* HERO */}

      <div className="cs-module-hero">

        <div className="cs-module-icon">
          <Users size={28} />
        </div>

        <div>

          <div className="cs-module-kicker">
            OPERATIONS / CROWD ANALYTICS
          </div>

          <h2>
            Crowd Analytics
          </h2>

          <p>
            Live crowd intelligence for selected camera{" "}
            <strong>
              {selectedCameraId}
            </strong>
            .
          </p>

        </div>

      </div>


      {/* CAMERA STATUS */}

      <div className="cs-module-card">

        <div className="cs-module-card-header">

          <div>

            <h3>
              Live Camera Intelligence
            </h3>

            <p>
              Camera-specific data from the production
              perception and risk pipeline.
            </p>

          </div>

          <span className="cs-module-badge">
            {cameraIntelligence?.status ||
              "WAITING"}
          </span>

        </div>


        {!cameraIntelligence ? (

          <div className="cs-empty">
            <Activity
              size={17}
              className="cs-spin"
            />
            Waiting for camera intelligence...
          </div>

        ) : (

          <div className="cs-module-two-column">

            <div>

              <div className="cs-module-list-row">

                <div>
                  <strong>
                    Camera
                  </strong>

                  <span>
                    {cameraIntelligence.camera_name ||
                      selectedCameraId}
                  </span>
                </div>

                <div className="cs-module-list-value">

                  <strong>
                    {cameraIntelligence.source_type ||
                      "—"}
                  </strong>

                  <span>
                    {cameraIntelligence.live_stream
                      ? "LIVE"
                      : "RECORDED"}
                  </span>

                </div>

              </div>


              <div className="cs-module-list-row">

                <div>
                  <strong>
                    Frame
                  </strong>

                  <span>
                    Latest processed frame
                  </span>
                </div>

                <div className="cs-module-list-value">

                  <strong>
                    {latestFrame.frame_number ??
                      "—"}
                  </strong>

                  <span>
                    {format(
                      latestFrame.timestamp_seconds,
                      1
                    )}s
                  </span>

                </div>

              </div>

            </div>


            <div>

              <div className="cs-module-list-row">

                <div>
                  <strong>
                    Risk
                  </strong>

                  <span>
                    Current operational risk
                  </span>
                </div>

                <div className="cs-module-list-value">

                  <strong>
                    {format(currentRisk)}
                  </strong>

                  <span>
                    {currentRiskLevel}
                  </span>

                </div>

              </div>


              <div className="cs-module-list-row">

                <div>
                  <strong>
                    Response
                  </strong>

                  <span>
                    Current decision support
                  </span>
                </div>

                <div className="cs-module-list-value">

                  <strong>
                    {latestResponse.response_action ||
                      "—"}
                  </strong>

                  <span>
                    {latestResponse.response_priority ||
                      "—"}
                  </span>

                </div>

              </div>

            </div>

          </div>

        )}

      </div>


      {/* SUMMARY CARDS */}

      <div className="cs-module-grid">

        <div className="cs-module-stat">

          <div className="cs-module-stat-icon">
            <Users size={19} />
          </div>

          <span>
            CURRENT PEOPLE
          </span>

          <strong>
            {format(currentPeople, 0)}
          </strong>

          <small>
            selected camera
          </small>

        </div>


        <div className="cs-module-stat">

          <div className="cs-module-stat-icon">
            <Users size={19} />
          </div>

          <span>
            MAXIMUM PEOPLE
          </span>

          <strong>
            {format(stats.maxPeople, 0)}
          </strong>

          <small>
            rolling camera window
          </small>

        </div>


        <div className="cs-module-stat">

          <div className="cs-module-stat-icon">
            <Gauge size={19} />
          </div>

          <span>
            CROWD LOAD
          </span>

          <strong>
            {percent(currentCrowdLoad)}
          </strong>

          <small>
            current camera signal
          </small>

        </div>


        <div className="cs-module-stat">

          <div className="cs-module-stat-icon">
            <Zap size={19} />
          </div>

          <span>
            MOVEMENT LOAD
          </span>

          <strong>
            {percent(currentMovementLoad)}
          </strong>

          <small>
            current camera signal
          </small>

        </div>


        <div className="cs-module-stat">

          <div className="cs-module-stat-icon">
            <Activity size={19} />
          </div>

          <span>
            SPATIAL LOAD
          </span>

          <strong>
            {percent(currentSpatialLoad)}
          </strong>

          <small>
            current camera signal
          </small>

        </div>


        <div className="cs-module-stat">

          <div className="cs-module-stat-icon">
            <AlertTriangle size={19} />
          </div>

          <span>
            MOVEMENT EVENTS
          </span>

          <strong>
            {stats.movementEvents}
          </strong>

          <small>
            observed in rolling history
          </small>

        </div>

      </div>


      {/* CROWD LOAD TIMELINE */}

      <div className="cs-module-card">

        <div className="cs-module-card-header">

          <div>

            <h3>
              Crowd Load & Movement
            </h3>

            <p>
              Rolling live history captured from{" "}
              {selectedCameraId}.
            </p>

          </div>

          <span className="cs-module-badge">
            {history.length} SAMPLES
          </span>

        </div>


        <div className="cs-module-chart">

          {latestChartData.length ? (

            <ResponsiveContainer
              width="100%"
              height={310}
            >

              <AreaChart
                data={latestChartData}
              >

                <defs>

                  <linearGradient
                    id="cameraCrowdGradient"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >

                    <stop
                      offset="5%"
                      stopColor="#38bdf8"
                      stopOpacity={0.30}
                    />

                    <stop
                      offset="95%"
                      stopColor="#38bdf8"
                      stopOpacity={0}
                    />

                  </linearGradient>

                </defs>


                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#172033"
                />


                <XAxis
                  dataKey="name"
                  stroke="#64748b"
                  tick={{ fontSize: 11 }}
                />


                <YAxis
                  domain={[0, 1]}
                  stroke="#64748b"
                  tick={{ fontSize: 11 }}
                />


                <Tooltip
                  contentStyle={{
                    background: "#07111f",
                    border: "1px solid #1e293b",
                    borderRadius: "10px",
                    color: "#e2e8f0",
                  }}
                />


                <Area
                  type="monotone"
                  dataKey="crowd"
                  name="Crowd Load"
                  stroke="#38bdf8"
                  fill="url(#cameraCrowdGradient)"
                  strokeWidth={2}
                />


                <Area
                  type="monotone"
                  dataKey="movement"
                  name="Movement Load"
                  stroke="#a78bfa"
                  fill="transparent"
                  strokeWidth={2}
                />


                <Area
                  type="monotone"
                  dataKey="spatial"
                  name="Spatial Load"
                  stroke="#2dd4bf"
                  fill="transparent"
                  strokeWidth={2}
                />

              </AreaChart>

            </ResponsiveContainer>

          ) : (

            <div className="cs-empty">
              <Activity
                size={17}
                className="cs-spin"
              />
              Waiting for live camera samples...
            </div>

          )}

        </div>

      </div>


      {/* GROWTH */}

      <div className="cs-module-two-column">

        <div className="cs-module-card">

          <div className="cs-module-card-header">

            <div>

              <h3>
                Crowd Growth
              </h3>

              <p>
                Current selected-camera growth signal.
              </p>

            </div>

          </div>


          <div className="cs-module-chart">

            {latestChartData.length ? (

              <ResponsiveContainer
                width="100%"
                height={260}
              >

                <BarChart
                  data={latestChartData}
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#172033"
                  />


                  <XAxis
                    dataKey="name"
                    stroke="#64748b"
                    tick={{ fontSize: 10 }}
                  />


                  <YAxis
                    domain={[0, 1]}
                    stroke="#64748b"
                    tick={{ fontSize: 10 }}
                  />


                  <Tooltip
                    contentStyle={{
                      background: "#07111f",
                      border: "1px solid #1e293b",
                      borderRadius: "10px",
                    }}
                  />


                  <Bar
                    dataKey="growth"
                    name="Growth Load"
                    fill="#f59e0b"
                    radius={[3, 3, 0, 0]}
                  />

                </BarChart>

              </ResponsiveContainer>

            ) : (

              <div className="cs-empty">
                Waiting for camera growth data...
              </div>

            )}

          </div>

        </div>


        {/* MOVEMENT EVENT */}

        <div className="cs-module-card">

          <div className="cs-module-card-header">

            <div>

              <h3>
                Movement Event
              </h3>

              <p>
                Current movement-event signal for the
                selected camera.
              </p>

            </div>

            <span
              className={`cs-module-badge ${
                movementEventActive
                  ? "warning"
                  : ""
              }`}
            >
              {movementEventActive
                ? "ACTIVE"
                : "CLEAR"}
            </span>

          </div>


          <div className="cs-module-list">

            <div className="cs-module-list-row">

              <div>

                <strong>
                  Signal
                </strong>

                <span>
                  High-speed movement event
                </span>

              </div>

              <div className="cs-module-list-value">

                <strong>
                  {movementEventActive
                    ? "YES"
                    : "NO"}
                </strong>

                <span>
                  {format(
                    latestRisk.movement_event_signal,
                    0
                  )}
                </span>

              </div>

            </div>


            <div className="cs-module-list-row">

              <div>

                <strong>
                  Mean Speed
                </strong>

                <span>
                  Image-space movement speed
                </span>

              </div>

              <div className="cs-module-list-value">

                <strong>
                  {format(meanSpeed, 0)}
                </strong>

                <span>
                  px/s
                </span>

              </div>

            </div>


            <div className="cs-module-list-row">

              <div>

                <strong>
                  Maximum Speed
                </strong>

                <span>
                  Highest tracked speed
                </span>

              </div>

              <div className="cs-module-list-value">

                <strong>
                  {format(maxSpeed, 0)}
                </strong>

                <span>
                  px/s
                </span>

              </div>

            </div>


            <div className="cs-module-list-row">

              <div>

                <strong>
                  Moving Tracks
                </strong>

                <span>
                  Currently moving tracked objects
                </span>

              </div>

              <div className="cs-module-list-value">

                <strong>
                  {movingTracks}
                </strong>

                <span>
                  tracks
                </span>

              </div>

            </div>

          </div>

        </div>

      </div>


      {/* CURRENT RISK FEATURES */}

      <div className="cs-module-card">

        <div className="cs-module-card-header">

          <div>

            <h3>
              Current Risk Features
            </h3>

            <p>
              Live feature values from the selected camera.
            </p>

          </div>

          <span className="cs-module-badge">
            LIVE
          </span>

        </div>


        <div className="cs-flow-grid">

          <div className="cs-flow-card">

            <div className="cs-flow-icon">
              <Gauge size={18} />
            </div>

            <div className="cs-flow-content">

              <strong>
                Crowd Load
              </strong>

              <span>
                Current normalized signal
              </span>

              <small>
                {percent(currentCrowdLoad)}
              </small>

            </div>

          </div>


          <div className="cs-flow-card">

            <div className="cs-flow-icon">
              <Zap size={18} />
            </div>

            <div className="cs-flow-content">

              <strong>
                Movement Load
              </strong>

              <span>
                Current normalized signal
              </span>

              <small>
                {percent(currentMovementLoad)}
              </small>

            </div>

          </div>


          <div className="cs-flow-card">

            <div className="cs-flow-icon">
              <Activity size={18} />
            </div>

            <div className="cs-flow-content">

              <strong>
                Spatial Load
              </strong>

              <span>
                Current spatial signal
              </span>

              <small>
                {percent(currentSpatialLoad)}
              </small>

            </div>

          </div>


          <div className="cs-flow-card">

            <div className="cs-flow-icon">
              <Users size={18} />
            </div>

            <div className="cs-flow-content">

              <strong>
                Persistence
              </strong>

              <span>
                Current temporal signal
              </span>

              <small>
                {percent(currentPersistenceLoad)}
              </small>

            </div>

          </div>

        </div>


        <div className="cs-module-note">

          <Activity size={14} />

          All values above come from the selected
          camera's live production intelligence endpoint.
          No camera ID is inferred from historical global data.

        </div>

      </div>


      {/* PERSISTED HISTORICAL ANALYTICS */}
      <div className="cs-module-card">
        <div className="cs-module-card-header">
          <div>
            <h3>
              <CalendarRange
                size={17}
                style={{ display: "inline", marginRight: 8, verticalAlign: "middle" }}
              />
              Historical Crowd Analytics
            </h3>
            <p>
              Persisted five-second snapshots from the selected camera's SQLite history.
            </p>
          </div>

          <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
            <select
              value={timeRange}
              onChange={(event) => setTimeRange(event.target.value)}
              aria-label="Historical time range"
              style={{
                background: "#07111f",
                color: "#e2e8f0",
                border: "1px solid #334155",
                borderRadius: 8,
                padding: "8px 10px",
              }}
            >
              <option value="1h">Last hour</option>
              <option value="6h">Last 6 hours</option>
              <option value="24h">Last 24 hours</option>
              <option value="all">All recorded history</option>
            </select>
            <span className="cs-module-badge">
              {persistedSnapshots.length} SNAPSHOTS
            </span>
          </div>
        </div>

        {historyError ? (
          <div className="cs-empty" role="alert">
            <AlertTriangle size={17} />
            {historyError}
          </div>
        ) : historyLoading && !persistedSnapshots.length ? (
          <div className="cs-empty">
            <Activity size={17} className="cs-spin" />
            Loading persisted crowd history...
          </div>
        ) : !persistedSnapshots.length ? (
          <div className="cs-empty">
            <Activity size={17} />
            No historical data is available for {selectedCameraId} in this time range.
            Snapshots will appear after this camera's history sampler records data.
          </div>
        ) : (
          <>
            <div className="cs-module-grid" style={{ marginTop: 18 }}>
              <div className="cs-module-stat">
                <div className="cs-module-stat-icon"><Users size={19} /></div>
                <span>HISTORICAL AVERAGE</span>
                <strong>{format(historicalAverage, 1)}</strong>
                <small>people per snapshot</small>
              </div>

              <div className="cs-module-stat">
                <div className="cs-module-stat-icon"><Users size={19} /></div>
                <span>HISTORICAL PEAK</span>
                <strong>{format(historicalPeak, 0)}</strong>
                <small>
                  {historicalSummary?.peak_captured_at
                    ? new Date(historicalSummary.peak_captured_at).toLocaleString()
                    : "peak person count"}
                </small>
              </div>

              <div className="cs-module-stat">
                <div className="cs-module-stat-icon"><Gauge size={19} /></div>
                <span>AVERAGE RISK SCORE</span>
                <strong>{format(historicalAverageRisk, 1)}</strong>
                <small>historical risk score</small>
              </div>

              <div className="cs-module-stat">
                <div className="cs-module-stat-icon"><Activity size={19} /></div>
                <span>RECORDED SNAPSHOTS</span>
                <strong>{format(historicalSummary?.snapshot_count ?? persistedSnapshots.length, 0)}</strong>
                <small>saved in SQLite</small>
              </div>
            </div>

            <div className="cs-module-two-column" style={{ marginTop: 18 }}>
              <div className="cs-module-card">
                <div className="cs-module-card-header">
                  <div>
                    <h3>People Count Over Time</h3>
                    <p>Historical person count from saved camera snapshots.</p>
                  </div>
                </div>
                <div className="cs-module-chart">
                  <ResponsiveContainer width="100%" height={280}>
                    <AreaChart data={historicalChartData}>
                      <defs>
                        <linearGradient id="historicalPeopleGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#172033" />
                      <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 10 }} />
                      <YAxis allowDecimals={false} stroke="#64748b" tick={{ fontSize: 11 }} />
                      <Tooltip
                        contentStyle={{
                          background: "#07111f",
                          border: "1px solid #1e293b",
                          borderRadius: 10,
                          color: "#e2e8f0",
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="people"
                        name="People"
                        stroke="#38bdf8"
                        fill="url(#historicalPeopleGradient)"
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="cs-module-card">
                <div className="cs-module-card-header">
                  <div>
                    <h3>Risk Score Over Time</h3>
                    <p>Historical operational risk scores.</p>
                  </div>
                </div>
                <div className="cs-module-chart">
                  <ResponsiveContainer width="100%" height={280}>
                    <AreaChart data={historicalChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#172033" />
                      <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 10 }} />
                      <YAxis domain={[0, 100]} stroke="#64748b" tick={{ fontSize: 11 }} />
                      <Tooltip
                        contentStyle={{
                          background: "#07111f",
                          border: "1px solid #1e293b",
                          borderRadius: 10,
                          color: "#e2e8f0",
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="risk"
                        name="Risk score"
                        stroke="#f59e0b"
                        fill="transparent"
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            <div className="cs-module-two-column" style={{ marginTop: 18 }}>
              <div className="cs-module-card">
                <div className="cs-module-card-header">
                  <div>
                    <h3>Risk Distribution</h3>
                    <p>Number of saved snapshots in each risk category.</p>
                  </div>
                </div>
                <div className="cs-module-chart">
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={riskDistribution}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#172033" />
                      <XAxis dataKey="level" stroke="#64748b" tick={{ fontSize: 10 }} />
                      <YAxis allowDecimals={false} stroke="#64748b" tick={{ fontSize: 11 }} />
                      <Tooltip
                        contentStyle={{
                          background: "#07111f",
                          border: "1px solid #1e293b",
                          borderRadius: 10,
                          color: "#e2e8f0",
                        }}
                      />
                      <Bar dataKey="count" name="Snapshots" fill="#a78bfa" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="cs-module-card">
                <div className="cs-module-card-header">
                  <div>
                    <h3>
                      <MapPin
                        size={16}
                        style={{ display: "inline", marginRight: 7, verticalAlign: "middle" }}
                      />
                      4×4 Crowd Hotspot Map
                    </h3>
                    <p>Accumulated image-space occupancy across saved snapshots.</p>
                  </div>
                </div>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
                    gap: 8,
                    padding: "12px 4px",
                  }}
                >
                  {hotspotZones.map((item) => {
                    const intensity = item.value / maxHotspotValue;
                    return (
                      <div
                        key={item.zone}
                        title={`${item.zone}: ${item.value} accumulated occupancy`}
                        style={{
                          minHeight: 76,
                          borderRadius: 9,
                          border: "1px solid rgba(148,163,184,0.22)",
                          background: `rgba(239, 68, 68, ${0.08 + intensity * 0.72})`,
                          display: "flex",
                          flexDirection: "column",
                          justifyContent: "center",
                          alignItems: "center",
                          gap: 5,
                          color: "#f8fafc",
                        }}
                      >
                        <strong style={{ fontSize: 13 }}>{item.zone.toUpperCase()}</strong>
                        <span style={{ fontSize: 19, fontWeight: 700 }}>{item.value}</span>
                      </div>
                    );
                  })}
                </div>
                <div className="cs-module-note">
                  <AlertTriangle size={14} />
                  Occupancy totals are accumulated track-center counts, not calibrated physical density (people/m²).
                </div>
              </div>
            </div>

            <div className="cs-module-card" style={{ marginTop: 18 }}>
              <div className="cs-module-card-header">
                <div>
                  <h3>Peak Periods & Historical Hotspots</h3>
                  <p>Summary calculated from the selected camera's persisted records.</p>
                </div>
                <span className="cs-module-badge">
                  {historicalSummary?.peak_periods?.length || 0} PERIODS
                </span>
              </div>

              {historicalSummary?.peak_periods?.length ? (
                <div className="cs-module-list">
                  {historicalSummary.peak_periods.map((period) => (
                    <div className="cs-module-list-row" key={period.period}>
                      <div>
                        <strong>{period.period}</strong>
                        <span>{period.snapshot_count} snapshots recorded</span>
                      </div>
                      <div className="cs-module-list-value">
                        <strong>{format(period.average_person_count, 1)} avg.</strong>
                        <span>{format(period.peak_person_count, 0)} peak people</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="cs-empty">No peak-period summary is available.</div>
              )}

              <div className="cs-module-note">
                <RefreshCw size={14} />
                {lastHistoryUpdate
                  ? `Last refreshed ${lastHistoryUpdate.toLocaleTimeString()}. Automatically refreshes every 10 seconds.`
                  : "Historical data refreshes automatically every 10 seconds."}
              </div>
            </div>
          </>
        )}
      </div>

      {/* DISCLAIMER */}

      <div className="cs-module-disclaimer">

        <AlertTriangle size={15} />

        <div>

          <strong>
            Decision-support interpretation
          </strong>

          <span>
            Crowd and movement values are production
            pipeline features and rule-based operational
            signals. They are not probabilities and are not
            validated emergency predictions. Human review
            is required for operational response decisions.
          </span>

        </div>

      </div>

    </div>
  );
}