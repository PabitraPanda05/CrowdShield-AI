import { useEffect, useMemo, useState } from "react";

import {
  AlertTriangle,
  CheckCircle2,
  Compass,
  Flag,
  Route,
  ShieldCheck,
  Target,
  Activity,
  Gauge,
  Camera,
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


export default function ResponseRouting({
  selectedCameraId,
  cameraIntelligence,
}) {
  const [routeData, setRouteData] = useState(null);
  const [validation, setValidation] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


  async function loadRoutingData() {
    try {
      setError("");

      const [
        routeResult,
        validationResult,
      ] = await Promise.all([
        api.simulatedRoute(),
        api.routeValidation(),
      ]);

      setRouteData(
        routeResult || null
      );

      setValidation(
        validationResult || null
      );

    } catch (err) {
      console.error(
        "Routing API error:",
        err
      );

      setError(
        "Unable to load routing data."
      );

    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadRoutingData();

    const timer = setInterval(
      () => {
        loadRoutingData();
      },
      10000
    );

    return () =>
      clearInterval(timer);
  }, []);


  const route =
    routeData?.route || [];


  const latestRisk =
    cameraIntelligence?.latest_risk || {};


  const currentRisk =
    Number(
      latestRisk.operational_risk_score ?? 0
    );


  const currentRiskLevel =
    latestRisk.operational_risk_level ||
    "UNKNOWN";


  const dominantFactor =
    latestRisk.dominant_risk_factor ||
    "—";


  const response =
    cameraIntelligence?.latest_response || {};


  const routeBounds = useMemo(() => {
    if (!route.length) {
      return {
        minX: 0,
        maxX: 1,
        minY: 0,
        maxY: 1,
      };
    }


    const xs = route.map(
      (point) =>
        Number(point.pixel_x)
    );

    const ys = route.map(
      (point) =>
        Number(point.pixel_y)
    );


    return {
      minX: Math.min(...xs),
      maxX: Math.max(...xs),
      minY: Math.min(...ys),
      maxY: Math.max(...ys),
    };

  }, [route]);


  function mapX(value) {
    const width =
      routeBounds.maxX -
        routeBounds.minX ||
      1;

    return (
      8 +
      ((value - routeBounds.minX) /
        width) *
        84
    );
  }


  function mapY(value) {
    const height =
      routeBounds.maxY -
        routeBounds.minY ||
      1;

    return (
      88 -
      ((value - routeBounds.minY) /
        height) *
        70
    );
  }


  if (!selectedCameraId) {
    return (
      <div className="cs-module">

        <div className="cs-module-placeholder">

          <Route size={30} />

          <h3>
            Response Routing
          </h3>

          <p>
            Select a camera to view its current
            risk context alongside the routing
            simulation.
          </p>

        </div>

      </div>
    );
  }


  if (loading) {
    return (
      <div className="cs-module">

        <div className="cs-module-placeholder">

          <Route size={30} />

          <h3>
            Loading Response Routing
          </h3>

          <p>
            Loading production routing simulation
            data...
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
          <Route size={28} />
        </div>


        <div>

          <div className="cs-module-kicker">
            RESPONSE / ROUTING
          </div>

          <h2>
            Response Routing
          </h2>

          <p>
            Risk-aware response context and
            simulated route planning for{" "}
            <strong>
              {selectedCameraId}
            </strong>
            .
          </p>

        </div>


        <div className="cs-module-status">

          <ShieldCheck size={13} />

          SIMULATION

        </div>

      </div>


      {error && (
        <div className="cs-error">

          <AlertTriangle size={16} />

          {error}

        </div>
      )}


      {/* CAMERA RISK CONTEXT */}

      <div className="cs-module-card">

        <div className="cs-module-card-header">

          <div>

            <h3>
              Selected Camera Risk Context
            </h3>

            <p>
              Live operational-risk information
              associated with the selected camera.
            </p>

          </div>


          <span className="cs-module-badge">

            {cameraIntelligence?.status ||
              "WAITING"}

          </span>

        </div>


        {!cameraIntelligence ? (

          <div className="cs-empty">

            <Activity size={17} />

            Waiting for selected camera
            intelligence...

          </div>

        ) : (

          <div className="cs-module-grid">

            <div className="cs-module-stat">

              <div className="cs-module-stat-icon">

                <Camera size={19} />

              </div>

              <span>
                CAMERA
              </span>

              <strong>
                {selectedCameraId}
              </strong>

              <small>
                {cameraIntelligence.camera_name ||
                  "Selected camera"}
              </small>

            </div>


            <div className="cs-module-stat">

              <div className="cs-module-stat-icon">

                <Gauge size={19} />

              </div>

              <span>
                CURRENT RISK
              </span>

              <strong>
                {format(
                  currentRisk,
                  1
                )}
              </strong>

              <small>
                {currentRiskLevel}
              </small>

            </div>


            <div className="cs-module-stat">

              <div className="cs-module-stat-icon">

                <Activity size={19} />

              </div>

              <span>
                DOMINANT FACTOR
              </span>

              <strong>
                {dominantFactor}
              </strong>

              <small>
                live camera signal
              </small>

            </div>


            <div className="cs-module-stat">

              <div className="cs-module-stat-icon">

                <ShieldCheck size={19} />

              </div>

              <span>
                RESPONSE
              </span>

              <strong>
                {response.response_action ||
                  "—"}
              </strong>

              <small>
                {response.response_priority ||
                  "—"}
              </small>

            </div>

          </div>

        )}

      </div>


      {/* SIMULATION WARNING */}

      <div className="cs-routing-warning">

        <AlertTriangle size={17} />

        <div>

          <strong>
            Simulation-only routing
          </strong>

          <span>
            The current route is generated from a
            simulated A* grid. It is not a real-world
            evacuation route, is not safety-validated,
            and must not be treated as an emergency
            navigation instruction. The selected
            camera risk shown above is live context;
            it does not alter this simulated route.
          </span>

        </div>

      </div>


      {/* SUMMARY */}

      <div className="cs-module-grid">

        <div className="cs-module-stat">

          <div className="cs-module-stat-icon">
            <Route size={19} />
          </div>

          <span>
            ROUTE POINTS
          </span>

          <strong>
            {routeData?.total_points ??
              route.length}
          </strong>

          <small>
            simulated path
          </small>

        </div>


        <div className="cs-module-stat">

          <div className="cs-module-stat-icon">
            <Target size={19} />
          </div>

          <span>
            START
          </span>

          <strong className="cs-route-coordinate">

            {validation?.start_point
              ? `${validation.start_point[0]}, ${validation.start_point[1]}`
              : "—"}

          </strong>

          <small>
            grid coordinate
          </small>

        </div>


        <div className="cs-module-stat">

          <div className="cs-module-stat-icon">
            <Flag size={19} />
          </div>

          <span>
            DESTINATION
          </span>

          <strong className="cs-route-coordinate">

            {validation?.destination_point
              ? `${validation.destination_point[0]}, ${validation.destination_point[1]}`
              : "—"}

          </strong>

          <small>
            grid coordinate
          </small>

        </div>


        <div className="cs-module-stat">

          <div className="cs-module-stat-icon">
            <CheckCircle2 size={19} />
          </div>

          <span>
            OBSTACLE CHECK
          </span>

          <strong>
            {validation?.blocked_cells_on_route ??
              "—"}
          </strong>

          <small>
            blocked cells
          </small>

        </div>


        <div className="cs-module-stat">

          <div className="cs-module-stat-icon">
            <Compass size={19} />
          </div>

          <span>
            CONTINUITY
          </span>

          <strong>
            {validation?.invalid_consecutive_steps ??
              "—"}
          </strong>

          <small>
            invalid steps
          </small>

        </div>


        <div className="cs-module-stat">

          <div className="cs-module-stat-icon">
            <ShieldCheck size={19} />
          </div>

          <span>
            VALIDATION
          </span>

          <strong>

            {validation?.obstacle_validation ===
              "PASSED" &&
            validation?.continuity_validation ===
              "PASSED"
              ? "PASSED"
              : "CHECK"}

          </strong>

          <small>
            simulation validation
          </small>

        </div>

      </div>


      {/* ROUTE VISUALIZATION */}

      <div className="cs-module-card">

        <div className="cs-module-card-header">

          <div>

            <h3>
              Simulated A* Route
            </h3>

            <p>
              Grid representation of the generated
              simulation route.
            </p>

          </div>

          <span className="cs-module-badge">

            FRAME{" "}
            {routeData?.frame ?? "—"}

          </span>

        </div>


        <div className="cs-route-map">

          <div className="cs-route-grid">

            {route.map(
              (point, index) => {

                const x =
                  mapX(
                    Number(
                      point.pixel_x
                    )
                  );

                const y =
                  mapY(
                    Number(
                      point.pixel_y
                    )
                  );

                const first =
                  index === 0;

                const last =
                  index ===
                  route.length - 1;


                return (
                  <div
                    key={`${point.grid_x}-${point.grid_y}-${index}`}
                    className={
                      first
                        ? "cs-route-point cs-route-start"
                        : last
                        ? "cs-route-point cs-route-end"
                        : "cs-route-point"
                    }
                    style={{
                      left: `${x}%`,
                      top: `${y}%`,
                    }}
                    title={
                      first
                        ? "Start point"
                        : last
                        ? "Destination"
                        : `Route point ${index + 1}`
                    }
                  />
                );
              }
            )}


            {route.length > 1 && (

              <svg
                className="cs-route-svg"
                viewBox="0 0 100 100"
                preserveAspectRatio="none"
              >

                <polyline
                  points={route
                    .map(
                      (point) => {

                        const x =
                          mapX(
                            Number(
                              point.pixel_x
                            )
                          );

                        const y =
                          mapY(
                            Number(
                              point.pixel_y
                            )
                          );

                        return `${x},${y}`;
                      }
                    )
                    .join(" ")}
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="1.1"
                  vectorEffect="non-scaling-stroke"
                />

              </svg>

            )}


            <div className="cs-route-label cs-route-label-start">
              START
            </div>

            <div className="cs-route-label cs-route-label-end">
              DESTINATION
            </div>

          </div>

        </div>


        <div className="cs-route-legend">

          <span>
            <i className="route-dot route-dot-start" />
            Start
          </span>

          <span>
            <i className="route-dot route-dot-path" />
            Simulated route
          </span>

          <span>
            <i className="route-dot route-dot-end" />
            Destination
          </span>

        </div>

      </div>


      {/* VALIDATION */}

      <div className="cs-module-two-column">

        <div className="cs-module-card">

          <div className="cs-module-card-header">

            <div>

              <h3>
                Route Validation
              </h3>

              <p>
                Structural checks returned by the
                backend.
              </p>

            </div>


            <span className="cs-validation-pass">

              <CheckCircle2 size={13} />

              {validation?.status ||
                "UNKNOWN"}

            </span>

          </div>


          <div className="cs-module-list">

            <div className="cs-module-list-row">

              <span>
                Start point
              </span>

              <strong>
                {validation?.start_correct
                  ? "CORRECT"
                  : "CHECK"}
              </strong>

            </div>


            <div className="cs-module-list-row">

              <span>
                Destination point
              </span>

              <strong>
                {validation?.destination_correct
                  ? "CORRECT"
                  : "CHECK"}
              </strong>

            </div>


            <div className="cs-module-list-row">

              <span>
                Obstacle validation
              </span>

              <strong>
                {validation?.obstacle_validation}
              </strong>

            </div>


            <div className="cs-module-list-row">

              <span>
                Continuity validation
              </span>

              <strong>
                {validation?.continuity_validation}
              </strong>

            </div>


            <div className="cs-module-list-row">

              <span>
                Blocked cells
              </span>

              <strong>
                {validation?.blocked_cells_on_route}
              </strong>

            </div>


            <div className="cs-module-list-row">

              <span>
                Invalid consecutive steps
              </span>

              <strong>
                {validation?.invalid_consecutive_steps}
              </strong>

            </div>

          </div>

        </div>


        {/* ROUTE METADATA */}

        <div className="cs-module-card">

          <div className="cs-module-card-header">

            <div>

              <h3>
                Route Metadata
              </h3>

              <p>
                Current routing simulation metadata.
              </p>

            </div>

          </div>


          <div className="cs-module-list">

            <div className="cs-module-list-row">

              <span>
                Route type
              </span>

              <strong>
                {routeData?.route_type ||
                  "—"}
              </strong>

            </div>


            <div className="cs-module-list-row">

              <span>
                Frame
              </span>

              <strong>
                {routeData?.frame ??
                  "—"}
              </strong>

            </div>


            <div className="cs-module-list-row">

              <span>
                Total points
              </span>

              <strong>
                {routeData?.total_points ??
                  "—"}
              </strong>

            </div>


            <div className="cs-module-list-row">

              <span>
                Source status
              </span>

              <strong>
                Simulation only
              </strong>

            </div>


            <div className="cs-module-list-row">

              <span>
                Safety validation
              </span>

              <strong>
                Not validated
              </strong>

            </div>

          </div>

        </div>

      </div>


      {/* DISCLAIMER */}

      <div className="cs-module-disclaimer">

        <AlertTriangle size={15} />

        <div>

          <strong>
            Routing limitation
          </strong>

          <span>
            The current implementation demonstrates A*
            routing on a simulated grid. Successful
            obstacle and continuity checks confirm only
            the structural validity of this simulation.
            They do not establish real-world evacuation
            safety or emergency routing suitability.
            The selected camera's live risk is displayed
            as operational context only and does not
            automatically modify the simulated route.
          </span>

        </div>

      </div>

    </div>
  );
}