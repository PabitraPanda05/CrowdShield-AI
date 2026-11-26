from typing import Any, Dict


class ResponseDecisionEngine:
    """
    Production response-decision engine.

    Converts an operational risk state into an explainable
    monitoring / response recommendation.

    IMPORTANT:
        These are decision-support actions.
        They are not autonomous emergency commands.
    """

    VALID_LEVELS = {
        "LOW",
        "MODERATE",
        "HIGH",
        "CRITICAL",
    }

    def __init__(
        self,
        rising_growth_threshold: float = 0.50,
        high_risk_threshold: float = 50.0,
    ):
        if rising_growth_threshold < 0:
            raise ValueError(
                "rising_growth_threshold must be non-negative."
            )

        if high_risk_threshold < 0:
            raise ValueError(
                "high_risk_threshold must be non-negative."
            )

        self.rising_growth_threshold = float(
            rising_growth_threshold
        )

        self.high_risk_threshold = float(
            high_risk_threshold
        )

    # -----------------------------------------------------------------
    # Determine whether crowd conditions are rising
    # -----------------------------------------------------------------

    def is_rising(
        self,
        window: Dict[str, Any],
    ) -> bool:
        """
        Determine whether the current window contains
        a meaningful positive crowd-growth signal.
        """

        return bool(
            float(
                window.get(
                    "growth_load",
                    0.0,
                )
            )
            >= self.rising_growth_threshold
        )

    # -----------------------------------------------------------------
    # Determine independent operational signal
    # -----------------------------------------------------------------

    def has_independent_signal(
        self,
        window: Dict[str, Any],
    ) -> bool:
        """
        Detect an additional operational signal besides
        crowd growth.
        """

        return bool(
            window.get(
                "high_speed_signal",
                False,
            )
            or float(
                window.get(
                    "spatial_load",
                    0.0,
                )
            )
            >= 0.75
        )

    # -----------------------------------------------------------------
    # Response decision
    # -----------------------------------------------------------------

    def decide(
        self,
        risk_record: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Produce one response decision for a risk window.
        """

        level = str(
            risk_record[
                "operational_risk_level"
            ]
        ).upper()

        if level not in self.VALID_LEVELS:
            raise ValueError(
                f"Invalid operational risk level: {level}"
            )

        score = float(
            risk_record[
                "operational_risk_score"
            ]
        )

        rising = self.is_rising(
            risk_record
        )

        independent_signal = (
            self.has_independent_signal(
                risk_record
            )
        )

        movement_event = bool(
            risk_record.get(
                "movement_event_signal",
                0.0,
            )
        )

        # -------------------------------------------------------------
        # Response policy
        # -------------------------------------------------------------

        if level == "CRITICAL":

            action = (
                "CRITICAL MONITORING"
            )

            priority = "CRITICAL"

            reason = (
                "Critical operational risk index; "
                "maintain immediate human attention "
                "and verify conditions."
            )

        elif level == "HIGH" and rising:

            action = (
                "ESCALATED MONITORING"
            )

            priority = "HIGH"

            reason = (
                "High operational risk with increasing "
                "crowd load; escalate monitoring."
            )

        elif level == "HIGH":

            action = (
                "HIGH-PRIORITY MONITORING"
            )

            priority = "HIGH"

            reason = (
                "High operational risk index; "
                "maintain high-priority monitoring."
            )

        elif (
            level == "MODERATE"
            and rising
            and independent_signal
        ):

            action = (
                "PREPARE RESPONSE"
            )

            priority = "MEDIUM"

            reason = (
                "Moderate operational risk with increasing "
                "crowd load and an independent signal; "
                "prepare human response."
            )

        elif (
            level == "MODERATE"
            and independent_signal
        ):

            action = (
                "ACTIVE MONITORING"
            )

            priority = "MEDIUM"

            reason = (
                "Moderate operational risk with an "
                "additional operational signal; "
                "increase monitoring."
            )

        elif (
            level == "LOW"
            and rising
        ):

            action = "WATCH"

            priority = "LOW"

            reason = (
                "Low operational risk with increasing "
                "crowd load; continue observation."
            )

        elif level == "LOW":

            action = "ROUTINE MONITORING"

            priority = "LOW"

            reason = (
                "Low operational risk with no "
                "elevated operational signal."
            )

        else:

            action = "MONITOR"

            priority = "MEDIUM"

            reason = (
                "Moderate operational risk; "
                "continue monitoring."
            )

        # -------------------------------------------------------------
        # Additional signal description
        # -------------------------------------------------------------

        signals = []

        if rising:
            signals.append(
                "increasing crowd load"
            )

        if movement_event:
            signals.append(
                "movement event"
            )

        if float(
            risk_record.get(
                "spatial_load",
                0.0,
            )
        ) >= 0.75:
            signals.append(
                "high spatial concentration"
            )

        signal_summary = (
            ", ".join(signals)
            if signals
            else "none"
        )

        return {
            "window_id": int(
                risk_record["window_id"]
            ),

            "start_frame": int(
                risk_record["start_frame"]
            ),

            "end_frame": int(
                risk_record["end_frame"]
            ),

            "start_time": float(
                risk_record["start_time"]
            ),

            "end_time": float(
                risk_record["end_time"]
            ),

            "operational_risk_score": score,

            "operational_risk_level": level,

            "risk_dominant_factor": str(
                risk_record[
                    "dominant_risk_factor"
                ]
            ),

            "crowd_rising": rising,

            "independent_signal": (
                independent_signal
            ),

            "movement_event": movement_event,

            "response_action": action,

            "response_priority": priority,

            "response_reason": reason,

            "active_signals": signal_summary,

            "human_review_required": True,

            "autonomous_emergency_action": False,
        }

    # -----------------------------------------------------------------
    # Batch decisions
    # -----------------------------------------------------------------

    def decide_batch(
        self,
        risk_records,
    ):
        """
        Generate response decisions for multiple
        operational risk records.
        """

        return [
            self.decide(record)
            for record in risk_records
        ]
