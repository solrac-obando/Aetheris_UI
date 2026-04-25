// Aetheris UI - M12 Physics Kernel (WGSL)
// Copyright 2026 Carlos Ivan Obando Aure
// Standard WGSL implementation for cross-vendor GPU compute.

struct ElementState {
    x: f32,
    y: f32,
    w: f32,
    h: f32,
}

struct Velocity {
    vx: f32,
    vy: f32,
    vw: f32,
    vh: f32,
}

struct Config {
    lerp_factor: f32,
    container_w: f32,
    container_h: f32,
    dt: f32,
    viscosity: f32,
    boundary_k: f32,
    snap_dist: f32,
    snap_vel: f32,
}

@group(0) @binding(0) var<storage, read_write> states: array<ElementState>;
@group(0) @binding(1) var<storage, read_write> velocities: array<Velocity>;
@group(0) @binding(2) var<storage, read> targets: array<ElementState>;
@group(0) @binding(3) var<uniform> config: Config;

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) global_id: vec3<u32>) {
    let i = global_id.x;
    let n = arrayLength(&states);
    
    if (i >= n) {
        return;
    }

    var state = states[i];
    var vel = velocities[i];
    let target = targets[i];

    // 1. Calculate Restoring Force (Hooke's Law)
    // F = k * (target - current)
    // In our simplified model, we apply acceleration directly as a function of the offset
    let acc_x = (target.x - state.x) * config.lerp_factor;
    let acc_y = (target.y - state.y) * config.lerp_factor;
    let acc_w = (target.w - state.w) * config.lerp_factor;
    let acc_h = (target.h - state.h) * config.lerp_factor;

    // 2. Calculate Boundary Repulsion
    var b_force_x = 0.0;
    var b_force_y = 0.0;

    if (state.x < 0.0) {
        b_force_x += (0.0 - state.x) * config.boundary_k;
    } else if (state.x + state.w > config.container_w) {
        b_force_x -= ((state.x + state.w) - config.container_w) * config.boundary_k;
    }

    if (state.y < 0.0) {
        b_force_y += (0.0 - state.y) * config.boundary_k;
    } else if (state.y + state.h > config.container_h) {
        b_force_y -= ((state.y + state.h) - config.container_h) * config.boundary_k;
    }

    // 3. Symplectic Euler Integration
    let damp = 1.0 - config.viscosity;
    
    // Update Velocity: v = (v + a * dt) * (1 - viscosity)
    vel.vx = (vel.vx + (acc_x + b_force_x) * config.dt) * damp;
    vel.vy = (vel.vy + (acc_y + b_force_y) * config.dt) * damp;
    vel.vw = (vel.vw + acc_w * config.dt) * damp;
    vel.vh = (vel.vh + acc_h * config.dt) * damp;

    // Aether-Guard: Max Velocity Clamping (L2 Norm Approximation)
    let speed_sq = vel.vx * vel.vx + vel.vy * vel.vy;
    let max_v = 5000.0;
    if (speed_sq > max_v * max_v) {
        let speed = sqrt(speed_sq);
        vel.vx = (vel.vx / speed) * max_v;
        vel.vy = (vel.vy / speed) * max_v;
    }

    // Update State: s = s + v * dt
    state.x += vel.vx * config.dt;
    state.y += vel.vy * config.dt;
    state.w += vel.vw * config.dt;
    state.h += vel.vh * config.dt;

    // Ensure non-negative dimensions
    if (state.w < 0.0) { state.w = 0.0; }
    if (state.h < 0.0) { state.h = 0.0; }

    // 4. Epsilon Snapping (Aether-Guard)
    let dist_sq = (target.x - state.x) * (target.x - state.x) + (target.y - state.y) * (target.y - state.y);
    if (dist_sq < config.snap_dist * config.snap_dist && speed_sq < config.snap_vel * config.snap_vel) {
        state.x = target.x;
        state.y = target.y;
        state.w = target.w;
        state.h = target.h;
        vel.vx = 0.0;
        vel.vy = 0.0;
        vel.vw = 0.0;
        vel.vh = 0.0;
    }

    // 5. NaB Detection (Cero-Safe)
    if (is_not_finite(state.x) || is_not_finite(state.y)) {
        // Fallback: stay at target or reset if needed
        state.x = target.x;
        state.y = target.y;
    }

    // Output
    states[i] = state;
    velocities[i] = vel;
}

fn is_not_finite(v: f32) -> bool {
    // WGSL doesn't have is_finite directly in all targets, but we can check via comparison
    return v != v || v > 1e38 || v < -1e38;
}
