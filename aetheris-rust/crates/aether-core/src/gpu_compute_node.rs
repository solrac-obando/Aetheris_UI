use wgpu::util::DeviceExt;
use aether_math::Vec4;
use bytemuck::{Pod, Zeroable};

#[repr(C)]
#[derive(Clone, Copy, Pod, Zeroable, Debug)]
pub struct GPUConfig {
    pub lerp_factor: f32,
    pub container_w: f32,
    pub container_h: f32,
    pub dt: f32,
    pub viscosity: f32,
    pub boundary_k: f32,
    pub snap_dist: f32,
    pub snap_vel: f32,
}

pub struct GPUComputeNode {
    pub pipeline: wgpu::ComputePipeline,
    pub bind_group_layout: wgpu::BindGroupLayout,
    pub config_buffer: wgpu::Buffer,
    pub state_buffer: Option<wgpu::Buffer>,
    pub velocity_buffer: Option<wgpu::Buffer>,
    pub target_buffer: Option<wgpu::Buffer>,
    pub staging_buffer: Option<wgpu::Buffer>,
    pub staging_buffer_vel: Option<wgpu::Buffer>,
    pub bind_group: Option<wgpu::BindGroup>,
    pub current_capacity: usize,
}

impl GPUComputeNode {
    pub fn new(device: &wgpu::Device) -> Self {
        let shader = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: Some("Aether Physics Shader"),
            source: wgpu::ShaderSource::Wgsl(std::borrow::Cow::Borrowed(include_str!("../../../../core/kernels/physics_kernel.wgsl"))),
        });

        let bind_group_layout = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
            label: Some("Physics Bind Group Layout"),
            entries: &[
                wgpu::BindGroupLayoutEntry {
                    binding: 0,
                    visibility: wgpu::ShaderStages::COMPUTE,
                    ty: wgpu::BindingType::Buffer {
                        ty: wgpu::BufferBindingType::Storage { read_only: false },
                        has_dynamic_offset: false,
                        min_binding_size: None,
                    },
                    count: None,
                },
                wgpu::BindGroupLayoutEntry {
                    binding: 1,
                    visibility: wgpu::ShaderStages::COMPUTE,
                    ty: wgpu::BindingType::Buffer {
                        ty: wgpu::BufferBindingType::Storage { read_only: false },
                        has_dynamic_offset: false,
                        min_binding_size: None,
                    },
                    count: None,
                },
                wgpu::BindGroupLayoutEntry {
                    binding: 2,
                    visibility: wgpu::ShaderStages::COMPUTE,
                    ty: wgpu::BindingType::Buffer {
                        ty: wgpu::BufferBindingType::Storage { read_only: true },
                        has_dynamic_offset: false,
                        min_binding_size: None,
                    },
                    count: None,
                },
                wgpu::BindGroupLayoutEntry {
                    binding: 3,
                    visibility: wgpu::ShaderStages::COMPUTE,
                    ty: wgpu::BindingType::Buffer {
                        ty: wgpu::BufferBindingType::Uniform,
                        has_dynamic_offset: false,
                        min_binding_size: None,
                    },
                    count: None,
                },
            ],
        });

        let pipeline_layout = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
            label: Some("Physics Pipeline Layout"),
            bind_group_layouts: &[&bind_group_layout],
            push_constant_ranges: &[],
        });

        let pipeline = device.create_compute_pipeline(&wgpu::ComputePipelineDescriptor {
            label: Some("Physics Compute Pipeline"),
            layout: Some(&pipeline_layout),
            module: &shader,
            entry_point: Some("main"),
            compilation_options: Default::default(),
            cache: None,
        });

        let config_buffer = device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("Config Buffer"),
            size: std::mem::size_of::<GPUConfig>() as u64,
            usage: wgpu::BufferUsages::UNIFORM | wgpu::BufferUsages::COPY_DST,
            mapped_at_creation: false,
        });

        Self {
            pipeline,
            bind_group_layout,
            config_buffer,
            state_buffer: None,
            velocity_buffer: None,
            target_buffer: None,
            staging_buffer: None,
            staging_buffer_vel: None,
            bind_group: None,
            current_capacity: 0,
        }
    }

    fn ensure_capacity(&mut self, device: &wgpu::Device, n: usize) {
        if n > self.current_capacity {
            let new_capacity = n.next_power_of_two().max(1024);
            let size = (new_capacity * std::mem::size_of::<Vec4>()) as u64;

            self.state_buffer = Some(device.create_buffer(&wgpu::BufferDescriptor {
                label: Some("States Buffer"),
                size,
                usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC | wgpu::BufferUsages::COPY_DST,
                mapped_at_creation: false,
            }));

            self.velocity_buffer = Some(device.create_buffer(&wgpu::BufferDescriptor {
                label: Some("Velocities Buffer"),
                size,
                usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC | wgpu::BufferUsages::COPY_DST,
                mapped_at_creation: false,
            }));

            self.target_buffer = Some(device.create_buffer(&wgpu::BufferDescriptor {
                label: Some("Targets Buffer"),
                size,
                usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_DST,
                mapped_at_creation: false,
            }));

            self.staging_buffer = Some(device.create_buffer(&wgpu::BufferDescriptor {
                label: Some("Staging Buffer States"),
                size,
                usage: wgpu::BufferUsages::MAP_READ | wgpu::BufferUsages::COPY_DST,
                mapped_at_creation: false,
            }));

            self.staging_buffer_vel = Some(device.create_buffer(&wgpu::BufferDescriptor {
                label: Some("Staging Buffer Vel"),
                size,
                usage: wgpu::BufferUsages::MAP_READ | wgpu::BufferUsages::COPY_DST,
                mapped_at_creation: false,
            }));

            self.bind_group = Some(device.create_bind_group(&wgpu::BindGroupDescriptor {
                label: Some("Physics Bind Group"),
                layout: &self.bind_group_layout,
                entries: &[
                    wgpu::BindGroupEntry { binding: 0, resource: self.state_buffer.as_ref().unwrap().as_entire_binding() },
                    wgpu::BindGroupEntry { binding: 1, resource: self.velocity_buffer.as_ref().unwrap().as_entire_binding() },
                    wgpu::BindGroupEntry { binding: 2, resource: self.target_buffer.as_ref().unwrap().as_entire_binding() },
                    wgpu::BindGroupEntry { binding: 3, resource: self.config_buffer.as_entire_binding() },
                ],
            }));

            self.current_capacity = new_capacity;
        }
    }

    pub fn compute(
        &mut self,
        device: &wgpu::Device,
        queue: &wgpu::Queue,
        states: &mut [Vec4],
        velocities: &mut [Vec4],
        targets: &[Vec4],
        config: GPUConfig,
    ) {
        let n = states.len();
        if n == 0 { return; }

        self.ensure_capacity(device, n);

        // Upload data
        queue.write_buffer(self.state_buffer.as_ref().unwrap(), 0, bytemuck::cast_slice(states));
        queue.write_buffer(self.velocity_buffer.as_ref().unwrap(), 0, bytemuck::cast_slice(velocities));
        queue.write_buffer(self.target_buffer.as_ref().unwrap(), 0, bytemuck::cast_slice(targets));
        queue.write_buffer(&self.config_buffer, 0, bytemuck::bytes_of(&config));

        // Dispatch
        let mut encoder = device.create_command_encoder(&wgpu::CommandEncoderDescriptor { label: Some("Physics Encoder") });
        {
            let mut cpass = encoder.begin_compute_pass(&wgpu::ComputePassDescriptor { label: Some("Physics Pass"), timestamp_writes: None });
            cpass.set_pipeline(&self.pipeline);
            cpass.set_bind_group(0, self.bind_group.as_ref().unwrap(), &[]);
            let workgroups = (n as u32 + 63) / 64;
            cpass.dispatch_workgroups(workgroups, 1, 1);
        }

        // Copy back to staging
        let data_size = (n * std::mem::size_of::<Vec4>()) as u64;
        encoder.copy_buffer_to_buffer(self.state_buffer.as_ref().unwrap(), 0, self.staging_buffer.as_ref().unwrap(), 0, data_size);
        encoder.copy_buffer_to_buffer(self.velocity_buffer.as_ref().unwrap(), 0, self.staging_buffer_vel.as_ref().unwrap(), 0, data_size);

        queue.submit(Some(encoder.finish()));

        // Map and read back
        let buffer_slice = self.staging_buffer.as_ref().unwrap().slice(..data_size);
        let buffer_slice_vel = self.staging_buffer_vel.as_ref().unwrap().slice(..data_size);

        let (tx, rx) = std::sync::mpsc::channel();
        let (txv, rxv) = std::sync::mpsc::channel();
        
        buffer_slice.map_async(wgpu::MapMode::Read, move |v| tx.send(v).unwrap());
        buffer_slice_vel.map_async(wgpu::MapMode::Read, move |v| txv.send(v).unwrap());
        
        device.poll(wgpu::Maintain::Wait);
        
        if let Ok(Ok(())) = rx.recv() {
            let data = buffer_slice.get_mapped_range();
            states.copy_from_slice(bytemuck::cast_slice(&data));
            drop(data);
            self.staging_buffer.as_ref().unwrap().unmap();
        }

        if let Ok(Ok(())) = rxv.recv() {
            let data = buffer_slice_vel.get_mapped_range();
            velocities.copy_from_slice(bytemuck::cast_slice(&data));
            drop(data);
            self.staging_buffer_vel.as_ref().unwrap().unmap();
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use aether_math::Vec4;

    fn get_test_device() -> Option<(wgpu::Device, wgpu::Queue)> {
        let instance = wgpu::Instance::default();
        let adapter = pollster::block_on(instance.request_adapter(&wgpu::RequestAdapterOptions {
            power_preference: wgpu::PowerPreference::LowPower,
            force_fallback_adapter: true, // Force fallback for headless tests
            compatible_surface: None,
        }))?;

        Some(pollster::block_on(adapter.request_device(
            &wgpu::DeviceDescriptor {
                label: None,
                required_features: wgpu::Features::empty(),
                required_limits: wgpu::Limits::default(),
                memory_hints: wgpu::MemoryHints::Performance,
            },
            None,
        )).unwrap())
    }

    #[test]
    fn test_gpu_node_init() {
        if let Some((device, _)) = get_test_device() {
            let _node = GPUComputeNode::new(&device);
        }
    }

    #[test]
    fn test_gpu_node_compute_basic() {
        if let Some((device, queue)) = get_test_device() {
            let mut node = GPUComputeNode::new(&device);
            let mut states = [Vec4::new(0.0, 0.0, 100.0, 100.0)];
            let mut velocities = [Vec4::ZERO];
            let targets = [Vec4::new(100.0, 100.0, 100.0, 100.0)];
            
            let config = GPUConfig {
                lerp_factor: 0.1,
                container_w: 800.0,
                container_h: 600.0,
                dt: 1.0, // Large DT for visibility
                viscosity: 0.0,
                boundary_k: 0.5,
                snap_dist: 0.5,
                snap_vel: 5.0,
            };

            node.compute(&device, &queue, &mut states, &mut velocities, &targets, config);

            // Hooke's Law: F = 0.1 * (100 - 0) = 10
            // Integration: v = 0 + 10 * 1 = 10, s = 0 + 10 * 1 = 10
            assert!(states[0].x > 0.0);
            assert!(velocities[0].x > 0.0);
        }
    }
}
