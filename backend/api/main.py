import os
import json
import time

import cv2
import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.services.production_data_service import production_data_service
from backend.services.database_service import database_service
from backend.services.camera_service import camera_service
from backend.services.incident_service import incident_service


app = FastAPI(
    title="CrowdShield AI API",
    description="Backend API for crowd monitoring and risk analysis",
    version="1.0.0"
)


# ----------------------------------------------------------------
# DATABASE INITIALIZATION
# ----------------------------------------------------------------

@app.on_event("startup")
def initialize_database():
    """
    Initialize additive database tables.
    Existing database tables and records are preserved.
    """
    database_service.initialize_crowd_history()
    print("[DATABASE] Crowd history table initialized.")

    incident_service.initialize()
    print("[DATABASE] Alert and incident tables initialized.")




# ----------------------------------------------------------------
# CORS configuration
# ----------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PROJECT_DIR = r"C:\Users\pabit\CrowdShield-AI"


RISK_FILE = os.path.join(
    PROJECT_DIR,
    "data",
    "processed",
    "risk",
    "clean_risk_analysis_dataset.csv"
)


def load_risk_data():

    if not os.path.exists(RISK_FILE):
        raise HTTPException(
            status_code=404,
            detail="Risk dataset not found"
        )

    return pd.read_csv(RISK_FILE)


# ----------------------------------------------------------------
# HOME
# ----------------------------------------------------------------

@app.get("/")
def home():

    return {
        "project": "CrowdShield AI",
        "status": "Backend API is running"
    }


# ----------------------------------------------------------------
# PRODUCTION HEALTH
# ----------------------------------------------------------------

@app.get("/api/health")
def api_health():

    """Return backend health and production pipeline status."""

    return {
        "status": "healthy",
        "service": "CrowdShield AI Backend",
        "api_version": "1.0.0",
        "pipeline_source": "production_pipeline",
        "human_review_required": True,
        "autonomous_emergency_action": False,
    }


# ----------------------------------------------------------------
# DASHBOARD SUMMARY
# ----------------------------------------------------------------

@app.get("/api/dashboard/summary")
def dashboard_summary():

    summary = production_data_service.dashboard_summary()

    return {

        "source": summary.get(
            "source",
            "production_pipeline"
        ),

        "summary_type": (
            "production_operational_risk"
        ),

        "risk_interpretation": (
            "Rule-based operational risk index "
            "for decision support; not a probability "
            "or validated emergency prediction."
        ),

        "score_range": {

            "minimum": summary.get(
                "minimum_risk_score"
            ),

            "maximum": summary.get(
                "maximum_risk_score"
            ),

        },

        "processed_windows": summary.get(
            "processed_windows",
            0
        ),

        "minimum_risk_score": summary.get(
            "minimum_risk_score"
        ),

        "mean_risk_score": summary.get(
            "mean_risk_score"
        ),

        "maximum_risk_score": summary.get(
            "maximum_risk_score"
        ),

        "risk_distribution": summary.get(
            "risk_distribution",
            {}
        ),

        "response_distribution": summary.get(
            "response_distribution",
            {}
        ),

        "latest_state": summary.get(
            "latest_state",
            {}
        ),

        "human_review_required": True,

        "autonomous_emergency_action": False,

    }


# ----------------------------------------------------------------
# RISK TIMELINE
# ----------------------------------------------------------------

@app.get("/api/risk/timeline")
def risk_timeline():

    timeline = production_data_service.risk_timeline()

    return {

        "status": "success",

        "source": "production_pipeline",

        "timeline_type": "production_operational_risk",

        "interpretation": (
            "Rule-based operational risk index over temporal "
            "windows for decision support; not a probability "
            "or validated emergency prediction."
        ),

        "window_count": len(timeline),

        "risk_levels": [
            "LOW",
            "MODERATE",
            "HIGH",
            "CRITICAL",
        ],

        "human_review_required": True,

        "autonomous_emergency_action": False,

        "data": timeline,

    }


