import os
import requests
import cv2
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt


# ============================================================
# CROWDShield AI — STREAMLIT RESEARCH / ML DASHBOARD
# ============================================================

st.set_page_config(
    page_title="CrowdShield AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = r"C:\Users\pabit\CrowdShield-AI"

API_URL = "http://127.0.0.1:8000"

VIDEO_PATH = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "videos",
    "people.mp4.mp4",
)

PRODUCTION_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "production_pipeline",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        background-color: #f7f9fc;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    .metric-card {
        background-color: white;
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    .metric-title {
        color: #64748b;
        font-size: 13px;
        font-weight: 600;
    }

    .metric-value {
        color: #0f172a;
        font-size: 28px;
        font-weight: 800;
        margin-top: 5px;
    }

    .safe-box {
        background-color: #ecfdf5;
        border-left: 5px solid #22c55e;
        padding: 14px;
        border-radius: 8px;
    }

    .warning-box {
        background-color: #fffbeb;
        border-left: 5px solid #f59e0b;
        padding: 14px;
        border-radius: 8px;
    }

    .danger-box {
        background-color: #fef2f2;
        border-left: 5px solid #ef4444;
        padding: 14px;
        border-radius: 8px;
    }

    .info-box {
        background-color: #eff6ff;
        border-left: 5px solid #3b82f6;
        padding: 14px;
        border-radius: 8px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def api_get(endpoint):
    """
    GET request to FastAPI.
    Returns JSON or raises an exception.
    """
    response = requests.get(
        f"{API_URL}{endpoint}",
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def extract_list(payload, possible_keys=None):
    """
    Safely convert API responses into a list.

    Handles:
        [...]
        {"data": [...]}
        {"timeline": [...]}
        {"alerts": [...]}
        {"results": [...]}
    """

    if payload is None:
        return []

    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):

        if possible_keys is None:
            possible_keys = [
                "data",
                "timeline",
                "alerts",
                "results",
                "items",
            ]

        for key in possible_keys:

            value = payload.get(key)

            if isinstance(value, list):
                return value

        return []

    return []


def dataframe_from_api(
    payload,
    possible_keys=None,
):
    """
    Safely create DataFrame from API response.
    """

    records = extract_list(
        payload,
        possible_keys,
    )

    if not records:
        return pd.DataFrame()

    if isinstance(records, list):

        clean_records = []

        for item in records:

            if isinstance(item, dict):
                clean_records.append(item)

        if clean_records:
            return pd.DataFrame(clean_records)

    return pd.DataFrame()


def safe_number(value, default=0.0):

    try:
        if value is None:
            return default

        return float(value)

    except Exception:
        return default


def safe_int(value, default=0):

    try:
        if value is None:
            return default

        return int(value)

    except Exception:
        return default


def risk_color(level):

    level = str(level).upper()

    if level == "CRITICAL":
        return "#dc2626"

    if level == "HIGH":
        return "#ef4444"

    if level == "MODERATE":
        return "#f59e0b"

    if level == "LOW":
        return "#22c55e"

    return "#64748b"


def display_value(value, default="—"):

    if value is None:
        return default

    return str(value)


# ============================================================
# LOAD API DATA
# ============================================================

@st.cache_data(ttl=5)
def load_dashboard():

    return api_get(
        "/api/dashboard/summary"
    )


@st.cache_data(ttl=5)
def load_timeline():

    return api_get(
        "/api/risk/timeline"
    )


@st.cache_data(ttl=5)
def load_alerts():

    return api_get(
        "/api/alerts"
    )


@st.cache_data(ttl=5)
def load_cameras():

    return api_get(
        "/api/cameras"
    )


@st.cache_data(ttl=5)
def load_crowd_intelligence():

    return api_get(
        "/api/crowd-intelligence"
    )


@st.cache_data(ttl=5)
def load_frame_intelligence():

    return api_get(
        "/api/crowd-intelligence/frames"
    )


@st.cache_data(ttl=5)
def load_crowd_alerts():

    return api_get(
        "/api/crowd-intelligence/alerts"
    )


@st.cache_data(ttl=5)
def load_crowd_flow():

    return api_get(
        "/api/crowd-intelligence/flow"
    )


@st.cache_data(ttl=5)
def load_route():

    return api_get(
        "/api/routes/simulated"
    )


@st.cache_data(ttl=5)
def load_route_validation():

    return api_get(
        "/api/routes/validation"
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🛡️ CrowdShield AI")

    st.caption(
        "Intelligent Multimodal Crowd Safety "
        "and Emergency Response System"
    )

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "Command Center",
            "Risk Monitoring",
            "Crowd Intelligence",
            "Frame Monitor",
            "Alerts",
            "Camera",
            "Routing",
            "System",
        ],
    )

    st.divider()

    st.markdown(
        "**System Mode**"
    )

    st.info(
        "Recorded Camera Replay"
    )

    st.caption(
        "Decision-support system. "
        "Human review required."
    )

    if st.button(
        "🔄 Refresh Data",
        use_container_width=True,
    ):

        st.cache_data.clear()

        st.rerun()


