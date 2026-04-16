use aether_math::Vec4;
use rayon::prelude::*;

pub fn calculate_restoring_force(current: Vec4, target: Vec4, spring_constant: f32) -> Vec4 {
    let spring_constant = if !(0.0..=1e15).contains(&spring_constant) {
        0.1
    } else {
        spring_constant
    };

    let error = target - current;
    let mut force = error * spring_constant;

    let mag =
        (force.x * force.x + force.y * force.y + force.w * force.w + force.h * force.h).sqrt();
    if mag > 10000.0 {
        let scale = 10000.0 / mag;
        force.x *= scale;
        force.y *= scale;
        force.w *= scale;
        force.h *= scale;
    }

    force
}

pub fn calculate_boundary_forces(
    state: Vec4,
    container_w: f32,
    container_h: f32,
    boundary_stiffness: f32,
) -> Vec4 {
    let mut force = Vec4::ZERO;

    if state.x < 0.0 {
        force.x += (0.0 - state.x) * boundary_stiffness;
    } else if state.x + state.w > container_w {
        force.x -= ((state.x + state.w) - container_w) * boundary_stiffness;
    }

    if state.y < 0.0 {
        force.y += (0.0 - state.y) * boundary_stiffness;
    } else if state.y + state.h > container_h {
        force.y -= ((state.y + state.h) - container_h) * boundary_stiffness;
    }

    let mag =
        (force.x * force.x + force.y * force.y + force.w * force.w + force.h * force.h).sqrt();
    if mag > 5000.0 {
        let scale = 5000.0 / mag;
        force.x *= scale;
        force.y *= scale;
        force.w *= scale;
        force.h *= scale;
    }

    force
}

pub fn lerp(a: Vec4, b: Vec4, t: f32) -> Vec4 {
    a * (1.0 - t) + b * t
}

pub fn speed_to_stiffness(transition_time_ms: f32) -> f32 {
    if transition_time_ms <= 0.0 {
        return 0.1;
    }

    let mut t_sec = transition_time_ms / 1000.0;
    if t_sec < 0.001 {
        t_sec = 0.001;
    }

    let k = 16.0 / (t_sec * t_sec);
    k.min(10000.0)
}

pub fn speed_to_viscosity(transition_time_ms: f32) -> f32 {
    if transition_time_ms <= 0.0 {
        return 0.1;
    }

    let viscosity = 1.0 - (transition_time_ms / 1000.0);
    viscosity.clamp(0.05, 0.95)
}

pub fn batch_restoring_forces(
    states: &[Vec4],
    targets: &[Vec4],
    spring_k: f32,
    out_forces: &mut [Vec4],
) {
    out_forces
        .par_iter_mut()
        .zip(states.par_iter())
        .zip(targets.par_iter())
        .for_each(|((force, &state), &target)| {
            *force = calculate_restoring_force(state, target, spring_k);
        });
}

pub fn batch_boundary_forces(
    states: &[Vec4],
    container_w: f32,
    container_h: f32,
    boundary_k: f32,
    out_forces: &mut [Vec4],
) {
    out_forces
        .par_iter_mut()
        .zip(states.par_iter())
        .for_each(|(force, &state)| {
            *force = calculate_boundary_forces(state, container_w, container_h, boundary_k);
        });
}

pub fn batch_integrate(
    states: &mut [Vec4],
    velocities: &mut [Vec4],
    forces: &[Vec4],
    dt: f32,
    viscosity: f32,
    max_velocity: f32,
) {
    states
        .par_iter_mut()
        .zip(velocities.par_iter_mut())
        .zip(forces.par_iter())
        .for_each(|((state, vel), &force)| {
            let safe_force = force.sanitize();

            let damp = 1.0 - viscosity;

            let vx = (vel.x + safe_force.x * dt) * damp;
            let vy = (vel.y + safe_force.y * dt) * damp;
            let vw = (vel.w + safe_force.w * dt) * damp;
            let vh = (vel.h + safe_force.h * dt) * damp;

            let speed = (vx * vx + vy * vy).sqrt();
            let (vx, vy) = if speed > max_velocity && speed > 1e-9 {
                let scale = max_velocity / speed;
                (vx * scale, vy * scale)
            } else {
                (vx, vy)
            };

            state.x += vx * dt;
            state.y += vy * dt;
            state.w = (state.w + vw * dt).max(0.0);
            state.h = (state.h + vh * dt).max(0.0);

            *vel = Vec4::new(vx, vy, vw, vh);

            *state = state.sanitize();
            *vel = vel.sanitize();
        });
}