# ----------------------------------------------------------------
# ALERTS
# ----------------------------------------------------------------

@app.get("/api/alerts")
def get_alerts(
    camera_id: str = None,
    risk_level: str = None,
    status: str = None,
    limit: int = 200
):
    """
    Retrieve persistent live alerts with incident lifecycle status.

    Optional filters:
    - camera_id: camera identifier, e.g. CAM-002
    - risk_level: HIGH or CRITICAL
    - status: OPEN, ACKNOWLEDGED, ASSIGNED, RESOLVED
    - limit: maximum number of alerts
    """
    limit = max(1, min(limit, 500))

    try:
        live_alerts = incident_service.list_alerts(
            camera_id=camera_id,
            risk_level=risk_level,
            status=status,
            limit=limit
        )

        return {
            "status": "success",
            "source": "sqlite_live_alerts",
            "alert_type": "operational_risk",
            "description": (
                "Persistent HIGH and CRITICAL operational "
                "risk alerts requiring human review."
            ),
            "total_alerts": len(live_alerts),
            "filters": {
                "camera_id": camera_id,
                "risk_level": risk_level,
                "status": status,
                "limit": limit
            },
            "human_review_required": True,
            "autonomous_emergency_action": False,
            "alerts": live_alerts
        }

    except Exception as exc:
        print(f"[ALERT API ERROR] {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve alerts: {str(exc)}"
        )


# ----------------------------------------------------------------
# SIMULATED ROUTE
# ----------------------------------------------------------------

@app.get("/api/routes/simulated")
def get_simulated_route():

    route_file = os.path.join(
        PROJECT_DIR,
        "routes",
        "simulated_route_frame497.csv"
    )

    if not os.path.exists(route_file):

        raise HTTPException(
            status_code=404,
            detail="Simulated route file not found"
        )

    route_df = pd.read_csv(route_file)

    return {

        "frame": 497,

        "route_type": "Simulated A* route",

        "status": (
            "Demonstration only; not safety-validated"
        ),

        "total_points": int(
            len(route_df)
        ),

        "route": route_df.to_dict(
            orient="records"
        )

    }


# ----------------------------------------------------------------
# ROUTE VALIDATION
# ----------------------------------------------------------------

@app.get("/api/routes/validation")
def get_route_validation():

    report_file = os.path.join(
        PROJECT_DIR,
        "routes",
        "route_validation_report.json"
    )

    if not os.path.exists(report_file):

        raise HTTPException(
            status_code=404,
            detail="Route validation report not found"
        )

    with open(
        report_file,
        "r",
        encoding="utf-8"
    ) as f:

        report = json.load(f)

    return report


# ----------------------------------------------------------------
# CROWD INTELLIGENCE
# ----------------------------------------------------------------

@app.get("/api/crowd-intelligence")
def get_crowd_intelligence():

    data = production_data_service.crowd_intelligence()

    return {

        "status": "success",

        "source": "production_pipeline",

        "windows": len(data),

        "data": data,

    }


# ----------------------------------------------------------------
# FRAME-LEVEL CROWD INTELLIGENCE
# ----------------------------------------------------------------

@app.get("/api/crowd-intelligence/frames")
def get_frame_level_crowd_intelligence():

    data = production_data_service.frame_intelligence()

    return {

        "status": "success",

        "source": "production_pipeline",

        "frames": len(data),

        "data": data,

    }


# ----------------------------------------------------------------
# CROWD INTELLIGENCE ALERTS
# ----------------------------------------------------------------

@app.get("/api/crowd-intelligence/alerts")
def get_crowd_intelligence_alerts():

    alerts = production_data_service.alerts()

    return {

        "status": "success",

        "source": "production_pipeline",

        "alert_type": "operational_risk",

        "description": (
            "Rule-based operational risk alerts "
            "requiring human review."
        ),

        "alerts": len(alerts),

        "human_review_required": True,

        "autonomous_emergency_action": False,

        "data": alerts,

    }


