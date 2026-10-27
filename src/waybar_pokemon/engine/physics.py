"""Falling and jumping: vertical motion above the ground (y = 0, negative
y is higher)."""

GRAVITY = 400.0  # pixels per second²


def fall(y: float, velocity: float, dt: float) -> tuple[float, float]:
    """The height and vertical velocity after dt seconds; stops on the ground."""
    velocity += GRAVITY * dt
    return min(0.0, y + velocity * dt), velocity
