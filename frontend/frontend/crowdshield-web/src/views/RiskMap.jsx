import { useEffect, useMemo, useState } from "react";

import {
  AlertTriangle,
  Activity,
  Gauge,
  Map,
  ShieldAlert,
  TrendingUp,
} from "lucide-react";

import {
  Area,
  AreaChart,
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


function riskColor(level) {
  const value = String(level || "").toUpperCase();

  if (value === "CRITICAL") return "#fb7185";
  if (value === "HIGH") return "#fb923c";
  if (value === "MODERATE") return "#facc15";
  if (value === "LOW") return "#2dd4bf";

  return "#64748b";
}


function RiskBadge({ level }) {
  const color = riskColor(level);

  return (
    <span
      className="cs-risk-badge"
      style={{
        color,
        borderColor: `${color}35`,
        background: `${color}0d`,
      }}
    >
      {level || "UNKNOWN"}
    </span>
  );
}


export default function RiskMap({
  selectedCameraId,
  cameraIntelligence,
}) {
  const [riskHistory, setRiskHistory] = useState([]);
  const [selectedSample, setSelectedSample] = useState(null);


  /*
   * Build a rolling camera-specific risk history.
   *
   * We intentionally do not use the old global
   * riskTimeline() endpoint because those historical
   * records do not contain camera_id.
   */
  useEffect(() => {
    if (!cameraIntelligence) {
      return;
    }


    const frame =
      cameraIntelligence.latest_frame || {};

    const risk =
      cameraIntelligence.latest_risk || {};


    const frameNumber = Number(
      frame.frame_number ?? 0
    );


    const timestamp = Number(
      frame.timestamp_seconds ?? 0
    );


    const riskScore = Number(
      risk.operational_risk_score ?? 0
    );


    if (
      !Number.isFinite(frameNumber) ||
      frameNumber <= 0
    ) {
      return;
    }


    const sample = {
      frameNumber,
      timestamp,
      score: riskScore,

      level:
        risk.operational_risk_level ||
        "UNKNOWN",

      dominantFactor:
        risk.dominant_risk_factor ||
        "—",

      reason:
        risk.operational_risk_reason ||
        "—",

      crowdLoad:
        Number(risk.crowd_load ?? 0),

      movementLoad:
        Number(risk.movement_load ?? 0),

      movementEvent:
        Number(risk.movement_event_signal ?? 0),

      spatialLoad:
        Number(risk.spatial_load ?? 0),

      growthLoad:
        Number(risk.growth_load ?? 0),

      persistenceLoad:
        Number(risk.persistence_load ?? 0),

      averagePeople:
        Number(risk.average_people ?? 0),

      maximumPeople:
        Number(risk.maximum_people ?? 0),
    };


    setRiskHistory((previous) => {
      const existingIndex =
        previous.findIndex(
          (item) =>
            item.frameNumber ===
            sample.frameNumber
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
   * Reset the rolling risk history whenever the
   * selected camera changes.
   */
  useEffect(() => {
    setRiskHistory([]);
    setSelectedSample(null);
  }, [selectedCameraId]);


  const latestRisk =
    cameraIntelligence?.latest_risk || {};


  const latestFrame =
    cameraIntelligence?.latest_frame || {};


  const currentRisk =
    Number(
      latestRisk.operational_risk_score ?? 0
    );


  const currentLevel =
    latestRisk.operational_risk_level ||
    "UNKNOWN";


  const currentFactor =
    latestRisk.dominant_risk_factor ||
    "—";


  const currentReason =
    latestRisk.operational_risk_reason ||
    "—";


  const statistics = useMemo(() => {
    if (!riskHistory.length) {
      return {
        mean: currentRisk,
        minimum: currentRisk,
        maximum: currentRisk,
        high: currentLevel === "HIGH" ? 1 : 0,
        moderate:
          currentLevel === "MODERATE" ? 1 : 0,
        critical:
          currentLevel === "CRITICAL" ? 1 : 0,
        low:
          currentLevel === "LOW" ? 1 : 0,
      };
    }


    const scores =
      riskHistory.map(
        (item) =>
          Number(item.score || 0)
      );


    return {
      mean:
        scores.reduce(
          (sum, value) =>
            sum + value,
          0
        ) / scores.length,

      minimum:
        Math.min(...scores),

      maximum:
        Math.max(...scores),

      high:
        riskHistory.filter(
          (item) =>
            item.level === "HIGH"
        ).length,

      moderate:
        riskHistory.filter(
          (item) =>
            item.level === "MODERATE"
        ).length,

      critical:
        riskHistory.filter(
          (item) =>
            item.level === "CRITICAL"
        ).length,

      low:
        riskHistory.filter(
          (item) =>
            item.level === "LOW"
        ).length,
    };

  }, [
    riskHistory,
    currentRisk,
    currentLevel,
  ]);


  const chartData = useMemo(() => {
    return riskHistory.map(
      (item, index) => ({
        name:
          item.timestamp > 0
            ? `${item.timestamp.toFixed(1)}s`
            : `S${index + 1}`,

        score:
          Number(item.score || 0),

        level:
          item.level,
      })
    );
  }, [riskHistory]);


  const highestRiskSample = useMemo(() => {
    if (!riskHistory.length) {
      return null;
    }


    return riskHistory.reduce(
      (highest, current) =>
        Number(current.score || 0) >
        Number(highest.score || 0)
          ? current
          : highest
    );
  }, [riskHistory]);


  /*
   * If the currently selected sample disappears because
   * the rolling history moves forward, keep the latest
   * available sample selected.
   */
  useEffect(() => {
    if (!selectedSample && highestRiskSample) {
      setSelectedSample(highestRiskSample);
    }
  }, [
    highestRiskSample,
    selectedSample,
  ]);


  if (!selectedCameraId) {
    return (
      <div className="cs-module">

        <div className="cs-module-placeholder">

          <Map size={30} />

          <h3>
            Risk Map
          </h3>

          <p>
            Select a camera to view camera-specific
            operational risk.
          </p>

        </div>

      </div>
    );
  }


  return (
    <div className="cs-module">

      {/* HERO */}

      <div className="cs-module-hero">

        <div className="cs-module-icon">
          <Map size={28} />
        </div>

        <div>

          <div className="cs-module-kicker">
            OPERATIONS / RISK MAP
          </div>

          <h2>
            Risk Map
          </h2>

          <p>
            Live operational-risk analysis for selected
            camera{" "}
            <strong>
              {selectedCameraId}
            </strong>
            .
          </p>

        </div>

        <div className="cs-module-status">

          <Activity size={13} />

          CAMERA RISK

        </div>

      </div>


      {/* CAMERA STATUS */}

      <div className="cs-module-card">

        <div className="cs-module-card-header">

          <div>

            <h3>
              Selected Camera Risk
            </h3>

            <p>
              Current operational-risk state from the
              production AI pipeline.
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
                    Current Risk
                  </strong>

                  <span>
                    Operational risk score
                  </span>

                </div>

                <div className="cs-module-list-value">

                  <strong>
                    {format(currentRisk)}
                  </strong>

                  <span>
                    <RiskBadge
                      level={currentLevel}
                    />
                  </span>

                </div>

              </div>

            </div>


            <div>

              <div className="cs-module-list-row">

                <div>

                  <strong>
                    Dominant Factor
                  </strong>

                  <span>
                    Current risk driver
                  </span>

                </div>

                <div className="cs-module-list-value">

                  <strong>
                    {currentFactor}
                  </strong>

                  <span>
                    live
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

          </div>

        )}

      </div>


      {/* SUMMARY */}

      <div className="cs-module-grid">

        <div className="cs-module-stat">

          <div className="cs-module-stat-icon">
            <Gauge size={19} />
          </div>

          <span>
            CURRENT RISK
          </span>

          <strong>
            {format(currentRisk, 1)}
          </strong>

          <small>
            {currentLevel}
          </small>

        </div>


        <div className="cs-module-stat">

          <div className="cs-module-stat-icon">
            <TrendingUp size={19} />
          </div>

          <span>
            MAXIMUM RISK
          </span>

          <strong>
            {format(
              statistics.maximum,
              1
            )}
          </strong>

          <small>
            rolling camera history
          </small>

        </div>


        <div className="cs-module-stat">

          <div className="cs-module-stat-icon">
            <ShieldAlert size={19} />
          </div>

          <span>
            HIGH
          </span>

          <strong>
            {statistics.high}
          </strong>

          <small>
            rolling samples
          </small>

        </div>


        <div className="cs-module-stat">

          <div className="cs-module-stat-icon">
            <AlertTriangle size={19} />
          </div>

          <span>
            CRITICAL
          </span>

          <strong>
            {statistics.critical}
          </strong>

          <small>
            rolling samples
          </small>

        </div>


        <div className="cs-module-stat">

          <div className="cs-module-stat-icon">
            <Activity size={19} />
          </div>

          <span>
            MODERATE
          </span>

          <strong>
            {statistics.moderate}
          </strong>

          <small>
            rolling samples
          </small>

        </div>


        <div className="cs-module-stat">

          <div className="cs-module-stat-icon">
            <Map size={19} />
          </div>

          <span>
            SAMPLES
          </span>

          <strong>
            {riskHistory.length}
          </strong>

          <small>
            live camera history
          </small>

        </div>

      </div>


      {/* LIVE RISK TIMELINE */}

      <div className="cs-module-card">

        <div className="cs-module-card-header">

          <div>

            <h3>
              Live Operational Risk Timeline
            </h3>

            <p>
              Rolling risk samples captured from{" "}
              {selectedCameraId}.
            </p>

          </div>

          <span className="cs-module-badge">

            {riskHistory.length} SAMPLES

          </span>

        </div>


        <div className="cs-module-chart cs-risk-chart">

          {chartData.length ? (

            <ResponsiveContainer
              width="100%"
              height={350}
            >

              <AreaChart
                data={chartData}
              >

                <defs>

                  <linearGradient
                    id="cameraRiskGradient"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >

                    <stop
                      offset="5%"
                      stopColor="#fb923c"
                      stopOpacity={0.30}
                    />

                    <stop
                      offset="95%"
                      stopColor="#fb923c"
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
                  tick={{ fontSize: 10 }}
                />


                <YAxis
                  domain={[0, 100]}
                  stroke="#64748b"
                  tick={{ fontSize: 10 }}
                />


                <Tooltip
                  contentStyle={{
                    background: "#07111f",
                    border: "1px solid #1e293b",
                    borderRadius: "10px",
                  }}

                  formatter={(value) => [
                    `${Number(value).toFixed(2)}`,
                    "Risk Score",
                  ]}
                />


                <Area
                  type="monotone"
                  dataKey="score"
                  stroke="#fb923c"
                  fill="url(#cameraRiskGradient)"
                  strokeWidth={2.5}
                  activeDot={{
                    r: 5,
                  }}
                />

              </AreaChart>

            </ResponsiveContainer>

          ) : (

            <div className="cs-empty">

              <Activity
                size={17}
                className="cs-spin"
              />

              Waiting for live camera risk samples...

            </div>

          )}

        </div>

      </div>


      {/* WINDOW / SAMPLE ANALYSIS */}

      <div className="cs-module-two-column">

        {/* HIGHEST RISK SAMPLE */}

        <div className="cs-module-card">

          <div className="cs-module-card-header">

            <div>

              <h3>
                Highest-Risk Sample
              </h3>

              <p>
                Maximum risk observed in the rolling
                camera history.
              </p>

            </div>

            {highestRiskSample && (
              <RiskBadge
                level={
                  highestRiskSample.level
                }
              />
            )}

          </div>


          {highestRiskSample ? (

            <div className="cs-risk-detail">

              <div className="cs-risk-score-large">

                {format(
                  highestRiskSample.score,
                  2
                )}

                <span>
                  operational risk index
                </span>

              </div>


              <div className="cs-module-list">

                <div className="cs-module-list-row">

                  <span>
                    Frame
                  </span>

                  <strong>
                    {highestRiskSample.frameNumber}
                  </strong>

                </div>


                <div className="cs-module-list-row">

                  <span>
                    Time
                  </span>

                  <strong>
                    {format(
                      highestRiskSample.timestamp,
                      2
                    )}s
                  </strong>

                </div>


                <div className="cs-module-list-row">

                  <span>
                    Dominant factor
                  </span>

                  <strong>
                    {highestRiskSample.dominantFactor}
                  </strong>

                </div>


                <div className="cs-module-list-row">

                  <span>
                    Risk level
                  </span>

                  <strong>

                    <RiskBadge
                      level={
                        highestRiskSample.level
                      }
                    />

                  </strong>

                </div>

              </div>


              <div className="cs-risk-reason">

                <AlertTriangle size={14} />

                <span>
                  {highestRiskSample.reason}
                </span>

              </div>

            </div>

          ) : (

            <div className="cs-empty">
              No live risk samples available.
            </div>

          )}

        </div>


        {/* DISTRIBUTION */}

        <div className="cs-module-card">

          <div className="cs-module-card-header">

            <div>

              <h3>
                Risk Distribution
              </h3>

              <p>
                Classification of the selected camera's
                rolling samples.
              </p>

            </div>

          </div>


          <div className="cs-risk-distribution">

            <RiskDistributionRow
              label="CRITICAL"
              count={statistics.critical}
              total={riskHistory.length}
            />

            <RiskDistributionRow
              label="HIGH"
              count={statistics.high}
              total={riskHistory.length}
            />

            <RiskDistributionRow
              label="MODERATE"
              count={statistics.moderate}
              total={riskHistory.length}
            />

            <RiskDistributionRow
              label="LOW"
              count={statistics.low}
              total={riskHistory.length}
            />

          </div>

        </div>

      </div>


      {/* RISK SAMPLE TABLE */}

      <div className="cs-module-card">

        <div className="cs-module-card-header">

          <div>

            <h3>
              Live Risk Samples
            </h3>

            <p>
              Select a sample to inspect its camera-specific
              operational-risk reason.
            </p>

          </div>

        </div>


        <div className="cs-risk-table-wrap">

          <table className="cs-risk-table">

            <thead>

              <tr>
                <th>SAMPLE</th>
                <th>TIME</th>
                <th>SCORE</th>
                <th>LEVEL</th>
                <th>DOMINANT FACTOR</th>
                <th>REASON</th>
              </tr>

            </thead>


            <tbody>

              {riskHistory.length === 0 ? (

                <tr>

                  <td
                    colSpan="6"
                    style={{
                      textAlign: "center",
                    }}
                  >
                    Waiting for live risk samples...

                  </td>

                </tr>

              ) : (

                [...riskHistory]
                  .reverse()
                  .map((item) => (

                    <tr
                      key={item.frameNumber}
                      className={
                        selectedSample?.frameNumber ===
                        item.frameNumber
                          ? "selected"
                          : ""
                      }
                      onClick={() =>
                        setSelectedSample(item)
                      }
                    >

                      <td>
                        F{item.frameNumber}
                      </td>


                      <td>
                        {format(
                          item.timestamp,
                          1
                        )}s
                      </td>


                      <td>

                        <strong>
                          {format(
                            item.score,
                            2
                          )}
                        </strong>

                      </td>


                      <td>

                        <RiskBadge
                          level={
                            item.level
                          }
                        />

                      </td>


                      <td>
                        {item.dominantFactor}
                      </td>


                      <td>
                        {item.reason}
                      </td>

                    </tr>

                  ))

              )}

            </tbody>

          </table>

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
                {format(
                  Number(
                    latestRisk.crowd_load ?? 0
                  ) * 100,
                  1
                )}%
              </small>

            </div>

          </div>


          <div className="cs-flow-card">

            <div className="cs-flow-icon">
              <Activity size={18} />
            </div>

            <div className="cs-flow-content">

              <strong>
                Movement Load
              </strong>

              <span>
                Current normalized signal
              </span>

              <small>
                {format(
                  Number(
                    latestRisk.movement_load ?? 0
                  ) * 100,
                  1
                )}%
              </small>

            </div>

          </div>


          <div className="cs-flow-card">

            <div className="cs-flow-icon">
              <ShieldAlert size={18} />
            </div>

            <div className="cs-flow-content">

              <strong>
                Spatial Load
              </strong>

              <span>
                Current spatial signal
              </span>

              <small>
                {format(
                  Number(
                    latestRisk.spatial_load ?? 0
                  ) * 100,
                  1
                )}%
              </small>

            </div>

          </div>


          <div className="cs-flow-card">

            <div className="cs-flow-icon">
              <TrendingUp size={18} />
            </div>

            <div className="cs-flow-content">

              <strong>
                Growth Load
              </strong>

              <span>
                Current crowd-growth signal
              </span>

              <small>
                {format(
                  Number(
                    latestRisk.growth_load ?? 0
                  ) * 100,
                  1
                )}%
              </small>

            </div>

          </div>

        </div>


        <div className="cs-module-note">

          <Activity size={14} />

          Risk values are taken directly from the selected
          camera's production intelligence. Risk weights and
          thresholds are unchanged.

        </div>

      </div>


      {/* DISCLAIMER */}

      <div className="cs-module-disclaimer">

        <AlertTriangle size={15} />

        <div>

          <strong>
            Decision-support interpretation
          </strong>

          <span>
            This is a rule-based operational risk index
            for decision support. It is not a probability,
            not a validated emergency prediction, and not
            an autonomous emergency decision. Human review
            is required for operational response.

          </span>

        </div>

      </div>

    </div>
  );
}


function RiskDistributionRow({
  label,
  count,
  total,
}) {
  const percentage =
    total > 0
      ? (count / total) * 100
      : 0;

  const color = riskColor(label);


  return (
    <div className="cs-risk-distribution-row">

      <div className="cs-risk-distribution-label">

        <span
          style={{
            background: color,
          }}
        />

        <strong>
          {label}
        </strong>

      </div>


      <div className="cs-risk-bar">

        <div
          style={{
            width: `${percentage}%`,
            background: color,
          }}
        />

      </div>


      <strong className="cs-risk-count">
        {count}
      </strong>

    </div>
  );
}