import { useEffect, useState } from "react";

import {
  Activity,
  AlertTriangle,
  BrainCircuit,
  Camera,
  CheckCircle2,
  Database,
  Gauge,
  Layers,
  PlayCircle,
  Route,
  ShieldCheck,
  Target,
  Timer,
  Video,
  Users,
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


const pipelineStages = [
  {
    title: "Camera Source",
    subtitle: "Selected camera input",
    icon: Video,
  },
  {
    title: "YOLO Detection",
    subtitle: "Person detection",
    icon: Target,
  },
  {
    title: "ByteTrack",
    subtitle: "Multi-object tracking",
    icon: Activity,
  },
  {
    title: "Crowd Intelligence",
    subtitle: "Density and movement",
    icon: BrainCircuit,
  },
  {
    title: "Risk Features",
    subtitle: "Explainable features",
    icon: Gauge,
  },
  {
    title: "Temporal Aggregation",
    subtitle: "Window-level analysis",
    icon: Timer,
  },
  {
    title: "Operational Risk",
    subtitle: "Rule-based risk index",
    icon: ShieldCheck,
  },
  {
    title: "Response Decision",
    subtitle: "Human-reviewed action",
    icon: Route,
  },
];


export default function AIPipeline({
  selectedCameraId,
  cameraIntelligence,
}) {
  const [health, setHealth] = useState(null);
  const [summary, setSummary] = useState(null);
  const [runs, setRuns] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


  /*
   * Database information is intentionally kept separate
   * from selected-camera intelligence.
   *
   * The SQLite run records are global production records
   * and do not contain a reliable camera_id mapping.
   */
  async function loadDatabaseData() {
    try {
      setError("");

      const [
        healthResult,
        summaryResult,
        runsResult,
      ] = await Promise.all([
        api.databaseHealth(),
        api.databaseSummary(),
        api.databaseRuns(),
      ]);

      setHealth(healthResult);
      setSummary(summaryResult);
      setRuns(runsResult?.data || []);

    } catch (err) {
      console.error(
        "AI Pipeline database API error:",
        err
      );

      setError(
        "Unable to load AI pipeline database data."
      );

    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadDatabaseData();

    const interval = setInterval(
      loadDatabaseData,
      10000
    );

    return () => clearInterval(interval);
  }, []);


  const latestRun =
    runs.length > 0
      ? runs[runs.length - 1]
      : null;


  const latestFrame =
    cameraIntelligence?.latest_frame || {};


  const latestCrowd =
    latestFrame.crowd || {};


  const latestRisk =
    cameraIntelligence?.latest_risk || {};


  const latestResponse =
    cameraIntelligence?.latest_response || {};


  const personCount =
    Number(
      cameraIntelligence?.latest_person_count ??
        latestFrame.person_count ??
        0
    );


  const detectionCount =
    Number(
      latestFrame.detection_count ?? 0
    );


  const trackCount =
    Number(
      latestFrame.track_count ?? 0
    );


  const riskScore =
    Number(
      latestRisk.operational_risk_score ?? 0
    );


  const riskLevel =
    latestRisk.operational_risk_level ||
    "UNKNOWN";


  const pipelineStatus =
    cameraIntelligence?.status ||
    "WAITING";


  if (!selectedCameraId) {
    return (
      <div className="cs-module">

        <div className="cs-module-placeholder">

          <BrainCircuit size={30} />

          <h3>
            AI Pipeline
          </h3>

          <p>
            Select a camera to view its live AI
            processing pipeline.
          </p>

        </div>

      </div>
    );
  }


  if (loading) {
    return (
      <div className="cs-module">

        <div className="cs-module-placeholder">

          <BrainCircuit size={30} />

          <h3>
            Loading AI Pipeline
          </h3>

          <p>
            Loading production pipeline status...
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
          <BrainCircuit size={28} />
        </div>


        <div>

          <div className="cs-module-kicker">
            AI / PRODUCTION PIPELINE
          </div>

          <h2>
            AI Pipeline
          </h2>

          <p>
            Live perception, tracking, crowd intelligence,
            risk processing and response workflow for{" "}
            <strong>
              {selectedCameraId}
            </strong>
            .
          </p>

        </div>


        <div className="cs-module-status cs-status-ok">

          <CheckCircle2 size={13} />

          {pipelineStatus === "RUNNING"
            ? "PIPELINE ACTIVE"
            : pipelineStatus}

        </div>

      </div>


      {error && (
        <div className="cs-error">

          <AlertTriangle size={16} />

          {error}

        </div>
      )}


      {/* SELECTED CAMERA PIPELINE STATUS */}

      <div className="cs-module-card">

        <div className="cs-module-card-header">

          <div>

            <h3>
              Selected Camera Pipeline
            </h3>

            <p>
              Current live processing state from the
              production AI pipeline.
            </p>

          </div>


          <span className="cs-module-badge">

            {pipelineStatus}

          </span>

        </div>


        <div className="cs-module-grid">

          <PipelineStat
            icon={Camera}
            label="CAMERA"
            value={selectedCameraId}
            sub={
              cameraIntelligence?.camera_name ||
              "selected camera"
            }
          />


          <PipelineStat
            icon={Users}
            label="PEOPLE"
            value={personCount}
            sub="latest processed frame"
          />


          <PipelineStat
            icon={Target}
            label="DETECTIONS"
            value={detectionCount}
            sub="latest frame"
          />


          <PipelineStat
            icon={Activity}
            label="TRACKS"
            value={trackCount}
            sub="active tracked objects"
          />


          <PipelineStat
            icon={Gauge}
            label="RISK"
            value={format(riskScore, 1)}
            sub={riskLevel}
          />


          <PipelineStat
            icon={Route}
            label="RESPONSE"
            value={
              latestResponse.response_action ||
              "—"
            }
            sub={
              latestResponse.response_priority ||
              "—"
            }
          />

        </div>

      </div>


      {/* PIPELINE FLOW */}

      <div className="cs-module-card">

        <div className="cs-module-card-header">

          <div>

            <h3>
              Production Processing Flow
            </h3>

            <p>
              Current CrowdShield AI processing
              architecture for the selected camera.
            </p>

          </div>


          <span className="cs-module-badge">

            {pipelineStatus}

          </span>

        </div>


        <div className="cs-pipeline-flow">

          {pipelineStages.map(
            (stage, index) => {

              const Icon =
                stage.icon;


              return (
                <div
                  className="cs-pipeline-stage-wrapper"
                  key={stage.title}
                >

                  <div className="cs-pipeline-stage">

                    <div className="cs-pipeline-stage-icon">

                      <Icon size={19} />

                    </div>


                    <strong>
                      {stage.title}
                    </strong>


                    <span>
                      {stage.subtitle}
                    </span>


                    <div className="cs-pipeline-stage-status">

                      <CheckCircle2 size={11} />

                      ACTIVE

                    </div>

                  </div>


                  {index <
                    pipelineStages.length - 1 && (
                    <div className="cs-pipeline-arrow">
                      →
                    </div>
                  )}

                </div>
              );
            }
          )}

        </div>

      </div>


      {/* LIVE CAMERA OUTPUTS */}

      <div className="cs-module-two-column">

        {/* LATEST FRAME */}

        <div className="cs-module-card">

          <div className="cs-module-card-header">

            <div>

              <h3>
                Latest Camera Output
              </h3>

              <p>
                Most recent frame processed by the
                selected camera pipeline.
              </p>

            </div>

          </div>


          <div className="cs-module-list">

            <InfoRow
              label="Camera"
              value={
                cameraIntelligence?.camera_name ||
                selectedCameraId
              }
            />


            <InfoRow
              label="Source type"
              value={
                cameraIntelligence?.source_type
              }
            />


            <InfoRow
              label="Frame number"
              value={
                latestFrame.frame_number
              }
            />


            <InfoRow
              label="Timestamp"
              value={
                latestFrame.timestamp_seconds !==
                undefined
                  ? `${format(
                      latestFrame.timestamp_seconds,
                      2
                    )}s`
                  : undefined
              }
            />


            <InfoRow
              label="Person count"
              value={
                latestFrame.person_count
              }
            />


            <InfoRow
              label="Detection count"
              value={
                latestFrame.detection_count
              }
            />


            <InfoRow
              label="Track count"
              value={
                latestFrame.track_count
              }
            />

          </div>

        </div>


        {/* LIVE RISK OUTPUT */}

        <div className="cs-module-card">

          <div className="cs-module-card-header">

            <div>

              <h3>
                Live AI Decision Output
              </h3>

              <p>
                Current risk and response generated
                for the selected camera.
              </p>

            </div>

          </div>


          <div className="cs-module-list">

            <InfoRow
              label="Operational risk"
              value={
                format(
                  riskScore,
                  2
                )
              }
            />


            <InfoRow
              label="Risk level"
              value={
                riskLevel
              }
            />


            <InfoRow
              label="Dominant factor"
              value={
                latestRisk.dominant_risk_factor
              }
            />


            <InfoRow
              label="Movement event"
              value={
                Number(
                  latestRisk.movement_event_signal ??
                    0
                ) > 0
                  ? "ACTIVE"
                  : "CLEAR"
              }
            />


            <InfoRow
              label="Response"
              value={
                latestResponse.response_action
              }
            />


            <InfoRow
              label="Priority"
              value={
                latestResponse.response_priority
              }
            />


            <InfoRow
              label="Human review"
              value={
                latestResponse.human_review_required
                  ? "REQUIRED"
                  : "NOT REQUIRED"
              }
            />

          </div>

        </div>

      </div>


      {/* LIVE PIPELINE FEATURES */}

      <div className="cs-module-card">

        <div className="cs-module-card-header">

          <div>

            <h3>
              Live Pipeline Features
            </h3>

            <p>
              Current crowd-intelligence values generated
              from the selected camera.
            </p>

          </div>

          <span className="cs-module-badge">
            LIVE
          </span>

        </div>


        <div className="cs-pipeline-output-grid">

          <Output
            icon={Users}
            label="People"
            value={
              personCount
            }
          />


          <Output
            icon={Activity}
            label="Moving Tracks"
            value={
              latestCrowd.moving_tracks
            }
          />


          <Output
            icon={Gauge}
            label="Mean Speed"
            value={
              latestCrowd.mean_speed_px_per_sec !==
              undefined
                ? `${format(
                    latestCrowd.mean_speed_px_per_sec,
                    1
                  )} px/s`
                : "—"
            }
          />


          <Output
            icon={Gauge}
            label="Maximum Speed"
            value={
              latestCrowd.max_speed_px_per_sec !==
              undefined
                ? `${format(
                    latestCrowd.max_speed_px_per_sec,
                    1
                  )} px/s`
                : "—"
            }
          />


          <Output
            icon={Activity}
            label="Crowd Load"
            value={
              latestRisk.crowd_load !==
              undefined
                ? `${format(
                    Number(
                      latestRisk.crowd_load
                    ) * 100,
                    1
                  )}%`
                : "—"
            }
          />


          <Output
            icon={Gauge}
            label="Movement Load"
            value={
              latestRisk.movement_load !==
              undefined
                ? `${format(
                    Number(
                      latestRisk.movement_load
                    ) * 100,
                    1
                  )}%`
                : "—"
            }
          />


          <Output
            icon={Activity}
            label="Spatial Load"
            value={
              latestRisk.spatial_load !==
              undefined
                ? `${format(
                    Number(
                      latestRisk.spatial_load
                    ) * 100,
                    1
                  )}%`
                : "—"
            }
          />


          <Output
            icon={Timer}
            label="Growth Load"
            value={
              latestRisk.growth_load !==
              undefined
                ? `${format(
                    Number(
                      latestRisk.growth_load
                    ) * 100,
                    1
                  )}%`
                : "—"
            }
          />

        </div>

      </div>


      {/* GLOBAL DATABASE / PRODUCTION RUN */}

      <div className="cs-module-card">

        <div className="cs-module-card-header">

          <div>

            <h3>
              Production Run & Database
            </h3>

            <p>
              Global SQLite production records. These
              records are not attributed to the selected
              camera.
            </p>

          </div>

          <span className="cs-module-badge">

            GLOBAL

          </span>

        </div>


        <div className="cs-module-grid">

          <PipelineStat
            icon={PlayCircle}
            label="RUN STATUS"
            value={
              latestRun?.status ||
              "—"
            }
            sub="latest production run"
          />


          <PipelineStat
            icon={Layers}
            label="FRAMES"
            value={
              latestRun?.processed_frames ??
              "—"
            }
            sub="processed frames"
          />


          <PipelineStat
            icon={Activity}
            label="TRACKED FRAMES"
            value={
              latestRun?.frames_with_tracks ??
              "—"
            }
            sub="frames containing tracks"
          />


          <PipelineStat
            icon={Timer}
            label="PROCESSING TIME"
            value={
              `${format(
                latestRun?.processing_seconds,
                2
              )}s`
            }
            sub="latest run"
          />


          <PipelineStat
            icon={Gauge}
            label="THROUGHPUT"
            value={
              format(
                latestRun?.throughput_fps,
                2
              )
            }
            sub="frames / second"
          />


          <PipelineStat
            icon={Database}
            label="DATABASE"
            value={
              health?.integrity === "ok"
                ? "HEALTHY"
                : "CHECK"
            }
            sub="SQLite integrity"
          />

        </div>


        <div className="cs-module-two-column">

          {/* RUN */}

          <div>

            <div className="cs-module-card-header">

              <div>

                <h3>
                  Latest Production Run
                </h3>

                <p>
                  Global run information stored in
                  SQLite.
                </p>

              </div>

            </div>


            <div className="cs-module-list">

              <InfoRow
                label="Run ID"
                value={
                  latestRun?.run_id
                }
              />

              <InfoRow
                label="Source"
                value={
                  latestRun?.source_name
                }
              />

              <InfoRow
                label="Source type"
                value={
                  latestRun?.source_type
                }
              />

              <InfoRow
                label="Processed frames"
                value={
                  latestRun?.processed_frames
                }
              />

              <InfoRow
                label="Frames with tracks"
                value={
                  latestRun?.frames_with_tracks
                }
              />

              <InfoRow
                label="Temporal windows"
                value={
                  latestRun?.processed_windows
                }
              />

              <InfoRow
                label="Completed"
                value={
                  latestRun?.completed_at
                }
              />

            </div>

          </div>


          {/* OUTPUTS */}

          <div>

            <div className="cs-module-card-header">

              <div>

                <h3>
                  Global Pipeline Outputs
                </h3>

                <p>
                  Production artifacts stored by the
                  backend.
                </p>

              </div>

            </div>


            <div className="cs-pipeline-output-grid">

              <Output
                icon={Video}
                label="Frame Results"
                value={
                  latestRun?.processed_frames
                }
              />

              <Output
                icon={Activity}
                label="Tracking"
                value={
                  latestRun?.frames_with_tracks
                }
              />

              <Output
                icon={Layers}
                label="Risk Windows"
                value={
                  summary?.risk_windows
                }
              />

              <Output
                icon={Route}
                label="Responses"
                value={
                  summary?.response_decisions
                }
              />

              <Output
                icon={Database}
                label="Cameras"
                value={
                  summary?.cameras
                }
              />

            </div>

          </div>

        </div>

      </div>


      {/* HEALTH */}

      <div className="cs-module-card">

        <div className="cs-module-card-header">

          <div>

            <h3>
              Pipeline Data Integrity
            </h3>

            <p>
              Database and operational safety state.
            </p>

          </div>

        </div>


        <div className="cs-pipeline-health-grid">

          <Health
            label="Selected camera"
            value={
              cameraIntelligence?.status
            }
            ok={
              cameraIntelligence?.status ===
              "RUNNING"
            }
          />


          <Health
            label="Camera AI output"
            value={
              latestFrame.frame_number
                ? "ACTIVE"
                : "WAITING"
            }
            ok={
              Boolean(
                latestFrame.frame_number
              )
            }
          />


          <Health
            label="SQLite database"
            value={
              health?.database
            }
            ok={
              health?.integrity ===
              "ok"
            }
          />


          <Health
            label="Database integrity"
            value={
              health?.integrity
            }
            ok={
              health?.integrity ===
              "ok"
            }
          />


          <Health
            label="Human review"
            value={
              latestResponse.human_review_required
                ? "REQUIRED"
                : "NOT REQUIRED"
            }
            ok={
              latestResponse.human_review_required ===
              true
            }
          />


          <Health
            label="Autonomous emergency action"
            value={
              latestResponse.autonomous_emergency_action
                ? "ENABLED"
                : "DISABLED"
            }
            ok={
              latestResponse.autonomous_emergency_action ===
              false
            }
          />

        </div>

      </div>


      {/* DISCLAIMER */}

      <div className="cs-module-disclaimer">

        <AlertTriangle size={15} />

        <div>

          <strong>
            Production interpretation
          </strong>

          <span>
            The selected camera pipeline provides live
            perception, tracking, crowd intelligence,
            operational risk and response information.
            SQLite production-run records remain global
            because they are not reliably mapped to a
            camera ID. Operational risk is a rule-based
            decision-support index, not a probability or
            validated emergency prediction. Human review
            is required and autonomous emergency action
            remains disabled.

          </span>

        </div>

      </div>

    </div>
  );
}


/* ============================================================
   SMALL COMPONENTS
   ============================================================ */

function PipelineStat({
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

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

      <small>
        {sub}
      </small>

    </div>
  );
}


function InfoRow({
  label,
  value,
}) {
  return (
    <div className="cs-module-list-row">

      <span>
        {label}
      </span>

      <strong>
        {value ?? "—"}
      </strong>

    </div>
  );
}


function Output({
  icon: Icon,
  label,
  value,
}) {
  return (
    <div className="cs-pipeline-output">

      <div className="cs-pipeline-output-icon">

        <Icon size={17} />

      </div>

      <div>

        <strong>
          {value ?? "—"}
        </strong>

        <span>
          {label}
        </span>

      </div>

    </div>
  );
}


function Health({
  label,
  value,
  ok,
}) {
  return (
    <div className="cs-pipeline-health-item">

      <div className="cs-pipeline-health-icon">

        {ok ? (
          <CheckCircle2 size={16} />
        ) : (
          <AlertTriangle size={16} />
        )}

      </div>


      <div>

        <span>
          {label}
        </span>

        <strong
          className={
            label ===
            "Autonomous emergency action"
              ? "cs-health-safe"
              : ""
          }
        >
          {String(
            value ?? "—"
          ).toUpperCase()}
        </strong>

      </div>

    </div>
  );
}