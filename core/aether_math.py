import numpy as np


class StateTensor:
    """Aetheris UI treats UI elements as physical particles.

    Each element has a state vector [x, y, width, height] and evolves
    through velocity and acceleration using Euler integration with
    viscosity (friction) for stability.
    """

    def __init__(self, x: float = 0.0, y: float = 0.0, w: float = 100.0, h: float = 100.0):
        # Initialize the 3 core vectors as float32 for OpenGL compatibility
        self.state = np.array([x, y, w, h], dtype=np.float32)
        self.velocity = np.zeros(4, dtype=np.float32)
        self.acceleration = np.zeros(4, dtype=np.float32)

    def apply_force(self, force: np.ndarray):
        """Apply a force vector to acceleration.

        Assumes mass m=1, so F = ma becomes F = a.
        Force adds to existing acceleration (forces accumulate).
        """
        self.acceleration += force.astype(np.float32)

    def euler_integrate(self, dt: float, viscosity: float = 0.1, target_state: np.ndarray = None):
        """Update physics state using Euler integration.

        1. Update velocity with acceleration and apply friction (viscosity)
        2. Update position state based on velocity
        3. Clamp width and height to prevent negative dimensions
        4. Reset acceleration to zero for next frame
        5. Apply UI Snap Threshold (99% Rule): if close enough to target, snap to save computation
        """
        # Store current state for distance calculation
        current_state = self.state.copy()
        
        # 1. Update velocity with friction: v_new = (v + a * dt) * (1 - viscosity)
        self.velocity = (self.velocity + self.acceleration * dt) * np.float32(1.0 - viscosity)

        # 2. Update state: s_new = s + v * dt
        self.state = self.state + self.velocity * dt

        # 3. Clamp width and height to >= 0.0 (safety constraint)
        self.state[2] = max(self.state[2], np.float32(0.0))
        self.state[3] = max(self.state[3], np.float32(0.0))

        # 4. Reset acceleration to zero (prevents infinite accumulation)
        self.acceleration.fill(np.float32(0.0))
        
        # 5. Apply UI Snap Threshold (99% Rule/Epsilon Snapping)
        # If we have a target state and are close enough, snap to save computation
        if target_state is not None:
            # Calculate distance to target (L2 norm of position and size differences)
            distance = np.linalg.norm(self.state - target_state)
            # Velocity magnitude
            velocity_magnitude = np.linalg.norm(self.velocity)
            
            # Snap conditions: within 0.5 pixels AND moving slowly (< 5.0 px/s)
            if distance < 0.5 and velocity_magnitude < 5.0:
                self.state = target_state.copy()
                self.velocity.fill(np.float32(0.0))
                # Note: acceleration is already zero from line above