# ----------------------------------------------------------------
# CROWD FLOW
# ----------------------------------------------------------------

@app.get("/api/crowd-intelligence/flow")
def get_crowd_flow():

    flow_path = os.path.join(
        PROJECT_DIR,
        "data",
        "processed",
        "realtime_monitoring",
        "crowd_flow_grid_analysis.csv"
    )

    if not os.path.exists(flow_path):

        return {

            "status": "error",

            "message": (
                "Crowd flow analysis file not found"
            ),

            "data": []

        }

    flow_df = pd.read_csv(flow_path)

    return {

        "status": "success",

        "records": len(flow_df),

        "data": flow_df.to_dict(
            orient="records"
        )

    }


# ================================================================
# CAMERA ENDPOINTS
# ================================================================


@app.get("/api/cameras")
def cameras():

    """
    Return the existing recorded camera and
    registered live cameras.
    """

    recorded_camera = {

        "camera_id": "CAM-001",

        "camera_name": "Camera 1",

        "source_file": "people.mp4.mp4",

        "status": "RECORDED_REPLAY",

        "source_type": "recorded_video",

        "width": 1920,

        "height": 1080,

        "fps": 25.0,

        "frame_count": 498,

        "duration_sec": 19.92,

        "live_stream": False,

        "human_review_required": True,

        "autonomous_emergency_action": False,

    }

    live_cameras = camera_service.get_cameras()

    camera_records = [
        recorded_camera
    ] + live_cameras

    live_available = any(

        camera.get("live_stream")
        and camera.get("status") == "RUNNING"

        for camera in live_cameras

    )

    return {

        "status": "success",

        "source": "production_pipeline",

        "camera_type": "mixed",

        "camera_count": len(
            camera_records
        ),

        "live_camera_available": live_available,

        "human_review_required": True,

        "autonomous_emergency_action": False,

        "data": camera_records,

    }


# ----------------------------------------------------------------
# START CAMERA
# ----------------------------------------------------------------

