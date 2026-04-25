use std::time::Instant;

use aether_math::Vec4;

use crate::elements::DifferentialElement;
use crate::input_manager::InputManager;
use crate::solver;
use crate::state_manager::StateManager;

pub struct RenderData {
    pub rect: Vec4,
    pub color: Vec4,
    pub z: i32,
}

    batch_forces: Vec<Vec4>,
    gpu_node: Option<crate::gpu_compute_node::GPUComputeNode>,
    gpu_device: Option<wgpu::Device>,
    gpu_queue: Option<wgpu::Queue>,
}

impl Default for AetherEngine {
    fn default() -> Self {
        AetherEngine {
            elements: Vec::new(),
            last_instant: None,
            dt: 0.0,
            state_manager: StateManager::new(),
            input_manager: InputManager::new(),
            default_stiffness: 0.1,
            default_viscosity: 0.1,
            batch_states: Vec::new(),
            batch_velocities: Vec::new(),
            batch_targets: Vec::new(),
            batch_forces: Vec::new(),
            gpu_node: None,
            gpu_device: None,
            gpu_queue: None,
        }
    }
}

impl AetherEngine {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn enable_gpu(&mut self) -> bool {
        let instance = wgpu::Instance::default();
        let adapter = pollster::block_on(instance.request_adapter(&wgpu::RequestAdapterOptions {
            power_preference: wgpu::PowerPreference::HighPerformance,
            force_fallback_adapter: false,
            compatible_surface: None,
        }));

        if let Some(adapter) = adapter {
            let (device, queue) = pollster::block_on(adapter.request_device(
                &wgpu::DeviceDescriptor {
                    label: Some("Aether GPUDevice"),
                    required_features: wgpu::Features::empty(),
                    required_limits: wgpu::Limits::default(),
                    memory_hints: wgpu::MemoryHints::Performance,
                },
                None,
            )).unwrap();

            let node = crate::gpu_compute_node::GPUComputeNode::new(&device);
            self.gpu_device = Some(device);
            self.gpu_queue = Some(queue);
            self.gpu_node = Some(node);
            true
        } else {
            false
        }
    }

    pub fn register_element(&mut self, element: Box<dyn DifferentialElement>) {
        self.elements.push(element);
    }

    pub fn element_count(&self) -> usize {
        self.elements.len()
    }

    pub fn handle_pointer_down(&mut self, x: f32, y: f32) -> Option<usize> {
        for idx in (0..self.elements.len()).rev() {
            let elem = &self.elements[idx];
            let s = elem.tensor().state;
            if x >= s.x && x <= s.x + s.w && y >= s.y && y <= s.y + s.h {
                let now = std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap()
                    .as_secs_f64();
                self.input_manager.pointer_down(idx, x, y, now);
                return Some(idx);
            }
        }
        None
    }

    pub fn handle_pointer_move(&mut self, x: f32, y: f32) {
        if self.input_manager.is_dragging() {
            let now = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs_f64();
            self.input_manager.pointer_move(x, y, now);
        }
    }

    pub fn handle_pointer_up(&mut self) {
        if let Some(idx) = self.input_manager.dragged_element_index() {
            if idx < self.elements.len() {
                let (vx, vy) = self.input_manager.get_throw_velocity();
                if let Some(elem) = self.elements.get_mut(idx) {
                    let tensor = elem.tensor_mut();
                    tensor.velocity.x = vx;
                    tensor.velocity.y = vy;
                }
            }
        }
        self.input_manager.pointer_up();
    }

