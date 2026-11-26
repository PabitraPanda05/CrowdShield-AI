import { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Database,
  Layers,
  Server,
  ShieldCheck,
  Video,
} from "lucide-react";

import { api } from "../api";


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


export default function DatabaseView({
  selectedCameraId,
  cameraIntelligence,
}) {
  const [health, setHealth] = useState(null);
  const [summary, setSummary] = useState(null);
  const [cameras, setCameras] = useState([]);
  const [risk, setRisk] = useState([]);
  const [responses, setResponses] = useState([]);
  const [runs, setRuns] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


  async function loadDatabase() {
    try {
      setError("");

      const [
        healthResult,
        summaryResult,
        cameraResult,
        riskResult,
        responseResult,
        runsResult,
      ] = await Promise.all([
        api.databaseHealth(),
        api.databaseSummary(),
        api.databaseCameras(),
        api.databaseRisk(),
        api.databaseResponse(),
        api.databaseRuns(),
      ]);

      setHealth(healthResult || null);
      setSummary(summaryResult || null);
      setCameras(cameraResult?.data || []);
      setRisk(riskResult?.data || []);
      setResponses(responseResult?.data || []);
      setRuns(runsResult?.data || []);
    } catch (err) {
      console.error("Database API error:", err);
      setError("Unable to load database information.");
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadDatabase();

    const interval = setInterval(
      loadDatabase,
      10000
    );

    return () => clearInterval(interval);
  }, []);


  const liveCamera =
  cameraIntelligence || null;


const selectedCamera =
  liveCamera ||
  cameras.find(
    (camera) =>
      camera.camera_id === selectedCameraId
  ) ||
  null;


const currentRisk =
  liveCamera?.latest_risk || {};


const currentResponse =
  liveCamera?.latest_response || {};


  const latestRun =
    runs.length > 0
      ? runs[0]
      : null;


  if (loading) {
    return (
      <div className="cs-module">
        <div className="cs-module-placeholder">
          <Database size={30} />
          <h3>Loading Database</h3>
          <p>
            Loading SQLite database information...
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
          <Database size={28} />
        </div>

        <div>
          <div className="cs-module-kicker">
            DATA / SQLITE
          </div>

          <h2>Database</h2>

          <p>
            Production data storage, integrity and
            operational records.
          </p>
        </div>

        <div className="cs-module-status cs-status-ok">
          <CheckCircle2 size={13} />
          DATABASE HEALTHY
        </div>

      </div>


      {error && (
        <div className="cs-error">
          <AlertTriangle size={16} />
          {error}
        </div>
      )}


      {/* DATABASE SUMMARY */}

      <div className="cs-module-grid">

        <DatabaseStat
          icon={Database}
          label="DATABASE"
          value={
            health?.database
              ? health.database.toUpperCase()
              : "—"
          }
          sub="storage engine"
        />

        <DatabaseStat
          icon={CheckCircle2}
          label="INTEGRITY"
          value={
            health?.integrity
              ? health.integrity.toUpperCase()
              : "—"
          }
          sub="database check"
        />

        <DatabaseStat
          icon={Layers}
          label="RISK WINDOWS"
          value={summary?.risk_windows ?? "—"}
          sub="global stored windows"
        />

        <DatabaseStat
          icon={ShieldCheck}
          label="RESPONSES"
          value={
            summary?.response_decisions ?? "—"
          }
          sub="global stored decisions"
        />

        <DatabaseStat
          icon={Video}
          label="CAMERAS"
          value={summary?.cameras ?? "—"}
          sub="registered sources"
        />

        <DatabaseStat
          icon={Activity}
          label="PIPELINE RUNS"
          value={runs.length}
          sub="global stored runs"
        />

      </div>


      {/* SELECTED CAMERA DATABASE CONTEXT */}

      <div className="cs-module-card">

        <div className="cs-module-card-header">

          <div>
            <h3>
              Selected Camera Database Context
            </h3>

            <p>
              Live camera state from the selected
              production camera.
            </p>
          </div>

          <span className="cs-module-badge">
            {selectedCameraId || "NO CAMERA"}
          </span>

        </div>


        {selectedCamera ? (

          <div className="cs-module-two-column">

            <div className="cs-module-list">

              <InfoRow
                label="Camera"
                value={selectedCamera.camera_name}
              />

              <InfoRow
                label="Camera ID"
                value={selectedCamera.camera_id}
              />

              <InfoRow
                label="Source type"
                value={selectedCamera.source_type}
              />

              <InfoRow
                label="Status"
                value={
                  liveCamera?.status ||
                  selectedCamera.status
                }
              />

              <InfoRow
                label="Resolution"
                value={
                  liveCamera?.width &&
                  liveCamera?.height
                    ? `${liveCamera.width} × ${liveCamera.height}`
                    : selectedCamera.width &&
                      selectedCamera.height
                      ? `${selectedCamera.width} × ${selectedCamera.height}`
                      : "—"
                }
              />

              <InfoRow
                label="FPS"
                value={format(
                  liveCamera?.fps ??
                    selectedCamera.fps,
                  1
                )}
              />

              <InfoRow
                label="Frame count"
                value={
                  liveCamera?.frame_count ??
                  selectedCamera.frame_count ??
                  "—"
                }
              />

              <InfoRow
                label="Stream mode"
                value={
                  liveCamera?.live_stream
                    ? "LIVE"
                    : "RECORDED"
                }
              />

            </div>


            <div className="cs-module-list">

              <InfoRow
                label="Current people"
                value={
                  liveCamera?.latest_person_count ??
                  "—"
                }
              />

              <InfoRow
                label="Current risk"
                value={
                  currentRisk.operational_risk_score !==
                  undefined
                    ? format(
                        currentRisk.operational_risk_score,
                        2
                      )
                    : "—"
                }
              />

              <InfoRow
                label="Risk level"
                value={
                  currentRisk.operational_risk_level ||
                  "—"
                }
              />

              <InfoRow
                label="Dominant factor"
                value={
                  currentRisk.dominant_risk_factor ||
                  "—"
                }
              />

              <InfoRow
                label="Response"
                value={
                  currentResponse.response_action ||
                  "—"
                }
              />

              <InfoRow
                label="Priority"
                value={
                  currentResponse.response_priority ||
                  "—"
                }
              />

              <InfoRow
                label="Human review"
                value={
                  currentResponse.human_review_required
                    ? "REQUIRED"
                    : "NOT REQUIRED"
                }
              />

              <InfoRow
                label="Autonomous action"
                value={
                  currentResponse.autonomous_emergency_action
                    ? "ENABLED"
                    : "DISABLED"
                }
              />

            </div>

          </div>

        ) : (

          <div className="cs-empty">
            No selected camera is currently available.
          </div>

        )}

      </div>


      {/* DATABASE TABLES */}

      <div className="cs-module-card">

        <div className="cs-module-card-header">

          <div>
            <h3>Database Tables</h3>

            <p>
              Tables currently registered in SQLite.
            </p>
          </div>

          <span className="cs-module-badge">
            {health?.tables?.length || 0} TABLES
          </span>

        </div>


        <div className="cs-db-table-grid">

          {(health?.tables || []).map(
            (table) => (

              <div
                className="cs-db-table-item"
                key={table}
              >

                <Database size={15} />

                <span>
                  {table}
                </span>

                <CheckCircle2 size={13} />

              </div>

            )
          )}

        </div>

      </div>


      {/* CAMERA REGISTRY */}

      <div className="cs-module-two-column">

        <div className="cs-module-card">

          <div className="cs-module-card-header">

            <div>
              <h3>Camera Registry</h3>

              <p>
                Camera sources stored in the database.
              </p>
            </div>

          </div>


          <div className="cs-db-camera-list">

            {cameras.map(
              (camera) => {

                const isSelected =
                  camera.camera_id ===
                  selectedCameraId;

                return (
                  <div
                    className="cs-db-camera"
                    key={camera.camera_id}
                    style={
                      isSelected
                        ? {
                            borderColor:
                              "rgba(45, 212, 191, 0.45)",
                            background:
                              "rgba(45, 212, 191, 0.05)",
                          }
                        : undefined
                    }
                  >

                    <div className="cs-db-camera-icon">
                      <Video size={18} />
                    </div>

                    <div className="cs-db-camera-main">

                      <strong>
                        {camera.camera_name}
                      </strong>

                      <span>
                        {camera.camera_id}
                      </span>

                    </div>

                    <div className="cs-db-camera-status">

                      <span>
                        {isSelected
                          ? "SELECTED"
                          : camera.status}
                      </span>

                      <small>
                        {camera.width} × {camera.height}
                        {" · "}
                        {camera.fps} FPS
                      </small>

                    </div>

                  </div>
                );
              }
            )}

          </div>

        </div>


        {/* GLOBAL LATEST STATE */}

        <div className="cs-module-card">

          <div className="cs-module-card-header">

            <div>
              <h3>
                Latest Stored Operational State
              </h3>

              <p>
                Latest persisted SQLite risk and
                response record.
              </p>
            </div>

            {summary?.latest_state && (
              <RiskBadge
                level={
                  summary.latest_state.risk_level
                }
              />
            )}

          </div>


          <div className="cs-module-list">

            <InfoRow
              label="Scope"
              value="GLOBAL SQLITE RECORD"
            />

            <InfoRow
              label="Window"
              value={
                summary?.latest_state?.window_id
                  ? `W${summary.latest_state.window_id}`
                  : "—"
              }
            />

            <InfoRow
              label="Risk score"
              value={format(
                summary?.latest_state?.risk_score,
                2
              )}
            />

            <InfoRow
              label="Risk level"
              value={
                summary?.latest_state?.risk_level
              }
            />

            <InfoRow
              label="Response"
              value={
                summary?.latest_state?.response_action
              }
            />

            <InfoRow
              label="Priority"
              value={
                summary?.latest_state?.response_priority
              }
            />

            <InfoRow
              label="Human review"
              value={
                summary?.latest_state
                  ?.human_review_required
                  ? "REQUIRED"
                  : "NOT REQUIRED"
              }
            />

            <InfoRow
              label="Autonomous action"
              value={
                summary?.latest_state
                  ?.autonomous_emergency_action
                  ? "ENABLED"
                  : "DISABLED"
              }
            />

          </div>

        </div>

      </div>


      {/* GLOBAL RISK DATA */}

      <div className="cs-module-card">

        <div className="cs-module-card-header">

          <div>
            <h3>Stored Risk Windows</h3>

            <p>
              Global operational risk records
              persisted in SQLite. These records do
              not contain a camera_id mapping.
            </p>
          </div>

          <span className="cs-module-badge">
            {risk.length} RECORDS
          </span>

        </div>


        <div className="cs-db-table-wrap">

          <table className="cs-db-table">

            <thead>
              <tr>
                <th>SCOPE</th>
                <th>WINDOW</th>
                <th>PEOPLE</th>
                <th>CROWD</th>
                <th>MOVEMENT</th>
                <th>SPATIAL</th>
                <th>SCORE</th>
                <th>LEVEL</th>
                <th>DOMINANT FACTOR</th>
              </tr>
            </thead>

            <tbody>

              {risk.map(
                (item) => (

                  <tr key={item.window_id}>

                    <td>
                      GLOBAL
                    </td>

                    <td>
                      W{item.window_id}
                    </td>

                    <td>
                      {format(
                        item.average_people,
                        2
                      )}
                      {" / "}
                      {item.maximum_people}
                    </td>

                    <td>
                      {format(
                        item.crowd_load,
                        2
                      )}
                    </td>

                    <td>
                      {format(
                        item.movement_load,
                        2
                      )}
                    </td>

                    <td>
                      {format(
                        item.spatial_load,
                        2
                      )}
                    </td>

                    <td>
                      <strong>
                        {format(
                          item.operational_risk_score,
                          2
                        )}
                      </strong>
                    </td>

                    <td>
                      <RiskBadge
                        level={
                          item.operational_risk_level
                        }
                      />
                    </td>

                    <td>
                      {item.dominant_risk_factor}
                    </td>

                  </tr>

                )
              )}

            </tbody>

          </table>

        </div>

      </div>


      {/* GLOBAL RESPONSE DATA */}

      <div className="cs-module-card">

        <div className="cs-module-card-header">

          <div>
            <h3>Stored Response Decisions</h3>

            <p>
              Global human-reviewed operational
              response decisions persisted in SQLite.
            </p>
          </div>

          <span className="cs-module-badge">
            {responses.length} RECORDS
          </span>

        </div>


        <div className="cs-db-response-grid">

          {responses.map(
            (item) => (

              <div
                className="cs-db-response"
                key={item.window_id}
              >

                <div className="cs-db-response-top">

                  <strong>
                    W{item.window_id}
                  </strong>

                  <RiskBadge
                    level={
                      item.operational_risk_level
                    }
                  />

                </div>


                <div className="cs-db-response-score">
                  {format(
                    item.operational_risk_score,
                    2
                  )}
                </div>


                <div className="cs-db-response-action">
                  {item.response_action}
                </div>


                <div className="cs-db-response-signals">
                  {item.active_signals || "none"}
                </div>

              </div>

            )
          )}

        </div>

      </div>


      {/* GLOBAL PIPELINE RUN */}

      <div className="cs-module-card">

        <div className="cs-module-card-header">

          <div>
            <h3>Pipeline Run Registry</h3>

            <p>
              Production processing runs stored in
              SQLite. Camera association is not stored
              in this table.
            </p>
          </div>

          <span className="cs-module-badge">
            {runs.length} RUNS
          </span>

        </div>


        <div className="cs-db-run-card">

          {latestRun ? (

            <>

              <div className="cs-db-run-icon">
                <Server size={21} />
              </div>

              <div className="cs-db-run-main">

                <strong>
                  Run #{latestRun.run_id}
                </strong>

                <span>
                  {latestRun.source_name}
                </span>

              </div>

              <div className="cs-db-run-metrics">

                <div>
                  <span>FRAMES</span>
                  <strong>
                    {latestRun.processed_frames}
                  </strong>
                </div>

                <div>
                  <span>TRACKED</span>
                  <strong>
                    {latestRun.frames_with_tracks}
                  </strong>
                </div>

                <div>
                  <span>WINDOWS</span>
                  <strong>
                    {latestRun.processed_windows}
                  </strong>
                </div>

                <div>
                  <span>THROUGHPUT</span>
                  <strong>
                    {format(
                      latestRun.throughput_fps,
                      2
                    )} FPS
                  </strong>
                </div>

                <div>
                  <span>STATUS</span>
                  <strong className="cs-db-success">
                    {latestRun.status}
                  </strong>
                </div>

              </div>

            </>

          ) : (

            <div className="cs-empty">
              No pipeline runs stored.
            </div>

          )}

        </div>

      </div>


      {/* STORAGE / SAFETY */}

      <div className="cs-module-two-column">

        <div className="cs-module-card">

          <div className="cs-module-card-header">

            <div>
              <h3>Storage Information</h3>

              <p>
                Database integrity and source
                information.
              </p>
            </div>

          </div>


          <div className="cs-module-list">

            <InfoRow
              label="Engine"
              value={health?.database}
            />

            <InfoRow
              label="Integrity"
              value={health?.integrity}
            />

            <InfoRow
              label="Tables"
              value={health?.tables?.length}
            />

            <InfoRow
              label="Global risk records"
              value={risk.length}
            />

            <InfoRow
              label="Global response records"
              value={responses.length}
            />

            <InfoRow
              label="Camera records"
              value={cameras.length}
            />

          </div>

        </div>


        <div className="cs-module-card">

          <div className="cs-module-card-header">

            <div>
              <h3>Operational Safety State</h3>

              <p>
                Current selected-camera state and
                global database safeguards.
              </p>
            </div>

          </div>


          <div className="cs-db-safety">

            <SafetyRow
              label="Human review"
              value={
                currentResponse.human_review_required
                  ? "REQUIRED"
                  : "NOT REQUIRED"
              }
              safe
            />

            <SafetyRow
              label="Autonomous emergency action"
              value={
                currentResponse.autonomous_emergency_action
                  ? "ENABLED"
                  : "DISABLED"
              }
              safe
            />

            <SafetyRow
              label="Selected camera mode"
              value={
                liveCamera?.status ||
                selectedCamera?.status ||
                "—"
              }
            />

            <SafetyRow
              label="Selected camera risk"
              value={
                currentRisk.operational_risk_level ||
                "—"
              }
            />

            <SafetyRow
              label="Global pipeline status"
              value={
                latestRun?.status ||
                "—"
              }
              safe
            />

          </div>

        </div>

      </div>


      {/* DISCLAIMER */}

      <div className="cs-module-disclaimer">

        <AlertTriangle size={15} />

        <div>

          <strong>
            Database interpretation
          </strong>

          <span>
            Camera registry information is stored
            per camera. Live selected-camera risk and
            response values come from the active camera
            intelligence service. Historical risk windows,
            response decisions and pipeline runs are
            displayed as GLOBAL SQLite records because
            those tables do not contain a reliable
            camera_id mapping. Risk values represent the
            rule-based operational risk index used for
            decision support. They are not probability
            estimates or validated emergency predictions.
            Human review remains required and autonomous
            emergency action is disabled.
          </span>

        </div>

      </div>

    </div>
  );
}


function DatabaseStat({
  icon: Icon,
  label,
  value,
  sub,
}) {
  return (
    <div className="cs-module-stat">

      <div className="cs-module-stat-icon">
        <Icon size={19} />
      </div>

      <span>{label}</span>

      <strong>{value}</strong>

      <small>{sub}</small>

    </div>
  );
}


function InfoRow({ label, value }) {
  return (
    <div className="cs-module-list-row">
      <span>{label}</span>
      <strong>{value ?? "—"}</strong>
    </div>
  );
}


function SafetyRow({
  label,
  value,
  safe = false,
}) {
  return (
    <div className="cs-db-safety-row">

      <div className="cs-db-safety-icon">
        <CheckCircle2 size={16} />
      </div>

      <div>
        <span>{label}</span>

        <strong
          className={safe ? "cs-health-safe" : ""}
        >
          {value}
        </strong>
      </div>

    </div>
  );
}