# ============================================================
# HEADER
# ============================================================

st.title("🛡️ CrowdShield AI")

st.caption(
    "ML / AI Research and Operational Monitoring Dashboard"
)


# ============================================================
# API HEALTH CHECK
# ============================================================

try:

    health = api_get(
        "/api/health"
    )

    backend_available = True

except Exception as e:

    backend_available = False

    st.error(
        "Cannot connect to FastAPI backend."
    )

    st.code(
        str(e)
    )

    st.info(
        "Start FastAPI with: "
        "python -m uvicorn backend.api.main:app "
        "--host 0.0.0.0 --port 8000"
    )

    st.stop()


# ============================================================
# COMMAND CENTER
# ============================================================

if page == "Command Center":

    st.header(
        "🎯 Command Center"
    )

    try:

        dashboard = load_dashboard()

    except Exception as e:

        st.error(
            f"Dashboard API error: {e}"
        )

        st.stop()

    summary = dashboard.get(
        "summary",
        dashboard,
    )

    latest = dashboard.get(
        "latest_state",
        {},
    )

    if not isinstance(latest, dict):
        latest = {}

    processed_windows = safe_int(
        dashboard.get(
            "processed_windows",
            summary.get(
                "processed_windows",
                0,
            )
            if isinstance(summary, dict)
            else 0,
        )
    )

    minimum_risk = safe_number(
        dashboard.get(
            "minimum_risk_score",
            0,
        )
    )

    mean_risk = safe_number(
        dashboard.get(
            "mean_risk_score",
            0,
        )
    )

    maximum_risk = safe_number(
        dashboard.get(
            "maximum_risk_score",
            0,
        )
    )

    latest_score = safe_number(
        latest.get(
            "risk_score",
            latest.get(
                "operational_risk_score",
                0,
            ),
        )
    )

    latest_level = display_value(
        latest.get(
            "risk_level",
            latest.get(
                "operational_risk_level",
                "UNKNOWN",
            ),
        )
    )

    latest_response = display_value(
        latest.get(
            "response_action",
            "UNKNOWN",
        )
    )

    latest_priority = display_value(
        latest.get(
            "response_priority",
            "UNKNOWN",
        )
    )

    # --------------------------------------------------------
    # KPI ROW
    # --------------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Processed Windows",
            processed_windows,
        )

    with c2:

        st.metric(
            "Mean Risk",
            f"{mean_risk:.2f}",
        )

    with c3:

        st.metric(
            "Maximum Risk",
            f"{maximum_risk:.2f}",
        )

    with c4:

        st.metric(
            "Minimum Risk",
            f"{minimum_risk:.2f}",
        )

    st.divider()

    # --------------------------------------------------------
    # CURRENT RISK
    # --------------------------------------------------------

    st.subheader(
        "Current Operational Risk"
    )

    risk_col = risk_color(
        latest_level
    )

    st.markdown(
        f"""
        <div style="
            background-color:white;
            padding:22px;
            border-radius:12px;
            border-left:7px solid {risk_col};
            border-top:1px solid #e5e7eb;
            border-right:1px solid #e5e7eb;
            border-bottom:1px solid #e5e7eb;
        ">

        <h2 style="margin-bottom:5px;">
            {latest_level}
        </h2>

        <h1 style="
            color:{risk_col};
            margin-top:5px;
        ">
            {latest_score:.2f} / 100
        </h1>

        <p>
            <b>Response:</b>
            {latest_response}
        </p>

        <p>
            <b>Priority:</b>
            {latest_priority}
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # --------------------------------------------------------
    # RISK DISTRIBUTION
    # --------------------------------------------------------

    st.subheader(
        "Risk Distribution"
    )

    risk_distribution = dashboard.get(
        "risk_distribution",
        {},
    )

    if isinstance(
        risk_distribution,
        dict,
    ):

        risk_df = pd.DataFrame(
            [
                {
                    "Risk Level": str(k),
                    "Windows": safe_int(v),
                }
                for k, v in risk_distribution.items()
            ]
        )

        if not risk_df.empty:

            col1, col2 = st.columns(2)

            with col1:

                st.dataframe(
                    risk_df,
                    use_container_width=True,
                    hide_index=True,
                )

            with col2:

                st.bar_chart(
                    risk_df.set_index(
                        "Risk Level"
                    )
                )

    # --------------------------------------------------------
    # RESPONSE DISTRIBUTION
    # --------------------------------------------------------

    st.subheader(
        "Response Distribution"
    )

    response_distribution = dashboard.get(
        "response_distribution",
        {},
    )

    if isinstance(
        response_distribution,
        dict,
    ):

        response_df = pd.DataFrame(
            [
                {
                    "Response": str(k),
                    "Windows": safe_int(v),
                }
                for k, v in response_distribution.items()
            ]
        )

        if not response_df.empty:

            st.dataframe(
                response_df,
                use_container_width=True,
                hide_index=True,
            )

    st.divider()

    st.subheader(
        "Safety Controls"
    )

    sc1, sc2, sc3 = st.columns(3)

    with sc1:

        st.success(
            "Human Review: REQUIRED"
        )

    with sc2:

        st.success(
            "Autonomous Emergency Action: DISABLED"
        )

    with sc3:

        st.info(
            "System Role: DECISION SUPPORT"
        )

    st.warning(
        "Operational risk is a rule-based decision-support "
        "score. It is not a probability and is not presented "
        "as a validated emergency prediction."
    )


# ============================================================
# RISK MONITORING
# ============================================================

if page in ("Risk Monitoring", "Command Center"):

    st.header(
        "📈 Risk Monitoring"
    )

    try:

        timeline_response = load_timeline()

        timeline_df = dataframe_from_api(
            timeline_response,
            [
                "data",
                "timeline",
                "results",
            ],
        )

    except Exception as e:

        st.error(
            f"Risk timeline error: {e}"
        )

        timeline_df = pd.DataFrame()

    if timeline_df.empty:

        st.warning(
            "No risk timeline data available."
        )

    else:

        st.subheader(
            "Operational Risk Timeline"
        )

        # Normalize likely score column

        score_column = None

        for candidate in [
            "operational_risk_score",
            "risk_score",
            "score",
        ]:

            if candidate in timeline_df.columns:

                score_column = candidate
                break

        if score_column:

            chart_df = timeline_df[
                [score_column]
            ].copy()

            chart_df[score_column] = pd.to_numeric(
                chart_df[score_column],
                errors="coerce",
            )

            chart_df = chart_df.dropna()

            if not chart_df.empty:

                st.line_chart(
                    chart_df
                )

        st.dataframe(
            timeline_df,
            use_container_width=True,
            hide_index=True,
        )

        st.info(
            "Risk scores shown here are operational, "
            "rule-based decision-support values."
        )


# ============================================================
# CROWD INTELLIGENCE
# ============================================================

if page in ("Crowd Intelligence", "Command Center"):

    st.header(
        "👥 Crowd Intelligence"
    )

    try:

        crowd_response = load_crowd_intelligence()

        crowd_df = dataframe_from_api(
            crowd_response,
            [
                "data",
                "results",
            ],
        )

    except Exception as e:

        st.error(
            f"Crowd intelligence error: {e}"
        )

        crowd_df = pd.DataFrame()

    if crowd_df.empty:

        st.warning(
            "No crowd-intelligence data available."
        )

    else:

        st.subheader(
            "Temporal Crowd Intelligence"
        )

        st.dataframe(
            crowd_df,
            use_container_width=True,
            hide_index=True,
            height=500,
        )

        # ----------------------------------------------------
        # SELECT NUMERIC FEATURES
        # ----------------------------------------------------

        numeric_columns = crowd_df.select_dtypes(
            include="number"
        ).columns.tolist()

        if numeric_columns:

            selected_feature = st.selectbox(
                "Select feature for trend",
                numeric_columns,
            )

            feature_df = crowd_df[
                [selected_feature]
            ].copy()

            feature_df[
                selected_feature
            ] = pd.to_numeric(
                feature_df[
                    selected_feature
                ],
                errors="coerce",
            )

            st.line_chart(
                feature_df
            )

        st.divider()

        st.subheader(
            "Crowd Intelligence Interpretation"
        )

        st.markdown(
            """
            The crowd-intelligence layer combines explainable
            signals such as:

            - Crowd load
            - Movement load
            - Movement events
            - Spatial load
            - Crowd growth
            - Persistence
            - High-speed movement signals

            These features support the operational risk engine
            and are not independently treated as validated
            safety probabilities.
            """
        )


# ============================================================
# FRAME MONITOR
# ============================================================

if page in ("Frame Monitor", "Command Center"):

    st.header(
        "🎥 Frame-Level Crowd Monitor"
    )

    try:

        frame_response = load_frame_intelligence()

        frame_df = dataframe_from_api(
            frame_response,
            [
                "data",
                "frames",
                "results",
            ],
        )

    except Exception as e:

        st.error(
            f"Frame intelligence error: {e}"
        )

        frame_df = pd.DataFrame()

    if frame_df.empty:

        st.warning(
            "No frame-level intelligence data available."
        )

    else:

        st.subheader(
            "Frame Intelligence"
        )

        st.dataframe(
            frame_df,
            use_container_width=True,
            hide_index=True,
            height=400,
        )

        # ----------------------------------------------------
        # FRAME SELECTOR
        # ----------------------------------------------------

        if "frame" in frame_df.columns:

            frame_values = pd.to_numeric(
                frame_df["frame"],
                errors="coerce",
            ).dropna()

            if not frame_values.empty:

                frame_options = [
                    int(x)
                    for x in frame_values.tolist()
                ]

                selected_frame = st.selectbox(
                    "Select video frame",
                    frame_options,
                )

                # ------------------------------------------------
                # LOAD VIDEO FRAME
                # ------------------------------------------------

                selected_video_frame = None

                if os.path.exists(
                    VIDEO_PATH
                ):

                    cap = cv2.VideoCapture(
                        VIDEO_PATH
                    )

                    cap.set(
                        cv2.CAP_PROP_POS_FRAMES,
                        selected_frame,
                    )

                    success, video_frame = cap.read()

                    cap.release()

                    if success:

                        selected_video_frame = cv2.cvtColor(
                            video_frame,
                            cv2.COLOR_BGR2RGB,
                        )

                if selected_video_frame is not None:

                    st.image(
                        selected_video_frame,
                        caption=(
                            f"Video Frame {selected_frame}"
                        ),
                        use_container_width=True,
                    )

                else:

                    st.warning(
                        "Selected video frame could not be loaded."
                    )

        st.caption(
            "The displayed source is a recorded video replay, "
            "not a live CCTV feed."
        )


# ============================================================
# ALERTS
# ============================================================

if page in ("Alerts", "Command Center"):

    st.header(
        "🚨 Operational Alerts"
    )

    # --------------------------------------------------------
    # OPERATIONAL ALERTS
    # --------------------------------------------------------

    try:

        alerts_response = load_alerts()

        alerts_df = dataframe_from_api(
            alerts_response,
            [
                "alerts",
                "data",
                "results",
            ],
        )

    except Exception as e:

        st.error(
            f"Operational alert error: {e}"
        )

        alerts_df = pd.DataFrame()

    if not alerts_df.empty:

        st.subheader(
            "Operational Risk Alerts"
        )

        st.dataframe(
            alerts_df,
            use_container_width=True,
            hide_index=True,
            height=450,
        )

    else:

        st.info(
            "No operational alerts available."
        )

    # --------------------------------------------------------
    # CROWD ALERTS
    # --------------------------------------------------------

    try:

        crowd_alert_response = load_crowd_alerts()

        crowd_alert_df = dataframe_from_api(
            crowd_alert_response,
            [
                "data",
                "alerts",
                "results",
            ],
        )

    except Exception as e:

        st.error(
            f"Crowd alert error: {e}"
        )

        crowd_alert_df = pd.DataFrame()

    st.divider()

    st.subheader(
        "Explainable Crowd Alerts"
    )

    if not crowd_alert_df.empty:

        st.warning(
            f"{len(crowd_alert_df)} analytical alert "
            "windows detected."
        )

        st.dataframe(
            crowd_alert_df,
            use_container_width=True,
            hide_index=True,
            height=400,
        )

    else:

        st.success(
            "No analytical crowd alert records available."
        )

    st.caption(
        "Alerts are generated from operational or exploratory "
        "crowd-intelligence signals and should not be interpreted "
        "as validated real-world safety predictions."
    )


# ============================================================
# CAMERA
# ============================================================

if page in ("Camera", "Command Center"):

    st.header(
        "📹 Camera Monitoring"
    )

    try:

        cameras_response = load_cameras()

    except Exception as e:

        st.error(
            f"Camera API error: {e}"
        )

        st.stop()

    camera_type = cameras_response.get(
        "camera_type",
        "UNKNOWN",
    )

    camera_count = safe_int(
        cameras_response.get(
            "camera_count",
            0,
        )
    )

    live_available = cameras_response.get(
        "live_camera_available",
        False,
    )

    human_review = cameras_response.get(
        "human_review_required",
        True,
    )

    autonomous_action = cameras_response.get(
        "autonomous_emergency_action",
        False,
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Camera Count",
            camera_count,
        )

    with c2:

        st.metric(
            "Live Camera",
            "AVAILABLE"
            if live_available
            else "NOT AVAILABLE",
        )

    with c3:

        st.metric(
            "Camera Mode",
            str(camera_type).upper(),
        )

    camera_data = cameras_response.get(
        "data",
        [],
    )

    if isinstance(
        camera_data,
        list,
    ):

        camera_df = pd.DataFrame(
            [
                x
                for x in camera_data
                if isinstance(x, dict)
            ]
        )

        if not camera_df.empty:

            st.subheader(
                "Camera Registry"
            )

            st.dataframe(
                camera_df,
                use_container_width=True,
                hide_index=True,
            )

    st.divider()

    st.info(
        "Current source is a recorded video replay. "
        "It does not represent a live CCTV feed."
    )

    st.warning(
        f"Human review required: "
        f"{'YES' if human_review else 'NO'}"
    )

    st.success(
        f"Autonomous emergency action: "
        f"{'ENABLED' if autonomous_action else 'DISABLED'}"
    )


# ============================================================
# ROUTING
# ============================================================

if page in ("Routing", "Command Center"):

    st.header(
        "🗺️ Risk-Aware Routing"
    )

    try:

        route_response = load_route()
        validation_response = load_route_validation()

    except Exception as e:

        st.error(
            f"Routing API error: {e}"
        )

        st.stop()

    st.warning(
        "Demonstration only — this is a simulated A* route. "
        "It is not a real-world, safety-validated evacuation route."
    )

    route = route_response.get(
        "route",
        [],
    )

    route_status = route_response.get(
        "status",
        "UNKNOWN",
    )

    route_type = route_response.get(
        "route_type",
        "Simulated A*",
    )

    frame = route_response.get(
        "frame",
        "—",
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Route Type",
            str(route_type),
        )

    with c2:

        st.metric(
            "Route Points",
            len(route)
            if isinstance(route, list)
            else 0,
        )

    with c3:

        st.metric(
            "Frame",
            display_value(frame),
        )

    st.subheader(
        "Route Status"
    )

    st.info(
        display_value(
            route_status
        )
    )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    st.subheader(
        "Route Validation"
    )

    obstacle_validation = validation_response.get(
        "obstacle_validation",
        validation_response.get(
            "obstacle_validation_status",
            "UNKNOWN",
        ),
    )

    continuity_validation = validation_response.get(
        "continuity_validation",
        validation_response.get(
            "continuity_validation_status",
            "UNKNOWN",
        ),
    )

    blocked_points = safe_int(
        validation_response.get(
            "blocked_points",
            0,
        )
    )

    invalid_steps = safe_int(
        validation_response.get(
            "invalid_consecutive_steps",
            0,
        )
    )

    v1, v2, v3, v4 = st.columns(4)

    with v1:

        st.metric(
            "Obstacle Validation",
            display_value(
                obstacle_validation
            ),
        )

    with v2:

        st.metric(
            "Continuity",
            display_value(
                continuity_validation
            ),
        )

    with v3:

        st.metric(
            "Blocked Points",
            blocked_points,
        )

    with v4:

        st.metric(
            "Invalid Steps",
            invalid_steps,
        )

    # --------------------------------------------------------
    # ROUTE TABLE
    # --------------------------------------------------------

    if isinstance(
        route,
        list,
    ) and route:

        route_df = pd.DataFrame(
            {
                "Point": range(
                    1,
                    len(route) + 1,
                ),
                "Position": [
                    str(point)
                    for point in route
                ],
            }
        )

        st.subheader(
            "Simulated Route Path"
        )

        st.dataframe(
            route_df,
            use_container_width=True,
            hide_index=True,
            height=350,
        )

    st.caption(
        "Routing currently uses a synthetic grid and A* "
        "demonstration. It is not connected to a real road "
        "network and has not been safety validated."
    )


# ============================================================
# SYSTEM
# ============================================================

if page in ("System", "Command Center"):

    st.header(
        "⚙️ System Status"
    )

    # --------------------------------------------------------
    # BACKEND
    # --------------------------------------------------------

    try:

        backend_health = api_get(
            "/api/health"
        )

        backend_ok = True

    except Exception:

        backend_health = {}

        backend_ok = False

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    try:

        database_health = api_get(
            "/api/database/health"
        )

        database_ok = True

    except Exception:

        database_health = {}

        database_ok = False

    # --------------------------------------------------------
    # PIPELINE
    # --------------------------------------------------------

    try:

        database_runs = api_get(
            "/api/database/runs"
        )

        runs_df = dataframe_from_api(
            database_runs,
            [
                "data",
                "runs",
                "results",
            ],
        )

    except Exception:

        runs_df = pd.DataFrame()

    c1, c2, c3 = st.columns(3)

    with c1:

        if backend_ok:

            st.success(
                "FastAPI: HEALTHY"
            )

        else:

            st.error(
                "FastAPI: UNAVAILABLE"
            )

    with c2:

        if database_ok:

            st.success(
                "SQLite: HEALTHY"
            )

        else:

            st.error(
                "SQLite: UNAVAILABLE"
            )

    with c3:

        st.info(
            "AI Pipeline: PRODUCTION"
        )

    st.divider()

    st.subheader(
        "Backend Health Response"
    )

    if backend_health:

        st.json(
            backend_health
        )

    st.subheader(
        "Database Health Response"
    )

    if database_health:

        st.json(
            database_health
        )

    st.subheader(
        "Pipeline Runs"
    )

    if not runs_df.empty:

        st.dataframe(
            runs_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No pipeline run records available."
        )

    st.divider()

    st.subheader(
        "System Safety Contract"
    )

    st.success(
        "Human review required"
    )

    st.success(
        "Autonomous emergency action disabled"
    )

    st.info(
        "Operational risk = rule-based decision support"
    )

    st.info(
        "Camera source = recorded replay"
    )

    st.info(
        "Routing = simulated A* demonstration"
    )

    st.warning(
        "Image-space movement measurements are not calibrated "
        "physical walking speeds."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "CrowdShield AI • Intelligent Multimodal Crowd Safety, "
    "Risk Prediction and Emergency Response System"
)

st.caption(
    "Research / engineering dashboard • "
    "Decision support only • Human review required"
)