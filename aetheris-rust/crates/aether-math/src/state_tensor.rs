use crate::aether_guard::*;
use crate::vec4::Vec4;

#[derive(Clone, Debug)]
pub struct StateTensor {
    pub state: Vec4,
    pub velocity: Vec4,
    pub acceleration: Vec4,
}

impl StateTensor {
    pub fn new(x: f32, y: f32, w: f32, h: f32) -> Self {
        StateTensor {
            state: Vec4::new(x, y, w, h),
            velocity: Vec4::ZERO,
            acceleration: Vec4::ZERO,
        }
    }

    pub fn apply_force(&mut self, force: Vec4) {
        let safe_force = force.sanitize();
        self.acceleration = self.acceleration + safe_force;
        self.acceleration = clamp_acceleration(self.acceleration);
    }

    pub fn euler_integrate(&mut self, dt: f32, viscosity: f32, target: Option<&Vec4>) {
        let safe_dt = sanitize_dt(dt);

        self.velocity = (self.velocity + self.acceleration * safe_dt) * (1.0 - viscosity);
        self.velocity = clamp_velocity(self.velocity);

        self.state = self.state + self.velocity * safe_dt;

        if self.state.w < 0.0 {
            self.state.w = 0.0;
        }
        if self.state.h < 0.0 {
            self.state.h = 0.0;
        }

        self.acceleration = Vec4::ZERO;

        self.state = self.state.sanitize();
        self.velocity = self.velocity.sanitize();

        if let Some(t) = target {
            if check_snap(&self.state, t, &self.velocity) {
                self.state = *t;
                self.velocity = Vec4::ZERO;
            }
        }
    }
}