    pub fn tick(&mut self, win_w: f32, win_h: f32) -> Vec<RenderData> {
        let now = Instant::now();
        self.dt = match self.last_instant {
            Some(prev) => now.duration_since(prev).as_secs_f64(),
            None => 1.0 / 60.0,
        };
        self.last_instant = Some(now);

        let dt = if self.dt < 0.0001 {
            1.0 / 60.0
        } else {
            self.dt.clamp(0.001, 1.0)
        } as f32;
        let n = self.elements.len();

        if n == 0 {
            return Vec::new();
        }

        let viscosity_multiplier = self.state_manager.check_teleportation_shock(win_w, win_h);
        let active_viscosity = (self.default_viscosity * viscosity_multiplier).min(1.0);

        let use_batch = n >= 10;

        if use_batch {
            self.ensure_batch_buffers(n);

            for (idx, element) in self.elements.iter().enumerate() {
                let target = element.calculate_asymptotes(win_w, win_h);
                self.batch_targets[idx] = target;
                self.batch_states[idx] = element.tensor().state;
                self.batch_velocities[idx] = element.tensor().velocity;
            }

            if let (Some(node), Some(device), Some(queue)) = (&mut self.gpu_node, &self.gpu_device, &self.gpu_queue) {
                let config = crate::gpu_compute_node::GPUConfig {
                    lerp_factor: stiffness,
                    container_w: win_w,
                    container_h: win_h,
                    dt,
                    viscosity: active_viscosity,
                    boundary_k: 0.5,
                    snap_dist: 0.5,
                    snap_vel: 5.0,
                };
                
                node.compute(
                    device,
                    queue,
                    &mut self.batch_states[..n],
                    &mut self.batch_velocities[..n],
                    &self.batch_targets[..n],
                    config,
                );
            } else {
                solver::batch_restoring_forces(
                    &self.batch_states[..n],
                    &self.batch_targets[..n],
                    stiffness,
                    &mut self.batch_forces[..n],
                );
    
                for i in 0..n {
                    let bf = solver::calculate_boundary_forces(self.batch_states[i], win_w, win_h, 0.5);
                    self.batch_forces[i] = self.batch_forces[i] + bf;
                }
    
                if self.input_manager.is_dragging() {
                    if let Some(idx) = self.input_manager.dragged_element_index() {
                        if idx < n {
                            let elem = &self.elements[idx];
                            let s = elem.tensor().state;
                            let drag_force =
                                self.input_manager.calculate_drag_force(s.x, s.y, s.w, s.h);
                            self.batch_forces[idx] = drag_force;
                        }
                    }
                }
    
                solver::batch_integrate(
                    &mut self.batch_states[..n],
                    &mut self.batch_velocities[..n],
                    &self.batch_forces[..n],
                    dt,
                    active_viscosity,
                    5000.0,
                );
            }

            for (i, element) in self.elements.iter_mut().enumerate() {
                let tensor = element.tensor_mut();
                tensor.state = self.batch_states[i];
                tensor.velocity = self.batch_velocities[i];
                tensor.acceleration = Vec4::ZERO;
            }
        } else {
            let drag_idx = self.input_manager.dragged_element_index();
            let is_dragging = self.input_manager.is_dragging();
            for idx in 0..n {
                let state = self.elements[idx].tensor().state;
                let target = self.elements[idx].calculate_asymptotes(win_w, win_h);
                let stiffness = self.default_stiffness;

                let force = if is_dragging && drag_idx == Some(idx) {
                    self.input_manager
                        .calculate_drag_force(state.x, state.y, state.w, state.h)
                } else {
                    solver::calculate_restoring_force(state, target, stiffness)
                };

                let boundary = solver::calculate_boundary_forces(state, win_w, win_h, 0.5);
                let total_force = force + boundary;

                let tensor = self.elements[idx].tensor_mut();
                tensor.apply_force(total_force);
                tensor.euler_integrate(dt, active_viscosity, Some(&target));
            }
        }

        let mut result = Vec::with_capacity(n);
        for element in &self.elements {
            result.push(RenderData {
                rect: element.tensor().state,
                color: element.color(),
                z: element.z_index(),
            });
        }
        result
    }

    fn ensure_batch_buffers(&mut self, n: usize) {
        if self.batch_states.len() < n {
            self.batch_states = vec![Vec4::ZERO; n];
            self.batch_velocities = vec![Vec4::ZERO; n];
            self.batch_targets = vec![Vec4::ZERO; n];
            self.batch_forces = vec![Vec4::ZERO; n];
        }
    }

    pub fn get_ui_metadata(&self) -> String {
        let mut parts = Vec::new();
        for element in &self.elements {
            if let Some(meta) = element.metadata() {
                parts.push(format!(
                    "\"{}\": {}",
                    element.z_index(),
                    serde_json::to_string(&meta).unwrap_or_default()
                ));
            }
        }
        format!("{{{}}}", parts.join(","))
    }
}