@app.post("/api/cameras/start")
def start_camera(payload: dict):

    """
    Start a webcam or RTSP/IP camera
    in the background.
    """

    required_fields = [
        "camera_id",
        "source_type",
        "source"
    ]

    missing = [
        field
        for field in required_fields
        if field not in payload
    ]

    if missing:

        raise HTTPException(
            status_code=400,
            detail=f"Missing required fields: {missing}",
        )

    try:

        result = camera_service.start_camera(

            camera_id=payload["camera_id"],

            camera_name=payload.get(
                "camera_name",
                payload["camera_id"]
            ),

            source_type=payload["source_type"],

            source=payload["source"],

            expected_fps=payload.get(
                "expected_fps"
            ),

        )

        return {

            "status": "success",

            "message": "Camera startup requested.",

            "data": result,

        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


# ----------------------------------------------------------------
# CAMERA STATUS
# ----------------------------------------------------------------

@app.get("/api/cameras/{camera_id}/status")
def camera_status(camera_id: str):

    """
    Get the latest status for one registered
    live camera.
    """

    result = camera_service.get_camera(
        camera_id
    )

    if result is None:

        raise HTTPException(
            status_code=404,
            detail=f"Camera {camera_id} was not found.",
        )

    return {
        "status": "success",
        "data": result
    }


# ----------------------------------------------------------------
# CAMERA INTELLIGENCE
# ----------------------------------------------------------------

@app.get("/api/cameras/{camera_id}/intelligence")
def camera_intelligence(camera_id: str):

    """
    Return camera-specific AI intelligence.

    CAM-001 uses the recorded production
    pipeline artifacts.

    Live cameras use the runtime camera service.
    """

    # ============================================================
    # RECORDED CAMERA — CAM-001
    # ============================================================

    if camera_id == "CAM-001":

        try:

            frame_df = (
                production_data_service
                .frame_risk_features()
            )

            risk_df = (
                production_data_service
                .operational_risk()
            )

            response_records = (
                production_data_service
                .response_decisions()
            )

            metadata = (
                production_data_service
                .metadata()
            )

            latest_frame = (
                frame_df.iloc[-1].to_dict()
                if not frame_df.empty
                else {}
            )

            latest_risk = (
                risk_df.iloc[-1].to_dict()
                if not risk_df.empty
                else {}
            )

            latest_response = (
                response_records[-1]
                if response_records
                else {}
            )

            source = metadata.get(
                "source",
                {}
            )

            return {

                "status": "success",

                "data": {

                    "camera_id": "CAM-001",

                    "camera_name": "Camera 1",

                    "source_type": "recorded_video",

                    "status": "RECORDED_REPLAY",

                    "live_stream": False,

                    "width": source.get(
                        "width",
                        1920
                    ),

                    "height": source.get(
                        "height",
                        1080
                    ),

                    "fps": source.get(
                        "fps",
                        25.0
                    ),

                    "frame_count": source.get(
                        "frame_number",
                        len(frame_df)
                    ),

                    "latest_frame": latest_frame,

                    "latest_person_count": (
                        latest_frame.get(
                            "person_count",
                            0
                        )
                    ),

                    "latest_risk": latest_risk,

                    "latest_response": latest_response,

                    "error": None,

                    "last_updated": None,

                    "data_source": (
                        "recorded_production_pipeline"
                    ),

                    "recorded_pipeline": {

                        "processed_frames":
                            metadata.get(
                                "processed_frames",
                                len(frame_df)
                            ),

                        "frames_with_tracks":
                            metadata.get(
                                "frames_with_tracks",
                                0
                            ),

                        "temporal_windows":
                            metadata.get(
                                "temporal_windows",
                                len(risk_df)
                            ),

                        "throughput_fps":
                            metadata.get(
                                "throughput_fps"
                            ),

                        "source_name":
                            source.get(
                                "source_name",
                                "crowdshield_recorded_validation"
                            ),

                    },

                },

            }

        except Exception as exc:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Failed to load recorded "
                    f"camera intelligence: {exc}"
                ),
            )


    # ============================================================
    # LIVE CAMERAS — WEBCAM / RTSP / IP CAMERA
    # ============================================================

    camera = camera_service.get_camera(
        camera_id
    )

    if camera is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Camera {camera_id} was not found."
            ),
        )

    return {

        "status": "success",

        "data": {

            "camera_id": camera.get(
                "camera_id"
            ),

            "camera_name": camera.get(
                "camera_name"
            ),

            "source_type": camera.get(
                "source_type"
            ),

            "status": camera.get(
                "status"
            ),

            "live_stream": camera.get(
                "live_stream"
            ),

            "width": camera.get(
                "width"
            ),

            "height": camera.get(
                "height"
            ),

            "fps": camera.get(
                "fps"
            ),

            "frame_count": camera.get(
                "frame_count"
            ),

            "latest_frame": camera.get(
                "latest_frame",
                {}
            ),

            "latest_person_count": camera.get(
                "latest_person_count",
                0
            ),

            "latest_risk": camera.get(
                "latest_risk",
                {}
            ),

            "latest_response": camera.get(
                "latest_response",
                {}
            ),

            "error": camera.get(
                "error"
            ),

            "last_updated": camera.get(
                "last_updated"
            ),

            "data_source": "live_camera_service",

        },

    }


# ----------------------------------------------------------------
# RECORDED VIDEO
# ----------------------------------------------------------------

