"""V2 stream validation helpers."""

from __future__ import annotations

import math

from certgen.stats.design_contracts import ComparisonStream


def validate_direction_convention(stream: ComparisonStream) -> bool:
    return stream.direction == "negative_mean_A_better_positive_mean_B_better"


def require_bounded_stream(stream: ComparisonStream) -> None:
    if not stream.bounded or stream.lower_bound is None or stream.upper_bound is None:
        raise ValueError("bounded stream with explicit lower/upper bounds is required")
    if stream.lower_bound >= stream.upper_bound:
        raise ValueError("stream lower_bound must be smaller than upper_bound")
    for value in stream.values:
        if not math.isfinite(value):
            raise ValueError("stream contains a non-finite value")
        if value < stream.lower_bound or value > stream.upper_bound:
            raise ValueError("stream value outside declared bounds")
