import numpy as np
import pytest

from core.aether_math import StateTensor
from core.solver import calculate_restoring_force, calculate_boundary_forces


def test_tensor_integration():
    """Test StateTensor applies force and integrates correctly."""
    tensor = StateTensor(0.0, 0.0, 10.0, 10.0)

    # Apply force [10, 0, 0, 0] (push right)
    tensor.apply_force(np.array([10.0, 0.0, 0.0, 0.0], dtype=np.float32))

    # Integrate with no viscosity (viscosity=0.0) and dt=1.0
    tensor.euler_integrate(dt=1.0, viscosity=0.0)

    # After integration: velocity = (0 + 10*1) * (1 - 0) = [10, 0, 0, 0]
    # state = [0,0,10,10] + [10,0,0,0] * 1 = [10, 0, 10, 10]
    assert tensor.velocity[0] == pytest.approx(10.0, abs=1e-5)
    assert tensor.state[0] == pytest.approx(10.0, abs=1e-5)


def test_solver_hookes_law():
    """Test Hooke's law restoring force calculation."""
    current = np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32)
    target = np.array([100.0, 0.0, 0.0, 0.0], dtype=np.float32)
    spring_constant = 0.1

    force = calculate_restoring_force(current, target, spring_constant)

    # Force = (target - current) * k = ([100,0,0,0] - [0,0,0,0]) * 0.1 = [10,0,0,0]
    assert force[0] == pytest.approx(10.0, abs=1e-5)
    assert force[1] == pytest.approx(0.0, abs=1e-5)
    assert force[2] == pytest.approx(0.0, abs=1e-5)
    assert force[3] == pytest.approx(0.0, abs=1e-5)


def test_boundary_forces():
    """Test boundary repulsion forces push element back into container."""
    # Element at x=-10 (outside left boundary)
    state = np.array([-10.0, 50.0, 100.0, 100.0], dtype=np.float32)
    container_w = 800.0
    container_h = 600.0
    boundary_stiffness = 1.0

    force = calculate_boundary_forces(state, container_w, container_h, boundary_stiffness)

    # Left boundary crossed: force[0] = (0 - (-10)) * 1.0 = 10.0 (positive push right)
    assert force[0] == pytest.approx(10.0, abs=1e-5)
    # Y is within bounds, no force
    assert force[1] == pytest.approx(0.0, abs=1e-5)
