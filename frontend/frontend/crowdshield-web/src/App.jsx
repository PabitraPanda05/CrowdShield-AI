import { useCallback, useEffect, useMemo, useState } from "react";

import {
  Activity,
  AlertTriangle,
  BarChart3,
  Bell,
  Camera,
  CheckCircle2,
  Database,
  Eye,
  Gauge,
  LayoutDashboard,
  Map,
  RefreshCw,
  Route,
  Shield,
  Siren,
  Users,
  Wifi,
  XCircle,
  Zap,
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

import { api } from "./api";

import CameraIntelligence from "./views/CameraIntelligence";
import CrowdAnalytics from "./views/CrowdAnalytics";
import RiskMap from "./views/RiskMap";
import ResponseRouting from "./views/ResponseRouting";
import AIPipeline from "./views/AIPipeline";
import DatabaseView from "./views/DatabaseView";
import AlertsManagement from "./views/AlertsManagement";


function riskColor(level) {
  const value = String(level || "").toUpperCase();

  if (value === "CRITICAL") return "#fb7185";
  if (value === "HIGH") return "#fb923c";
  if (value === "MODERATE") return "#facc15";
  if (value === "LOW") return "#2dd4bf";

  return "#64748b";
}


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


function App() {
  const [summary, setSummary] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [cameras, setCameras] = useState([]);

  // Global selected camera
  const [selectedCameraId, setSelectedCameraId] = useState(null);

  // Live intelligence for selected camera
  const [cameraIntelligence, setCameraIntelligence] = useState(null);

  // Rolling history of distinct processed frames for the selected camera.
  const [liveRiskHistory, setLiveRiskHistory] = useState([]);

  const [crowd, setCrowd] = useState(null);
  const [route, setRoute] = useState(null);
  const [dbHealth, setDbHealth] = useState(null);

  // Active frontend module
  const [activeSection, setActiveSection] = useState("command");


  const sectionMeta = {
    command: {
      title: "Command Center",
      kicker: "OPERATIONS / OVERVIEW",
    },
    camera: {
      title: "Camera Intelligence",
      kicker: "OPERATIONS / CAMERA INTELLIGENCE",
    },
    crowd: {
      title: "Crowd Analytics",
      kicker: "OPERATIONS / CROWD ANALYTICS",
    },
    risk: {
      title: "Risk Map",
      kicker: "OPERATIONS / RISK MAP",
    },
    routing: {
      title: "Response Routing",
      kicker: "OPERATIONS / RESPONSE ROUTING",
    },
    alerts: {
      title: "Alert Management",
      kicker: "OPERATIONS / ALERT MANAGEMENT",
    },
    pipeline: {
      title: "AI Pipeline",
      kicker: "SYSTEM / AI PIPELINE",
    },
    database: {
      title: "Database",
      kicker: "SYSTEM / DATABASE",
    },
  };


  const currentSection =
    sectionMeta[activeSection] || sectionMeta.command;


  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);


  const loadData = useCallback(async (silent = false) => {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const results = await Promise.allSettled([
        api.dashboardSummary(),
        api.riskTimeline(),
        api.alerts(),
        api.cameras(),
        api.crowdIntelligence(),
        api.simulatedRoute(),
        api.databaseHealth(),
      ]);

      const [
        summaryResult,
        timelineResult,
        alertsResult,
        cameraResult,
        crowdResult,
        routeResult,
        dbResult,
      ] = results;


      if (summaryResult.status === "fulfilled") {
        setSummary(summaryResult.value);
      }


      if (timelineResult.status === "fulfilled") {
        setTimeline(timelineResult.value?.data || []);
      }


      if (alertsResult.status === "fulfilled") {
        setAlerts(alertsResult.value?.alerts || []);
      }


      if (cameraResult.status === "fulfilled") {
        setCameras(cameraResult.value?.data || []);
      }


      if (crowdResult.status === "fulfilled") {
        setCrowd(crowdResult.value);
      }


      if (routeResult.status === "fulfilled") {
        setRoute(routeResult.value);
      }


      if (dbResult.status === "fulfilled") {
        setDbHealth(dbResult.value);
      }


      const successCount = results.filter(
        (result) => result.status === "fulfilled"
      ).length;


      setConnected(successCount > 0);


      if (successCount === 0) {
        setError("Backend API is unavailable.");
      } else if (successCount < results.length) {
        setError("Some backend services are unavailable.");
      } else {
        setError("");
      }


      setLastUpdated(new Date());

    } catch (err) {
      console.error(err);
      setConnected(false);
      setError("Failed to connect to backend.");

    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);


  // Keep the selected camera stable when camera data refreshes
  useEffect(() => {
    setSelectedCameraId((currentId) => {
      if (cameras.length === 0) {
        return currentId;
      }


      const currentCameraExists = cameras.some(
        (cameraItem) => cameraItem.camera_id === currentId
      );


      if (currentCameraExists) {
        return currentId;
      }


      const preferredCamera =
        cameras.find(
          (cameraItem) =>
            cameraItem.live_stream &&
            cameraItem.status === "RUNNING"
        ) ||
        cameras[0];


      return preferredCamera?.camera_id || null;
    });
  }, [cameras]);


  // Load live AI intelligence for the selected camera
  useEffect(() => {
    if (!selectedCameraId) {
      setCameraIntelligence(null);
      return;
    }


    let cancelled = false;


    const loadCameraIntelligence = async () => {
      try {
        const result = await api.cameraIntelligence(
          selectedCameraId
        );


        if (!cancelled) {
          setCameraIntelligence(
            result?.data || null
          );
        }

      } catch (err) {
        console.error(
          "Failed to load camera intelligence:",
          err
        );


        if (!cancelled) {
          setCameraIntelligence(null);
        }
      }
    };


    loadCameraIntelligence();


    const timer = setInterval(
      loadCameraIntelligence,
      1000
    );


    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [selectedCameraId]);


  useEffect(() => {
    loadData(false);


    const timer = setInterval(() => {
      loadData(true);
    }, 10000);


    return () => clearInterval(timer);
  }, [loadData]);


  const latest = summary?.latest_state || {};


  const camera =
    cameras.find(
      (cameraItem) => cameraItem.camera_id === selectedCameraId
    ) ||
    cameras[0] ||
    {};


  // ---------------------------------------------------------
  // SELECTED CAMERA LIVE INTELLIGENCE
  // ---------------------------------------------------------

  const liveCamera = cameraIntelligence || {};

  const liveFrame = liveCamera.latest_frame || {};
  const liveRisk = liveCamera.latest_risk || {};
  const liveResponse = liveCamera.latest_response || {};

  const isSelectedCameraLive = Boolean(
    cameraIntelligence?.camera_id === selectedCameraId &&
    cameraIntelligence?.live_stream
  );

  // Start a fresh timeline whenever the selected camera changes.
  useEffect(() => {
    setLiveRiskHistory([]);
  }, [selectedCameraId]);

  // Store each distinct processed frame once; the API is polled every second.
  useEffect(() => {
    if (
      !selectedCameraId ||
      cameraIntelligence?.camera_id !== selectedCameraId
    ) {
      return;
    }

    const risk = cameraIntelligence.latest_risk;
    const frame = cameraIntelligence.latest_frame;
    const score = Number(risk?.operational_risk_score);
    const frameNumber = Number(frame?.frame_number ?? risk?.end_frame ?? 0);

    if (
      !risk ||
      !frame ||
      !Number.isFinite(score) ||
      frameNumber <= 0
    ) {
      return;
    }

    const sample = {
      frameNumber,
      timestamp: frame.timestamp_seconds ?? risk.end_time ?? null,
      risk: score,
      level: risk.operational_risk_level || "UNKNOWN",
      people: Number(frame.person_count ?? 0),
      windowId: risk.window_id ?? null,
      reason: risk.operational_risk_reason || "Operational risk signal detected.",
    };

    setLiveRiskHistory((previous) => {
      const last = previous[previous.length - 1];
      if (last && last.frameNumber === sample.frameNumber) {
        return previous;
      }
      return [...previous, sample].slice(-30);
    });
  }, [selectedCameraId, cameraIntelligence]);


  const riskScore = Number(
    liveRisk.operational_risk_score ??
      camera?.latest_risk?.operational_risk_score ??
      latest?.operational_risk_score ??
      0
  );


  const riskLevel =
    liveRisk.operational_risk_level ||
    camera?.latest_risk?.operational_risk_level ||
    latest?.operational_risk_level ||
    "UNKNOWN";


  const timelineData = useMemo(() => {
    if (isSelectedCameraLive) {
      return liveRiskHistory.map((sample, index) => ({
        name: sample.timestamp != null
          ? `${Math.round(Number(sample.timestamp))}s`
          : `#${sample.frameNumber}`,
        risk: sample.risk,
        people: sample.people,
        level: sample.level,
      }));
    }

    return timeline.map((item) => ({
      name: `W${item.window_id}`,
      risk: Number(item.operational_risk_score || 0),
      crowd: Number(item.crowd_load || 0) * 100,
      movement: Number(item.movement_load || 0) * 100,
    }));
  }, [isSelectedCameraLive, liveRiskHistory, timeline]);

  const liveOperationalAlerts = useMemo(() => {
    if (!isSelectedCameraLive || !liveRisk.operational_risk_level) {
      return [];
    }

    const level = String(liveRisk.operational_risk_level).toUpperCase();
    const hasActiveSignal = Boolean(
      liveResponse.active_signals &&
      String(liveResponse.active_signals).trim() &&
      String(liveResponse.active_signals).toLowerCase() !== "none"
    );

    if (level === "LOW" && !hasActiveSignal) {
      return [];
    }

    return [{
      window_id: liveRisk.window_id ?? liveResponse.window_id ?? "LIVE",
      operational_risk_level: level,
      operational_risk_score: liveRisk.operational_risk_score,
      description:
        liveRisk.operational_risk_reason ||
        liveResponse.response_reason ||
        "Live operational risk signal detected.",
    }];
  }, [isSelectedCameraLive, liveRisk, liveResponse]);

  const displayedAlerts = isSelectedCameraLive
    ? liveOperationalAlerts
    : alerts;

  const responseDistribution =
    summary?.response_distribution || [];


  const crowdRows =
    crowd?.data || [];


  const peopleCount =
    liveCamera.latest_person_count ??
    liveFrame.person_count ??
    camera?.latest_person_count ??
    camera?.latest_frame?.person_count ??
    latest?.max_people ??
    latest?.people_count ??
    crowdRows?.[crowdRows.length - 1]?.people_count ??
    "—";


  return (
    <div className="cs-app">

      {/* SIDEBAR */}

      <aside className="cs-sidebar">

        <div className="cs-brand">

          <div className="cs-logo">
            <Shield size={25} />
          </div>

          <div>
            <div className="cs-brand-name">
              CrowdShield
            </div>

            <div className="cs-brand-sub">
              AI COMMAND CENTER
            </div>
          </div>

        </div>


        <div className="cs-nav-title">
          OPERATIONS
        </div>


        <nav className="cs-nav">

          <button
            className={`cs-nav-item ${
              activeSection === "command" ? "active" : ""
            }`}
            onClick={() => setActiveSection("command")}
          >
            <LayoutDashboard size={17} />
            Command Center
          </button>


          <button
            className={`cs-nav-item ${
              activeSection === "camera" ? "active" : ""
            }`}
            onClick={() => setActiveSection("camera")}
          >
            <Camera size={17} />
            Camera Intelligence
          </button>


          <button
            className={`cs-nav-item ${
              activeSection === "crowd" ? "active" : ""
            }`}
            onClick={() => setActiveSection("crowd")}
          >
            <Users size={17} />
            Crowd Analytics
          </button>


          <button
            className={`cs-nav-item ${
              activeSection === "risk" ? "active" : ""
            }`}
            onClick={() => setActiveSection("risk")}
          >
            <Map size={17} />
            Risk Map
          </button>


          <button
            className={`cs-nav-item ${
              activeSection === "routing" ? "active" : ""
            }`}
            onClick={() => setActiveSection("routing")}
          >
            <Route size={17} />
            Response Routing
          </button>

          <button
            className={`cs-nav-item ${
              activeSection === "alerts" ? "active" : ""
            }`}
            onClick={() => setActiveSection("alerts")}
          >
            <Siren size={17} />
            Alert Management
          </button>

        </nav>


        <div className="cs-nav-title">
          SYSTEM
        </div>


        <nav className="cs-nav">

          <button
            className={`cs-nav-item ${
              activeSection === "pipeline" ? "active" : ""
            }`}
            onClick={() => setActiveSection("pipeline")}
          >
            <Activity size={17} />
            AI Pipeline
          </button>


          <button
            className={`cs-nav-item ${
              activeSection === "database" ? "active" : ""
            }`}
            onClick={() => setActiveSection("database")}
          >
            <Database size={17} />
            Database
          </button>

        </nav>


        <div className="cs-sidebar-bottom">

          <div className="cs-oversight">

            <Eye size={17} />

            <div>
              <strong>
                Human Oversight
              </strong>

              <span>
                Required for decisions
              </span>
            </div>

          </div>


          <div className="cs-version">
            CrowdShield AI v1.0
          </div>

        </div>

      </aside>


      {/* MAIN */}

      <main className="cs-main">

        {/* TOP BAR */}

        <header className="cs-topbar">

          <div>

            <div className="cs-kicker">
              {currentSection.kicker}
            </div>

            <h1>
              {currentSection.title}
            </h1>

          </div>


          <div className="cs-top-actions">

            <div className="cs-connection">

              <span
                className={
                  connected
                    ? "cs-dot online"
                    : "cs-dot offline"
                }
              />

              {connected
                ? "BACKEND CONNECTED"
                : "BACKEND OFFLINE"}

            </div>


            <div className="cs-review">
              <Eye size={14} />
              HUMAN REVIEW REQUIRED
            </div>


            <button
              className="cs-refresh"
              onClick={() => loadData(true)}
            >
              <RefreshCw
                size={16}
                className={refreshing ? "cs-spin" : ""}
              />
            </button>

          </div>

        </header>


        {error && (
          <div className="cs-error">
            <AlertTriangle size={16} />
            {error}
          </div>
        )}


        {activeSection === "command" && (
          <>

            {/* HERO */}

            <section className="cs-hero">

              <div>

                <div className="cs-hero-label">
                  CROWD SAFETY INTELLIGENCE
                </div>

                <h2>
                  Situational awareness for
                  <span> high-density environments.</span>
                </h2>

                <p>
                  Monitor operational risk, crowd movement,
                  analytical alerts and response recommendations
                  through one centralized command interface.
                </p>

              </div>


              <div className="cs-system-pill">

                <Activity size={18} />

                <div>
                  <span>SYSTEM STATUS</span>

                  <strong>
                    {connected
                      ? "OPERATIONAL"
                      : "OFFLINE"}
                  </strong>
                </div>

              </div>

            </section>


            {/* KPI CARDS */}

            <section className="cs-kpis">

              <Kpi
                icon={<Gauge />}
                title="Operational Risk"
                value={format(riskScore)}
                suffix="/ 100"
                status={riskLevel}
                color={riskColor(riskLevel)}
              />


              <Kpi
                icon={<Users />}
                title="Crowd Load"
                value={peopleCount}
                suffix=" persons"
                status="TRACKED"
                color="#38bdf8"
              />


              <Kpi
                icon={<Bell />}
                title="Analytical Alerts"
                value={displayedAlerts.length}
                suffix=""
                status={
                  displayedAlerts.length
                    ? "ACTIVE"
                    : "CLEAR"
                }
                color={
                  displayedAlerts.length
                    ? "#fb923c"
                    : "#2dd4bf"
                }
              />


              <Kpi
                icon={<Camera />}
                title="Camera Source"
                value={camera.camera_id || "CAM-001"}
                suffix=""
                status={
                  camera.live_stream
                    ? camera.source_type === "rtsp"
                      ? "LIVE RTSP"
                      : "LIVE CAMERA"
                    : "RECORDED REPLAY"
                }
                color="#a78bfa"
              />

            </section>


            {/* MAIN PANELS */}

            <section className="cs-grid cs-main-grid">

              {/* CAMERA */}

              <Panel
                title="Camera Intelligence"
                subtitle="Production perception pipeline"
                icon={<Camera size={17} />}
                action={
                  camera.live_stream
                    ? camera.source_type === "rtsp"
                      ? "LIVE RTSP"
                      : "LIVE CAMERA"
                    : "RECORDED REPLAY"
                }
              >

                <div className="cs-camera">

                  <div className="cs-camera-grid" />

                  {camera.live_stream &&
                  camera.source_type === "rtsp" ? (

                    <iframe
                      title={`${camera.camera_name || camera.camera_id} live stream`}
                      src="http://127.0.0.1:8889/crowdshield/"
                      style={{
                        position: "absolute",
                        inset: 0,
                        width: "100%",
                        height: "100%",
                        border: "none",
                        zIndex: 2,
                        background: "#000",
                      }}
                      allow="autoplay; fullscreen"
                    />

                  ) : camera.live_stream &&
                    camera.source_type === "webcam" ? (

                    <img
                      src={`http://127.0.0.1:8000/api/cameras/${camera.camera_id}/frame?t=${Date.now()}`}
                      alt={`${camera.camera_name || camera.camera_id} live webcam`}
                      style={{
                        position: "absolute",
                        inset: 0,
                        width: "100%",
                        height: "100%",
                        objectFit: "cover",
                        zIndex: 2,
                        background: "#000",
                      }}
                    />

                  ) : (

                    <div className="cs-radar">
                      <div />
                      <div />
                      <div />
                      <span />
                    </div>

                  )}


                  <div className="cs-camera-title">
                    {camera.live_stream
                      ? "LIVE CAMERA ANALYTICS"
                      : "RECORDED CAMERA ANALYTICS"}
                  </div>


                  <div className="cs-camera-file">
                    {camera.live_stream
                      ? camera.camera_name ||
                        camera.camera_id ||
                        "Live Camera"
                      : camera.source_file ||
                        "people.mp4.mp4"}
                  </div>


                  <div className="cs-recorded">
                    <span />

                    {camera.live_stream
                      ? camera.source_type === "rtsp"
                        ? "LIVE RTSP STREAM"
                        : "LIVE CAMERA"
                      : "RECORDED REPLAY"}
                  </div>


                  <div className="cs-camera-stats">

                    <Stat
                      label="RESOLUTION"
                      value={`${camera.width || 1920} x ${
                        camera.height || 1080
                      }`}
                    />

                    <Stat
                      label="FPS"
                      value={camera.fps || 25}
                    />

                    <Stat
                      label="FRAMES"
                      value={camera.frame_count ?? 0}
                    />

                  </div>

                </div>


                <div className="cs-pipeline">

                  <Pipeline name="YOLO Detection" />
                  <Pipeline name="ByteTrack" />
                  <Pipeline name="Risk Engine" />
                  <Pipeline name="Response" />

                </div>

              </Panel>


              {/* RISK */}

              <Panel
                title="Operational Risk"
                subtitle="Current decision-support index"
                icon={<Gauge size={17} />}
              >

                <div className="cs-risk-box">

                  <div
                    className="cs-risk-ring"
                    style={{
                      "--risk": `${Math.min(
                        100,
                        riskScore
                      ) * 3.6}deg`,
                    }}
                  >

                    <div>

                      <small>
                        CURRENT RISK
                      </small>

                      <strong>
                        {format(riskScore)}
                      </strong>

                      <span>
                        / 100
                      </span>

                    </div>

                  </div>


                  <div
                    className="cs-risk-level"
                    style={{
                      color: riskColor(riskLevel),
                    }}
                  >
                    {riskLevel}
                  </div>

                </div>


                <div className="cs-risk-info">

                  <div>
                    <span>DOMINANT FACTOR</span>

                    <strong>
                      {liveRisk.dominant_risk_factor ||
                        camera?.latest_risk?.dominant_risk_factor ||
                        latest.dominant_risk_factor ||
                        "—"}
                    </strong>
                  </div>


                  <div>
                    <span>RESPONSE</span>

                    <strong>
                      {liveResponse.response_action ||
                        camera?.latest_response?.response_action ||
                        latest.response_action ||
                        "—"}
                    </strong>
                  </div>

                </div>


                <div className="cs-disclaimer">
                  <AlertTriangle size={13} />

                  Rule-based operational risk index.
                  Not a probability or validated emergency
                  prediction.
                </div>

              </Panel>

            </section>


            {/* ANALYTICS */}

            <section className="cs-grid cs-analytics-grid">

              <Panel
                title="Risk Timeline"
                subtitle={isSelectedCameraLive
                  ? `Live samples for ${selectedCameraId}`
                  : "Historical production pipeline windows"}
                icon={<Activity size={17} />}
                action={`${timelineData.length} ${isSelectedCameraLive ? "SAMPLES" : "WINDOWS"}`}
              >

                <div className="cs-chart">

                  {timelineData.length ? (

                    <ResponsiveContainer
                      width="100%"
                      height="100%"
                    >

                      <AreaChart
                        data={timelineData}
                      >

                        <defs>

                          <linearGradient
                            id="riskFill"
                            x1="0"
                            y1="0"
                            x2="0"
                            y2="1"
                          >

                            <stop
                              offset="0%"
                              stopColor="#38bdf8"
                              stopOpacity=".3"
                            />

                            <stop
                              offset="100%"
                              stopColor="#38bdf8"
                              stopOpacity="0"
                            />

                          </linearGradient>

                        </defs>


                        <CartesianGrid
                          stroke="#172033"
                          vertical={false}
                        />


                        <XAxis
                          dataKey="name"
                          stroke="#475569"
                          axisLine={false}
                          tickLine={false}
                          fontSize={9}
                        />


                        <YAxis
                          domain={[0, 100]}
                          stroke="#475569"
                          axisLine={false}
                          tickLine={false}
                          fontSize={9}
                        />


                        <Tooltip
                          contentStyle={{
                            background: "#07111f",
                            border: "1px solid #24344c",
                            borderRadius: "8px",
                            color: "#e2e8f0",
                          }}
                        />

                        <Area
                          type="monotone"
                          dataKey="risk"
                          stroke="#38bdf8"
                          strokeWidth={2}
                          fill="url(#riskFill)"
                        />

                      </AreaChart>

                    </ResponsiveContainer>

                  ) : (

                    <Empty
                      loading={loading}
                      text={isSelectedCameraLive ? "Waiting for live camera risk samples..." : "Waiting for production risk data..."}
                    />

                  )}

                </div>

              </Panel>


              {/* RISK DISTRIBUTION */}

              <Panel
                title="Risk Distribution"
                subtitle="Production pipeline windows"
                icon={<BarChart3 size={17} />}
              >

                <div className="cs-distribution">

                  {["CRITICAL", "HIGH", "MODERATE", "LOW"].map(
                    (level) => {

                      const count =
                        summary?.risk_distribution?.levels?.[
                          level
                        ] || 0;


                      const total =
                        summary?.window_count || 20;


                      return (
                        <div
                          className="cs-distribution-row"
                          key={level}
                        >

                          <div>
                            <i
                              style={{
                                background: riskColor(level),
                              }}
                            />

                            {level}
                          </div>


                          <span className="cs-bar">

                            <b
                              style={{
                                width: `${
                                  Math.min(
                                    100,
                                    (count / total) * 100
                                  )
                                }%`,
                                background:
                                  riskColor(level),
                              }}
                            />

                          </span>


                          <strong>
                            {count}
                          </strong>

                        </div>
                      );
                    }
                  )}

                </div>


                <div className="cs-mini-stats">

                  <Stat
                    label="WINDOWS"
                    value={summary?.window_count || 20}
                  />

                  <Stat
                    label="MEAN RISK"
                    value={format(
                      summary?.risk_statistics?.mean
                    )}
                  />

                  <Stat
                    label="MAX RISK"
                    value={format(
                      summary?.risk_statistics?.max
                    )}
                  />

                </div>

              </Panel>

            </section>


            {/* LOWER */}

            <section className="cs-grid cs-lower-grid">

              {/* ALERTS */}

              <Panel
                title="Operational Alerts"
                subtitle={isSelectedCameraLive
                  ? `Current signals from ${selectedCameraId}`
                  : "Historical rule-based analytical signals"}
                icon={<Siren size={17} />}
                action={`${displayedAlerts.length} ACTIVE`}
              >

                <div className="cs-alert-list">

                  {displayedAlerts.length ? (

                    displayedAlerts.slice(0, 7).map(
                      (alert, index) => (

                        <div
                          className="cs-alert"
                          key={`${alert.window_id}-${index}`}
                        >

                          <div
                            className="cs-alert-icon"
                            style={{
                              color: riskColor(
                                alert.operational_risk_level
                              ),
                              background: `${riskColor(
                                alert.operational_risk_level
                              )}12`,
                            }}
                          >
                            <AlertTriangle size={15} />
                          </div>


                          <div className="cs-alert-content">

                            <strong>
                              {isSelectedCameraLive
                                ? `${selectedCameraId} · LIVE`
                                : `Window ${alert.window_id}`}
                            </strong>

                            <span>
                              {alert.description ||
                                alert.operational_risk_reason ||
                                "Operational risk signal detected."}
                            </span>

                          </div>


                          <div className="cs-alert-score">

                            {format(
                              alert.operational_risk_score
                            )}

                            <small>
                              SCORE
                            </small>

                          </div>

                        </div>

                      )
                    )

                  ) : (

                    <Empty text={isSelectedCameraLive ? "No current alerts for this camera." : "No operational alerts."} />

                  )}

                </div>

              </Panel>


              {/* RESPONSE */}

              <Panel
                title="Response Intelligence"
                subtitle={isSelectedCameraLive
                  ? "Current camera response and historical action counts"
                  : "Historical response actions"}
                icon={<Zap size={17} />}
              >

                <div className="cs-risk-info" style={{ marginBottom: 16 }}>
                  <div>
                    <span>CURRENT ACTION</span>
                    <strong>
                      {isSelectedCameraLive
                        ? (liveResponse.response_action || "PENDING")
                        : (liveResponse.response_action || latest.response_action || "—")}
                    </strong>
                  </div>
                  <div>
                    <span>PRIORITY</span>
                    <strong>
                      {isSelectedCameraLive
                        ? (liveResponse.response_priority || "—")
                        : (liveResponse.response_priority || latest.response_priority || "—")}
                    </strong>
                  </div>
                </div>

                <p style={{ margin: "0 0 12px", color: "#94a3b8", fontSize: 12 }}>
                  {isSelectedCameraLive
                    ? (liveResponse.response_reason || "Waiting for a live response recommendation.")
                    : "Historical response-action distribution"}
                </p>

                <div className="cs-response-chart">

                  {responseDistribution.length ? (

                    <ResponsiveContainer
                      width="100%"
                      height="100%"
                    >

                      <BarChart
                        data={responseDistribution}
                        layout="vertical"
                        margin={{
                          left: 5,
                          right: 15,
                        }}
                      >

                        <CartesianGrid
                          stroke="#172033"
                          horizontal={false}
                        />


                        <XAxis
                          type="number"
                          stroke="#475569"
                          axisLine={false}
                          tickLine={false}
                          fontSize={9}
                        />


                        <YAxis
                          type="category"
                          dataKey="response_action"
                          width={135}
                          stroke="#64748b"
                          axisLine={false}
                          tickLine={false}
                          fontSize={8}
                        />


                        <Tooltip
                          contentStyle={{
                            background: "#07111f",
                            border: "1px solid #24344c",
                            borderRadius: "8px",
                          }}
                        />


                        <Bar
                          dataKey="count"
                          fill="#38bdf8"
                          radius={[0, 4, 4, 0]}
                        />

                      </BarChart>

                    </ResponsiveContainer>

                  ) : (

                    <Empty text="No response data." />

                  )}

                </div>


                <div className="cs-human-review">

                  <CheckCircle2 size={15} />

                  Human review required for all
                  operational response decisions.

                </div>

              </Panel>

            </section>


            {/* SYSTEM */}

            <section className="cs-grid cs-bottom-grid">

              <Panel
                title="System Health"
                subtitle="Production infrastructure"
                icon={<Activity size={17} />}
              >

                <div className="cs-health">

                  <Health
                    name="Backend API"
                    ok={connected}
                  />


                  <Health
                    name="Database"
                    ok={dbHealth?.status === "success"}
                  />


                  <Health
                    name="AI Pipeline"
                    ok={connected}
                  />


                  <Health
                    name="Camera Source"
                    ok={camera.status === "RUNNING"}
                  />

                </div>

              </Panel>


              <Panel
                title="Risk-Aware Routing"
                subtitle="Demonstration route engine"
                icon={<Route size={17} />}
              >

                <div className="cs-route">

                  <div className="cs-route-line">
                    <span />
                    <span />
                    <span />
                    <span />
                    <span />
                  </div>

                  <div className="cs-route-label start">
                    START
                  </div>

                  <div className="cs-route-label exit">
                    EXIT
                  </div>

                </div>


                <div className="cs-route-info">

                  <Stat
                    label="ROUTE POINTS"
                    value={
                      route?.route?.length || "—"
                    }
                  />

                  <Stat
                    label="TYPE"
                    value="SIMULATED A*"
                  />

                </div>


                <div className="cs-disclaimer">
                  <AlertTriangle size={13} />

                  Demonstration only — not safety-validated
                  for real-world emergency routing.

                </div>

              </Panel>

            </section>


            {/* FOOTER */}

            <footer className="cs-footer">

              <div>
                <Shield size={14} />
                CrowdShield AI
              </div>

              <span>
                Decision-support system · Human oversight required
              </span>

              <span>
                {lastUpdated
                  ? `Updated ${lastUpdated.toLocaleTimeString()}`
                  : "Waiting for sync"}
              </span>

            </footer>

          </>
        )}


        {activeSection === "camera" && (
          <CameraIntelligence
  cameras={cameras}
  crowd={crowd}
  selectedCameraId={selectedCameraId}
  setSelectedCameraId={setSelectedCameraId}
  cameraIntelligence={cameraIntelligence}
/>
        )}


        {activeSection === "crowd" && (
  <CrowdAnalytics
    selectedCameraId={selectedCameraId}
    cameraIntelligence={cameraIntelligence}
  />
)}


        {activeSection === "risk" && (
  <RiskMap
    selectedCameraId={selectedCameraId}
    cameraIntelligence={cameraIntelligence}
  />
)}


        {activeSection === "routing" && (
  <ResponseRouting
    selectedCameraId={selectedCameraId}
    cameraIntelligence={cameraIntelligence}
  />
)}


        {activeSection === "alerts" && (
          <AlertsManagement api={api} cameras={cameras} />
        )}

        {activeSection === "pipeline" && (
  <AIPipeline
    selectedCameraId={selectedCameraId}
    cameraIntelligence={cameraIntelligence}
  />
)}


       {activeSection === "database" && (
  <DatabaseView
    selectedCameraId={selectedCameraId}
    cameraIntelligence={cameraIntelligence}
  />
)}

      </main>

    </div>
  );
}


function Kpi({
  icon,
  title,
  value,
  suffix,
  status,
  color,
}) {

  return (
    <div className="cs-kpi">

      <div
        className="cs-kpi-icon"
        style={{ color }}
      >
        {icon}
      </div>

      <div>

        <span>
          {title}
        </span>

        <strong>
          {value}

          <small>
            {suffix}
          </small>
        </strong>

        <em style={{ color }}>
          <i
            style={{ background: color }}
          />

          {status}
        </em>

      </div>

    </div>
  );
}


function Panel({
  title,
  subtitle,
  icon,
  action,
  children,
}) {

  return (
    <div className="cs-panel">

      <div className="cs-panel-header">

        <div className="cs-panel-title">

          <div className="cs-panel-icon">
            {icon}
          </div>

          <div>
            <h3>{title}</h3>
            <p>{subtitle}</p>
          </div>

        </div>


        {action && (
          <span className="cs-panel-action">
            {action}
          </span>
        )}

      </div>


      <div className="cs-panel-body">
        {children}
      </div>

    </div>
  );
}


function Stat({ label, value }) {

  return (
    <div className="cs-stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}


function Pipeline({ name }) {

  return (
    <div className="cs-pipeline-item">
      <i />
      {name}
    </div>
  );
}


function Health({ name, ok }) {

  return (
    <div className="cs-health-item">

      {ok ? (
        <CheckCircle2
          size={17}
          color="#2dd4bf"
        />
      ) : (
        <XCircle
          size={17}
          color="#64748b"
        />
      )}

      <div>
        <strong>{name}</strong>

        <span>
          {ok ? "Operational" : "Unavailable"}
        </span>
      </div>

    </div>
  );
}


function Empty({ text, loading = false }) {

  return (
    <div className="cs-empty">

      {loading ? (
        <RefreshCw
          size={17}
          className="cs-spin"
        />
      ) : (
        <Activity size={17} />
      )}

      {text}

    </div>
  );
}


export default App;