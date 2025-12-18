"""Timing middleware for Taiga MCP Server.

This middleware provides detailed timing information for requests
to help identify performance bottlenecks.
"""

import time
from typing import Any

from fastmcp.server.middleware import Middleware

from src.infrastructure.logging import get_logger


logger = get_logger("middleware.timing")


class TimingStats:
    """Statistics container for timing data.

    Tracks min, max, average, and percentile timing information.
    """

    def __init__(self, max_samples: int = 1000) -> None:
        """Initialize timing stats.

        Args:
            max_samples: Maximum number of samples to keep.
        """
        self.max_samples = max_samples
        self._samples: list[float] = []
        self._total_time = 0.0
        self._total_count = 0

    def add_sample(self, duration: float) -> None:
        """Add a timing sample.

        Args:
            duration: Duration in seconds.
        """
        self._total_time += duration
        self._total_count += 1

        self._samples.append(duration)
        if len(self._samples) > self.max_samples:
            self._samples.pop(0)

    @property
    def count(self) -> int:
        """Get total request count."""
        return self._total_count

    @property
    def average(self) -> float:
        """Get average duration."""
        if self._total_count == 0:
            return 0.0
        return self._total_time / self._total_count

    @property
    def min_time(self) -> float:
        """Get minimum duration from recent samples."""
        if not self._samples:
            return 0.0
        return min(self._samples)

    @property
    def max_time(self) -> float:
        """Get maximum duration from recent samples."""
        if not self._samples:
            return 0.0
        return max(self._samples)

    def percentile(self, p: float) -> float:
        """Get percentile duration from recent samples.

        Args:
            p: Percentile (0-100).

        Returns:
            Duration at the given percentile.
        """
        if not self._samples:
            return 0.0
        sorted_samples = sorted(self._samples)
        index = int(len(sorted_samples) * p / 100)
        index = min(index, len(sorted_samples) - 1)
        return sorted_samples[index]

    def to_dict(self) -> dict[str, float]:
        """Convert stats to dictionary.

        Returns:
            Dictionary with timing statistics.
        """
        return {
            "count": self.count,
            "average_ms": self.average * 1000,
            "min_ms": self.min_time * 1000,
            "max_ms": self.max_time * 1000,
            "p50_ms": self.percentile(50) * 1000,
            "p95_ms": self.percentile(95) * 1000,
            "p99_ms": self.percentile(99) * 1000,
        }


class TimingMiddleware(Middleware):
    """Middleware for tracking request timing.

    Measures the duration of each request and provides statistics
    for monitoring and optimization.

    Attributes:
        slow_threshold_ms: Threshold for logging slow requests.
        track_by_tool: Whether to track timing per tool.
    """

    def __init__(
        self,
        slow_threshold_ms: float = 1000.0,
        track_by_tool: bool = True,
        max_samples_per_tool: int = 1000,
    ) -> None:
        """Initialize timing middleware.

        Args:
            slow_threshold_ms: Threshold for slow request warnings.
            track_by_tool: Whether to track timing per tool.
            max_samples_per_tool: Maximum samples per tool.
        """
        self.slow_threshold_ms = slow_threshold_ms
        self.track_by_tool = track_by_tool
        self.max_samples_per_tool = max_samples_per_tool

        # Global timing stats
        self._global_stats = TimingStats(max_samples=10000)

        # Per-tool timing stats
        self._tool_stats: dict[str, TimingStats] = {}

    async def on_call_tool(
        self,
        context: Any,
        call_next: Any,
    ) -> Any:
        """Handle tool calls with timing measurement.

        Args:
            context: The middleware context.
            call_next: Function to call the next middleware.

        Returns:
            The result from the tool.
        """
        # Get tool name
        tool_name = "unknown"
        params = getattr(context.request, "params", None)
        if params and hasattr(params, "name"):
            tool_name = params.name

        start_time = time.perf_counter()
        try:
            return await call_next(context)
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            duration_ms = duration * 1000

            # Record timing
            self._global_stats.add_sample(duration)

            if self.track_by_tool:
                if tool_name not in self._tool_stats:
                    self._tool_stats[tool_name] = TimingStats(max_samples=self.max_samples_per_tool)
                self._tool_stats[tool_name].add_sample(duration)

            # Log slow requests
            if duration_ms > self.slow_threshold_ms:
                logger.warning(
                    f"Slow request: {tool_name} took {duration_ms:.2f}ms",
                    extra={
                        "tool_name": tool_name,
                        "duration_ms": duration_ms,
                        "threshold_ms": self.slow_threshold_ms,
                    },
                )
            else:
                logger.debug(
                    f"Request timing: {tool_name} took {duration_ms:.2f}ms",
                    extra={
                        "tool_name": tool_name,
                        "duration_ms": duration_ms,
                    },
                )

    def get_global_stats(self) -> dict[str, float]:
        """Get global timing statistics.

        Returns:
            Dictionary with global timing stats.
        """
        return self._global_stats.to_dict()

    def get_tool_stats(self, tool_name: str) -> dict[str, float] | None:
        """Get timing statistics for a specific tool.

        Args:
            tool_name: Name of the tool.

        Returns:
            Dictionary with tool timing stats, or None if not tracked.
        """
        stats = self._tool_stats.get(tool_name)
        if stats:
            return stats.to_dict()
        return None

    def get_all_stats(self) -> dict[str, Any]:
        """Get all timing statistics.

        Returns:
            Dictionary with all timing stats.
        """
        return {
            "global": self.get_global_stats(),
            "by_tool": {name: stats.to_dict() for name, stats in self._tool_stats.items()},
        }

    def get_slowest_tools(self, n: int = 10) -> list[tuple[str, float]]:
        """Get the slowest tools by average duration.

        Args:
            n: Number of tools to return.

        Returns:
            List of (tool_name, average_ms) tuples.
        """
        tools_with_avg = [(name, stats.average * 1000) for name, stats in self._tool_stats.items()]
        tools_with_avg.sort(key=lambda x: x[1], reverse=True)
        return tools_with_avg[:n]

    def reset_stats(self) -> None:
        """Reset all timing statistics."""
        self._global_stats = TimingStats(max_samples=10000)
        self._tool_stats.clear()
