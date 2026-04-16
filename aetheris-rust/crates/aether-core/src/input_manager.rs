use aether_math::Vec4;
use std::collections::VecDeque;

pub struct InputManager {
    is_dragging: bool,
    dragged_element_index: Option<usize>,
    pointer_x: f32,
    pointer_y: f32,
    position_history: VecDeque<(f32, f32, f64)>,
}

impl Default for InputManager {
    fn default() -> Self {
        Self::new()
    }
}

impl InputManager {
    const DRAG_STIFFNESS: f32 = 5.0;
    #[allow(dead_code)]
    const DRAG_DAMPING: f32 = 0.3;
    const THROW_VELOCITY_SCALE: f32 = 1.0;
    const HISTORY_SIZE: usize = 5;

    pub fn new() -> Self {
        InputManager {
            is_dragging: false,
            dragged_element_index: None,
            pointer_x: 0.0,
            pointer_y: 0.0,
            position_history: VecDeque::with_capacity(Self::HISTORY_SIZE),
        }
    }

    pub fn is_dragging(&self) -> bool {
        self.is_dragging
    }

    pub fn dragged_element_index(&self) -> Option<usize> {
        self.dragged_element_index
    }

    pub fn pointer_down(&mut self, element_index: usize, x: f32, y: f32, timestamp: f64) {
        self.is_dragging = true;
        self.dragged_element_index = Some(element_index);
        self.pointer_x = x;
        self.pointer_y = y;
        self.position_history.clear();
        self.position_history.push_back((x, y, timestamp));
    }

    pub fn pointer_move(&mut self, x: f32, y: f32, timestamp: f64) {
        self.pointer_x = x;
        self.pointer_y = y;
        self.position_history.push_back((x, y, timestamp));
        if self.position_history.len() > Self::HISTORY_SIZE {
            self.position_history.pop_front();
        }
    }

    pub fn pointer_up(&mut self) {
        self.is_dragging = false;
        self.dragged_element_index = None;
    }

    pub fn get_throw_velocity(&self) -> (f32, f32) {
        let len = self.position_history.len();
        if len < 2 {
            return (0.0, 0.0);
        }

        let (vx, vy) = if len < 3 {
            let (px_curr, py_curr, t_curr) = self.position_history[len - 1];
            let (px_prev, py_prev, t_prev) = self.position_history[len - 2];
            let dt = (t_curr - t_prev) as f32;
            if dt.abs() < 1e-9 {
                (0.0, 0.0)
            } else {
                ((px_curr - px_prev) / dt, (py_curr - py_prev) / dt)
            }
        } else {
            let (px_curr, py_curr, t_curr) = self.position_history[len - 1];
            let (px_prev, py_prev, t_prev) = self.position_history[len - 2];
            let (px_prev2, py_prev2, _t_prev2) = self.position_history[len - 3];
            let dt = (t_curr - t_prev) as f32;
            if dt.abs() < 1e-9 {
                (0.0, 0.0)
            } else {
                let vx = (3.0 * px_curr - 4.0 * px_prev + px_prev2) / (2.0 * dt);
                let vy = (3.0 * py_curr - 4.0 * py_prev + py_prev2) / (2.0 * dt);
                (vx, vy)
            }
        };

        (
            vx * Self::THROW_VELOCITY_SCALE,
            vy * Self::THROW_VELOCITY_SCALE,
        )
    }

    pub fn calculate_drag_force(
        &self,
        element_x: f32,
        element_y: f32,
        element_w: f32,
        element_h: f32,
    ) -> Vec4 {
        let center_x = element_x + element_w / 2.0;
        let center_y = element_y + element_h / 2.0;
        let fx = (self.pointer_x - center_x) * Self::DRAG_STIFFNESS;
        let fy = (self.pointer_y - center_y) * Self::DRAG_STIFFNESS;
        Vec4::new(fx, fy, 0.0, 0.0)
    }

    pub fn reset(&mut self) {
        self.is_dragging = false;
        self.dragged_element_index = None;
        self.pointer_x = 0.0;
        self.pointer_y = 0.0;
        self.position_history.clear();
    }
}
