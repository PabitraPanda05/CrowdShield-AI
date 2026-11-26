
"""
CrowdShield AI — Production Risk-Aware Routing Service

Purpose
-------
Provides a reusable routing component that evaluates candidate paths
using travel cost and operational crowd-risk exposure.

IMPORTANT
---------
This implementation is intended for decision-support and prototype
validation.

It does NOT represent:
- a validated emergency evacuation system
- a real road-network routing engine
- a safety guarantee
- an autonomous emergency command system
"""

from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from math import sqrt
from typing import Dict, Iterable, List, Optional, Tuple


Node = Tuple[int, int]


@dataclass
class RouteResult:
    """
    Result returned by the routing engine.
    """

    path: List[Node]
    travel_cost: float
    risk_cost: float
    combined_cost: float
    risk_reduction_percent: float
    path_length: int


class RiskAwareRouter:
    """
    Risk-aware A* router over a grid-like graph.

    The router combines:
        travel cost
        +
        risk exposure

    Risk values are expected to be normalized to [0, 1].
    """

    def __init__(
        self,
        risk_weight: float = 1.0,
        distance_weight: float = 1.0,
    ) -> None:

        if risk_weight < 0:
            raise ValueError(
                "risk_weight must be >= 0"
            )

        if distance_weight <= 0:
            raise ValueError(
                "distance_weight must be > 0"
            )

        self.risk_weight = float(
            risk_weight
        )

        self.distance_weight = float(
            distance_weight
        )

    # -----------------------------------------------------------------
    # Neighbour generation
    # -----------------------------------------------------------------

    @staticmethod
    def neighbors(
        node: Node,
        width: int,
        height: int,
        allow_diagonal: bool = False,
    ) -> Iterable[Tuple[Node, float]]:

        x, y = node

        directions = [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
        ]

        if allow_diagonal:

            directions.extend(
                [
                    (-1, -1),
                    (-1, 1),
                    (1, -1),
                    (1, 1),
                ]
            )

        for dx, dy in directions:

            nx = x + dx
            ny = y + dy

            if (
                0 <= nx < width
                and
                0 <= ny < height
            ):

                distance = sqrt(
                    dx * dx + dy * dy
                )

                yield (
                    (nx, ny),
                    distance,
                )

    # -----------------------------------------------------------------
    # Heuristic
    # -----------------------------------------------------------------

    @staticmethod
    def heuristic(
        node: Node,
        goal: Node,
    ) -> float:

        x1, y1 = node
        x2, y2 = goal

        return sqrt(
            (x2 - x1) ** 2
            +
            (y2 - y1) ** 2
        )

    # -----------------------------------------------------------------
    # Edge cost
    # -----------------------------------------------------------------

    def edge_cost(
        self,
        distance: float,
        risk: float,
    ) -> float:

        risk = max(
            0.0,
            min(1.0, float(risk))
        )

        return (
            self.distance_weight * distance
            +
            self.risk_weight * risk
        )

    # -----------------------------------------------------------------
    # Route search
    # -----------------------------------------------------------------

    def find_route(
        self,
        start: Node,
        goal: Node,
        risk_map: Dict[Node, float],
        width: int,
        height: int,
        allow_diagonal: bool = False,
    ) -> RouteResult:

        if not (
            0 <= start[0] < width
            and
            0 <= start[1] < height
        ):
            raise ValueError(
                "Start node is outside the routing grid."
            )

        if not (
            0 <= goal[0] < width
            and
            0 <= goal[1] < height
        ):
            raise ValueError(
                "Goal node is outside the routing grid."
            )

        if start == goal:

            return RouteResult(
                path=[start],
                travel_cost=0.0,
                risk_cost=0.0,
                combined_cost=0.0,
                risk_reduction_percent=0.0,
                path_length=1,
            )

        open_set = []

        heappush(
            open_set,
            (
                self.heuristic(
                    start,
                    goal,
                ),
                0.0,
                start,
            ),
        )

        came_from: Dict[
            Node,
            Optional[Node]
        ] = {
            start: None
        }

        g_score: Dict[
            Node,
            float
        ] = {
            start: 0.0
        }

        while open_set:

            _, current_cost, current = (
                heappop(open_set)
            )

            if current == goal:
                break

            if current_cost > g_score.get(
                current,
                float("inf"),
            ):
                continue

            for neighbor, distance in self.neighbors(
                current,
                width,
                height,
                allow_diagonal,
            ):

                risk = risk_map.get(
                    neighbor,
                    0.0,
                )

                step_cost = self.edge_cost(
                    distance,
                    risk,
                )

                tentative = (
                    g_score[current]
                    +
                    step_cost
                )

                if tentative < g_score.get(
                    neighbor,
                    float("inf"),
                ):

                    came_from[
                        neighbor
                    ] = current

                    g_score[
                        neighbor
                    ] = tentative

                    priority = (
                        tentative
                        +
                        self.heuristic(
                            neighbor,
                            goal,
                        )
                    )

                    heappush(
                        open_set,
                        (
                            priority,
                            tentative,
                            neighbor,
                        ),
                    )

        if goal not in came_from:

            raise RuntimeError(
                "No route could be found."
            )

        # -------------------------------------------------------------
        # Reconstruct path
        # -------------------------------------------------------------

        path = []

        current = goal

        while current is not None:

            path.append(current)

            current = came_from[current]

        path.reverse()

        # -------------------------------------------------------------
        # Calculate metrics
        # -------------------------------------------------------------

        travel_cost = 0.0
        risk_cost = 0.0

        for index in range(
            1,
            len(path),
        ):

            previous = path[
                index - 1
            ]

            current = path[
                index
            ]

            dx = (
                current[0]
                -
                previous[0]
            )

            dy = (
                current[1]
                -
                previous[1]
            )

            distance = sqrt(
                dx * dx
                +
                dy * dy
            )

            risk = max(
                0.0,
                min(
                    1.0,
                    float(
                        risk_map.get(
                            current,
                            0.0,
                        )
                    ),
                ),
            )

            travel_cost += distance
            risk_cost += risk

        combined_cost = (
            self.distance_weight
            * travel_cost
            +
            self.risk_weight
            * risk_cost
        )

        return RouteResult(
            path=path,
            travel_cost=travel_cost,
            risk_cost=risk_cost,
            combined_cost=combined_cost,
            risk_reduction_percent=0.0,
            path_length=len(path),
        )

    # -----------------------------------------------------------------
    # Route comparison
    # -----------------------------------------------------------------

    @staticmethod
    def compare_routes(
        baseline: RouteResult,
        risk_aware: RouteResult,
    ) -> Dict[str, float]:

        if baseline.risk_cost <= 0:

            risk_reduction = 0.0

        else:

            risk_reduction = (
                (
                    baseline.risk_cost
                    -
                    risk_aware.risk_cost
                )
                /
                baseline.risk_cost
            ) * 100.0

        if baseline.travel_cost <= 0:

            travel_change = 0.0

        else:

            travel_change = (
                (
                    risk_aware.travel_cost
                    -
                    baseline.travel_cost
                )
                /
                baseline.travel_cost
            ) * 100.0

        return {
            "baseline_travel_cost":
                float(
                    baseline.travel_cost
                ),

            "risk_aware_travel_cost":
                float(
                    risk_aware.travel_cost
                ),

            "baseline_risk_cost":
                float(
                    baseline.risk_cost
                ),

            "risk_aware_risk_cost":
                float(
                    risk_aware.risk_cost
                ),

            "risk_reduction_percent":
                float(
                    risk_reduction
                ),

            "travel_cost_change_percent":
                float(
                    travel_change
                ),
        }

    # -----------------------------------------------------------------
    # Batch route evaluation
    # -----------------------------------------------------------------

    def evaluate_candidates(
        self,
        start: Node,
        goal: Node,
        risk_maps: List[Dict[Node, float]],
        width: int,
        height: int,
        allow_diagonal: bool = False,
    ) -> List[RouteResult]:

        results = []

        for risk_map in risk_maps:

            result = self.find_route(
                start=start,
                goal=goal,
                risk_map=risk_map,
                width=width,
                height=height,
                allow_diagonal=allow_diagonal,
            )

            results.append(result)

        return results
