use crate::Vec4;

pub const EPSILON: f32 = 1e-9;
pub const MAX_VELOCITY: f32 = 5000.0;
pub const MAX_ACCELERATION: f32 = 10000.0;
pub const SNAP_DISTANCE: f32 = 0.5;
pub const SNAP_VELOCITY: f32 = 5.0;
pub const MAX_PHYSICS_K: f32 = 10000.0;
pub const SAFE_DT_MIN: f32 = 0.0;
pub const SAFE_DT_MAX: f32 = 1.0;

pub fn safe_divide(numerator: f32, denominator: f32) -> f32 {
    let denom = denominator.abs().max(EPSILON);
    let sign = denominator.signum();
    let safe_sign = if sign == 0.0 { 1.0 } else { sign };
    numerator / (denom * safe_sign)
}

pub fn clamp_velocity(v: Vec4) -> Vec4 {
    v.clamp_magnitude(MAX_VELOCITY)
}

pub fn clamp_acceleration(a: Vec4) -> Vec4 {
    a.clamp_magnitude(MAX_ACCELERATION)
}

pub fn clamp_force(f: Vec4) -> Vec4 {
    f.clamp_magnitude(MAX_PHYSICS_K)
}

pub fn sanitize_dt(dt: f32) -> f32 {
    let safe = safe_divide(dt, 1.0);
    safe.clamp(SAFE_DT_MIN, SAFE_DT_MAX)
}

pub fn check_snap(state: &Vec4, target: &Vec4, velocity: &Vec4) -> bool {
    state.distance_to(target) < SNAP_DISTANCE && velocity.magnitude() < SNAP_VELOCITY
}