@app.get("/api/cameras/{camera_id}/video")
def camera_video(camera_id: str):

    """
    Serve the configured recorded video
    for CAM-001.
    """

    if camera_id != "CAM-001":

        raise HTTPException(
            status_code=404,
            detail=(
                f"Recorded video for "
                f"{camera_id} was not found."
            )
        )

    video_path = os.path.join(
        PROJECT_DIR,
        "data",
        "raw",
        "videos",
        "people.mp4.mp4"
    )

    if not os.path.exists(video_path):

        raise HTTPException(
            status_code=404,
            detail="Recorded video file was not found."
        )

    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename="people.mp4.mp4"
    )


# ----------------------------------------------------------------
# CAMERA FRAME
# ----------------------------------------------------------------

@app.get("/api/cameras/{camera_id}/frame")
def camera_frame(camera_id: str):

    """
    Return the latest processed camera
    frame as a JPEG.
    """

    worker = camera_service.get_camera_worker(
        camera_id
    )

    if worker is None:

        raise HTTPException(
            status_code=404,
            detail=f"Camera {camera_id} was not found."
        )

    with worker._lock:

        frame = (
            worker.latest_raw_frame.copy()
            if worker.latest_raw_frame is not None
            else None
        )

    if frame is None:

        raise HTTPException(
            status_code=503,
            detail=(
                "No camera frame is currently available."
            )
        )

    success, encoded = cv2.imencode(
        ".jpg",
        frame
    )

    if not success:

        raise HTTPException(
            status_code=500,
            detail="Failed to encode camera frame."
        )

    return Response(

        content=encoded.tobytes(),

        media_type="image/jpeg",

        headers={
            "Cache-Control": (
                "no-store, no-cache, "
                "must-revalidate, max-age=0"
            ),
            "Pragma": "no-cache",
            "Expires": "0",
        }

    )


# ----------------------------------------------------------------
# CAMERA STREAM
# ----------------------------------------------------------------

@app.get("/api/cameras/{camera_id}/stream")
def camera_stream(camera_id: str):

    """
    Stream the latest processed camera
    frames as MJPEG.
    """

    worker = camera_service.get_camera_worker(
        camera_id
    )

    if worker is None:

        raise HTTPException(
            status_code=404,
            detail=f"Camera {camera_id} was not found."
        )

    def generate_frames():

        while not worker._stop_event.is_set():

            with worker._lock:

                frame = (
                    worker.latest_raw_frame.copy()
                    if worker.latest_raw_frame is not None
                    else None
                )

            if frame is None:

                time.sleep(0.05)

                continue

            success, encoded = cv2.imencode(
                ".jpg",
                frame
            )

            if not success:

                time.sleep(0.05)

                continue

            yield (

                b"--frame\r\n"

                b"Content-Type: image/jpeg\r\n\r\n"

                + encoded.tobytes()

                + b"\r\n"

            )

            time.sleep(0.03)

    return StreamingResponse(

        generate_frames(),

        media_type=(
            "multipart/x-mixed-replace; "
            "boundary=frame"
        ),

    )


# ----------------------------------------------------------------
# STOP CAMERA
# ----------------------------------------------------------------

@app.post("/api/cameras/{camera_id}/stop")
def stop_camera(camera_id: str):

    """
    Stop a registered live camera.
    """

    try:

        result = camera_service.stop_camera(
            camera_id
        )

        return {

            "status": "success",

            "message": "Camera stop requested.",

            "data": result,

        }

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )


# ================================================================
# DATABASE SERVICE ENDPOINTS
# ================================================================


@app.get("/api/database/health")
def database_health():

    """
    Database health and integrity information.
    """

    return database_service.health()


@app.get("/api/database/summary")
def database_summary():

    """
    Production database summary.
    """

    return database_service.get_summary()


@app.get("/api/database/cameras")
def database_cameras():

    """
    Camera records persisted in the production database.
    """

    cameras = database_service.get_cameras()

    return {

        "status": "success",

        "source": "sqlite",

        "camera_count": len(cameras),

        "data": cameras,

    }


@app.get("/api/database/risk")
def database_risk():

    """
    Persisted operational risk windows.
    """

    data = database_service.get_risk_windows()

    return {

        "status": "success",

        "source": "sqlite",

        "window_count": len(data),

        "human_review_required": True,

        "autonomous_emergency_action": False,

        "data": data,

    }


