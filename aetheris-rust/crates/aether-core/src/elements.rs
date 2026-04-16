use aether_math::{StateTensor, Vec4};

pub trait DifferentialElement {
    fn tensor(&self) -> &StateTensor;
    fn tensor_mut(&mut self) -> &mut StateTensor;
    fn color(&self) -> Vec4;
    fn z_index(&self) -> i32;
    fn calculate_asymptotes(&self, container_w: f32, container_h: f32) -> Vec4;
    fn metadata(&self) -> Option<String>;
}

pub struct StaticBox {
    pub tensor: StateTensor,
    color: Vec4,
    z_index: i32,
    target_rect: Vec4,
}

impl StaticBox {
    pub fn new(x: f32, y: f32, w: f32, h: f32, color: Vec4, z: i32) -> Self {
        StaticBox {
            tensor: StateTensor::new(x, y, w, h),
            color,
            z_index: z,
            target_rect: Vec4::new(x, y, w, h),
        }
    }
}

impl DifferentialElement for StaticBox {
    fn tensor(&self) -> &StateTensor {
        &self.tensor
    }

    fn tensor_mut(&mut self) -> &mut StateTensor {
        &mut self.tensor
    }

    fn color(&self) -> Vec4 {
        self.color
    }

    fn z_index(&self) -> i32 {
        self.z_index
    }

    fn calculate_asymptotes(&self, _container_w: f32, _container_h: f32) -> Vec4 {
        self.target_rect
    }

    fn metadata(&self) -> Option<String> {
        Some(format!("StaticBox z={}", self.z_index))
    }
}

pub struct SmartPanel {
    pub tensor: StateTensor,
    color: Vec4,
    z_index: i32,
    padding: f32,
}

impl SmartPanel {
    pub fn new(padding: f32, color: Vec4, z: i32) -> Self {
        SmartPanel {
            tensor: StateTensor::new(0.0, 0.0, 100.0, 100.0),
            color,
            z_index: z,
            padding,
        }
    }
}

impl DifferentialElement for SmartPanel {
    fn tensor(&self) -> &StateTensor {
        &self.tensor
    }

    fn tensor_mut(&mut self) -> &mut StateTensor {
        &mut self.tensor
    }

    fn color(&self) -> Vec4 {
        self.color
    }

    fn z_index(&self) -> i32 {
        self.z_index
    }

    fn calculate_asymptotes(&self, container_w: f32, container_h: f32) -> Vec4 {
        let x = container_w * self.padding;
        let y = container_h * self.padding;
        let w = container_w * (1.0 - 2.0 * self.padding);
        let h = container_h * (1.0 - 2.0 * self.padding);
        Vec4::new(x, y, w, h)
    }

    fn metadata(&self) -> Option<String> {
        Some(format!(
            "SmartPanel z={} padding={}",
            self.z_index, self.padding
        ))
    }
}

pub struct SmartButton {
    pub tensor: StateTensor,
    color: Vec4,
    z_index: i32,
    parent_index: usize,
    offset_x: f32,
    offset_y: f32,
    offset_w: f32,
    offset_h: f32,
}

impl SmartButton {
    pub fn new(
        parent_index: usize,
        offset_x: f32,
        offset_y: f32,
        offset_w: f32,
        offset_h: f32,
        color: Vec4,
        z: i32,
    ) -> Self {
        SmartButton {
            tensor: StateTensor::new(0.0, 0.0, offset_w, offset_h),
            color,
            z_index: z,
            parent_index,
            offset_x,
            offset_y,
            offset_w,
            offset_h,
        }
    }

    pub fn parent_index(&self) -> usize {
        self.parent_index
    }

    pub fn calculate_asymptotes_with_parent(&self, parent_state: Vec4) -> Vec4 {
        let x = parent_state.x + self.offset_x;
        let y = parent_state.y + self.offset_y;
        Vec4::new(x, y, self.offset_w, self.offset_h)
    }
}

impl DifferentialElement for SmartButton {
    fn tensor(&self) -> &StateTensor {
        &self.tensor
    }

    fn tensor_mut(&mut self) -> &mut StateTensor {
        &mut self.tensor
    }

    fn color(&self) -> Vec4 {
        self.color
    }

    fn z_index(&self) -> i32 {
        self.z_index
    }

    fn calculate_asymptotes(&self, _container_w: f32, _container_h: f32) -> Vec4 {
        Vec4::new(self.offset_x, self.offset_y, self.offset_w, self.offset_h)
    }

    fn metadata(&self) -> Option<String> {
        Some(format!(
            "SmartButton z={} parent={}",
            self.z_index, self.parent_index
        ))
    }
}

pub struct CanvasTextNode {
    pub tensor: StateTensor,
    color: Vec4,
    z_index: i32,
    text: String,
    font_size: u32,
    font_family: String,
}

impl CanvasTextNode {
    pub fn new(
        x: f32,
        y: f32,
        w: f32,
        h: f32,
        color: Vec4,
        z: i32,
        text: &str,
        font_size: u32,
        font_family: &str,
    ) -> Self {
        CanvasTextNode {
            tensor: StateTensor::new(x, y, w, h),
            color,
            z_index: z,
            text: text.to_string(),
            font_size,
            font_family: font_family.to_string(),
        }
    }
}

impl DifferentialElement for CanvasTextNode {
    fn tensor(&self) -> &StateTensor {
        &self.tensor
    }

    fn tensor_mut(&mut self) -> &mut StateTensor {
        &mut self.tensor
    }

    fn color(&self) -> Vec4 {
        self.color
    }

    fn z_index(&self) -> i32 {
        self.z_index
    }

    fn calculate_asymptotes(&self, _container_w: f32, _container_h: f32) -> Vec4 {
        self.tensor.state
    }

    fn metadata(&self) -> Option<String> {
        Some(format!(
            "CanvasTextNode z={} text={}",
            self.z_index, self.text
        ))
    }
}

pub struct FlexibleTextNode {
    pub tensor: StateTensor,
    color: Vec4,
    z_index: i32,
    text: String,
}

impl FlexibleTextNode {
    pub fn new(x: f32, y: f32, w: f32, h: f32, color: Vec4, z: i32, text: &str) -> Self {
        FlexibleTextNode {
            tensor: StateTensor::new(x, y, w, h),
            color,
            z_index: z,
            text: text.to_string(),
        }
    }
}

impl DifferentialElement for FlexibleTextNode {
    fn tensor(&self) -> &StateTensor {
        &self.tensor
    }

    fn tensor_mut(&mut self) -> &mut StateTensor {
        &mut self.tensor
    }

    fn color(&self) -> Vec4 {
        self.color
    }

    fn z_index(&self) -> i32 {
        self.z_index
    }

    fn calculate_asymptotes(&self, _container_w: f32, _container_h: f32) -> Vec4 {
        self.tensor.state
    }

    fn metadata(&self) -> Option<String> {
        Some(format!(
            "FlexibleTextNode z={} text={}",
            self.z_index, self.text
        ))
    }
}
