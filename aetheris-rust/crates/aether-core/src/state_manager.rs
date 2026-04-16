use aether_math::Vec4;

pub struct StateManager {
    last_width: f32,
    last_height: f32,
    hyper_damping_frames: u32,
}

impl Default for StateManager {
    fn default() -> Self {
        Self::new()
    }
}

impl StateManager {
    pub fn new() -> Self {
        StateManager {
            last_width: 0.0,
            last_height: 0.0,
            hyper_damping_frames: 0,
        }
    }

    pub fn check_teleportation_shock(&mut self, current_w: f32, current_h: f32) -> f32 {
        if self.last_width == 0.0 {
            self.last_width = current_w;
            self.last_height = current_h;
            return 1.0;
        }

        let delta_w = (current_w - self.last_width).abs();
        self.last_width = current_w;
        self.last_height = current_h;

        if delta_w > 200.0 {
            self.hyper_damping_frames = 15;
        }

        if self.hyper_damping_frames > 0 {
            self.hyper_damping_frames -= 1;
            return 5.0;
        }

        1.0
    }

    pub fn lerp(a: Vec4, b: Vec4, t: f32) -> Vec4 {
        a * (1.0 - t) + b * t
    }
}