@app.get("/api/database/response")
def database_response():

    """
    Persisted response decisions.
    """

    data = database_service.get_response_decisions()

    return {

        "status": "success",

        "source": "sqlite",

        "decision_count": len(data),

        "human_review_required": True,

        "autonomous_emergency_action": False,

        "data": data,

    }


@app.get("/api/database/runs")
def database_runs():

    """
    Historical production pipeline runs.
    """

    data = database_service.get_pipeline_runs()

    return {

        "status": "success",

        "source": "sqlite",

        "run_count": len(data),

        "data": data,

    }



# ================================================================
# HISTORICAL CROWD ANALYTICS
# ================================================================

@app.get("/api/crowd-history")
def get_crowd_history(
    camera_id: str = None,
    start_time: str = None,
    end_time: str = None,
    limit: int = 1000
):
    """
    Retrieve persisted historical crowd snapshots.

    Optional filters:
    - camera_id: camera identifier, e.g. CAM-002
    - start_time/end_time: ISO-8601 timestamps
    - limit: maximum number of snapshots returned
    """
    limit = max(1, min(limit, 100000))

    data = database_service.get_crowd_snapshots(
        camera_id=camera_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )

    return {
        "status": "success",
        "source": "sqlite_crowd_history",
        "snapshot_count": len(data),
        "filters": {
            "camera_id": camera_id,
            "start_time": start_time,
            "end_time": end_time,
            "limit": limit
        },
        "data": data
    }


@app.get("/api/crowd-history/summary")
def get_crowd_history_summary(
    camera_id: str = None,
    start_time: str = None,
    end_time: str = None,
    limit: int = 20000
):
    """
    Return historical crowd statistics, peak periods and
    frequently occupied image-space zones.
    """
    limit = max(1, min(limit, 20000))

    summary = database_service.get_crowd_history_summary(
        camera_id=camera_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )

    return {
        "status": "success",
        "source": "sqlite_crowd_history",
        "data": summary
    }

# ================================================================
# INCIDENT LIFECYCLE ENDPOINTS
# ================================================================

@app.post("/api/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str, payload: dict = None):
    payload = payload or {}
    try:
        incident = incident_service.update(
            alert_id,
            "acknowledge",
            actor=payload.get("actor", "operator"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "status": "success",
        "incident": incident,
        "human_review_required": True,
        "autonomous_emergency_action": False,
    }


@app.post("/api/alerts/{alert_id}/assign")
def assign_alert(alert_id: str, payload: dict):
    officer = payload.get("officer")

    try:
        incident = incident_service.update(
            alert_id,
            "assign",
            actor=payload.get("actor", "operator"),
            officer=officer,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "status": "success",
        "incident": incident,
        "human_review_required": True,
        "autonomous_emergency_action": False,
    }


@app.post("/api/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: str, payload: dict = None):
    payload = payload or {}

    try:
        incident = incident_service.update(
            alert_id,
            "resolve",
            actor=payload.get("actor", "operator"),
            note=payload.get("note"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "status": "success",
        "incident": incident,
        "human_review_required": True,
        "autonomous_emergency_action": False,
    }


@app.post("/api/alerts/{alert_id}/reopen")
def reopen_alert(alert_id: str, payload: dict = None):
    payload = payload or {}

    try:
        incident = incident_service.update(
            alert_id,
            "reopen",
            actor=payload.get("actor", "operator"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "status": "success",
        "incident": incident,
        "human_review_required": True,
        "autonomous_emergency_action": False,
    }


@app.get("/api/incidents/history")
def incident_history(alert_id: str = None, limit: int = 200):
    limit = max(1, min(limit, 500))
    history = incident_service.history(alert_id, limit)

    return {
        "status": "success",
        "count": len(history),
        "history": history,
    }