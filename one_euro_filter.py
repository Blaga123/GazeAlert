"""
One Euro Filter (1€ Filter) implementation for real-time jitter reduction and zero-lag tracking.
Reference: Casiez, G., Roussel, N., and Vogel, D. (ACM CHI 2012).
"""

import math
import time
from typing import Optional, Tuple, Union


class LowPassFilter:
    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.s: Optional[float] = None

    def filter(self, value: float, alpha: Optional[float] = None) -> float:
        if alpha is not None:
            self.alpha = alpha
        if self.s is None:
            self.s = value
        else:
            self.s = self.alpha * value + (1.0 - self.alpha) * self.s
        return self.s

    def reset(self):
        self.s = None


class OneEuroFilter:
    """
    1-Euro Filter for 1D float signal.
    - min_cutoff: Lower values decrease jitter when stationary.
    - beta: Higher values decrease lag during fast movements.
    - d_cutoff: Cutoff frequency for derivative filtering.
    """
    def __init__(
        self,
        min_cutoff: float = 0.8,
        beta: float = 0.007,
        d_cutoff: float = 1.0,
    ):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff

        self.x_filter = LowPassFilter()
        self.dx_filter = LowPassFilter()
        self.last_time: Optional[float] = None

    def _alpha(self, dt: float, cutoff: float) -> float:
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def filter(self, x: float, timestamp: Optional[float] = None) -> float:
        if timestamp is None:
            timestamp = time.time()

        if self.last_time is None:
            self.last_time = timestamp
            self.dx_filter.filter(0.0)
            return self.x_filter.filter(x)

        dt = max(1e-4, timestamp - self.last_time)
        self.last_time = timestamp

        # Filter derivative (velocity)
        prev_x = self.x_filter.s if self.x_filter.s is not None else x
        dx = (x - prev_x) / dt
        a_d = self._alpha(dt, self.d_cutoff)
        filtered_dx = self.dx_filter.filter(dx, a_d)

        # Dynamic cutoff frequency
        cutoff = self.min_cutoff + self.beta * abs(filtered_dx)
        a_x = self._alpha(dt, cutoff)

        return self.x_filter.filter(x, a_x)

    def reset(self):
        self.x_filter.reset()
        self.dx_filter.reset()
        self.last_time = None


class OneEuroFilter2D:
    """Convenience wrapper for 2D coordinates (e.g. Iris X, Y or Screen X, Y)."""
    def __init__(self, min_cutoff: float = 0.8, beta: float = 0.007, d_cutoff: float = 1.0):
        self.fx = OneEuroFilter(min_cutoff, beta, d_cutoff)
        self.fy = OneEuroFilter(min_cutoff, beta, d_cutoff)

    def filter(self, pt: Tuple[float, float], timestamp: Optional[float] = None) -> Tuple[float, float]:
        return (
            self.fx.filter(pt[0], timestamp),
            self.fy.filter(pt[1], timestamp)
        )

    def reset(self):
        self.fx.reset()
        self.fy.reset()
