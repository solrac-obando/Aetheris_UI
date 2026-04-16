use aether_core::elements::{CanvasTextNode, FlexibleTextNode, SmartButton, SmartPanel, StaticBox};
use aether_core::AetherEngine;
use aether_math::Vec4;
use pyo3::prelude::*;
use pyo3::types::PyDict;

// ── PyVec4 ────────────────────────────────────────────────────────────────

#[pyclass(name = "Vec4")]
#[derive(Clone, Copy)]
pub struct PyVec4 {
    #[pyo3(get, set)]
    pub x: f32,
    #[pyo3(get, set)]
    pub y: f32,
    #[pyo3(get, set)]
    pub w: f32,
    #[pyo3(get, set)]
    pub h: f32,
}

#[pymethods]
impl PyVec4 {
    #[new]
    pub fn new(x: f32, y: f32, w: f32, h: f32) -> Self {
        PyVec4 { x, y, w, h }
    }

    pub fn magnitude(&self) -> f32 {
        self.into_inner().magnitude()
    }

    pub fn distance_to(&self, other: &PyVec4) -> f32 {
        self.into_inner().distance_to(&other.into_inner())
    }

    pub fn __repr__(&self) -> String {
        format!(
            "Vec4({:.2}, {:.2}, {:.2}, {:.2})",
            self.x, self.y, self.w, self.h
        )
    }
}

impl PyVec4 {
    pub fn from_inner(v: Vec4) -> Self {
        PyVec4 {
            x: v.x,
            y: v.y,
            w: v.w,
            h: v.h,
        }
    }

    pub fn into_inner(&self) -> Vec4 {
        Vec4::new(self.x, self.y, self.w, self.h)
    }
}

// ── Element Wrappers ──────────────────────────────────────────────────────

#[allow(dead_code)]
#[pyclass(name = "StaticBox")]
pub struct PyStaticBox {
    x: f32,
    y: f32,
    w: f32,
    h: f32,
    color: Vec4,
    z: i32,
}

#[pymethods]
impl PyStaticBox {
    #[new]
    pub fn new(x: f32, y: f32, w: f32, h: f32, color: &PyVec4, z: i32) -> Self {
        PyStaticBox {
            x,
            y,
            w,
            h,
            color: color.into_inner(),
            z,
        }
    }
}

#[pyclass(name = "SmartPanel")]
pub struct PySmartPanel {
    padding: f32,
    color: Vec4,
    z: i32,
}

#[pymethods]
impl PySmartPanel {
    #[new]
    pub fn new(padding: f32, color: &PyVec4, z: i32) -> Self {
        PySmartPanel {
            padding,
            color: color.into_inner(),
            z,
        }
    }
}

#[pyclass(name = "SmartButton")]
pub struct PySmartButton {
    parent_index: usize,
    offset_x: f32,
    offset_y: f32,
    offset_w: f32,
    offset_h: f32,
    color: Vec4,
    z: i32,
}

#[pymethods]
impl PySmartButton {
    #[new]
    pub fn new(
        parent_index: usize,
        offset_x: f32,
        offset_y: f32,
        offset_w: f32,
        offset_h: f32,
        color: &PyVec4,
        z: i32,
    ) -> Self {
        PySmartButton {
            parent_index,
            offset_x,
            offset_y,
            offset_w,
            offset_h,
            color: color.into_inner(),
            z,
        }
    }
}

#[pyclass(name = "CanvasTextNode")]
pub struct PyCanvasTextNode {
    x: f32,
    y: f32,
    w: f32,
    h: f32,
    color: Vec4,
    z: i32,
    text: String,
    font_size: u32,
    font_family: String,
}

#[pymethods]
impl PyCanvasTextNode {
    #[new]
    #[pyo3(signature = (x, y, w, h, color, z, text, font_size=16, font_family="Arial"))]
    pub fn new(
        x: f32,
        y: f32,
        w: f32,
        h: f32,
        color: &PyVec4,
        z: i32,
        text: &str,
        font_size: u32,
        font_family: &str,
    ) -> Self {
        PyCanvasTextNode {
            x,
            y,
            w,
            h,
            color: color.into_inner(),
            z,
            text: text.to_string(),
            font_size,
            font_family: font_family.to_string(),
        }
    }
}

#[pyclass(name = "FlexibleTextNode")]
pub struct PyFlexibleTextNode {
    x: f32,
    y: f32,
    w: f32,
    h: f32,
    color: Vec4,
    z: i32,
    text: String,
}

#[pymethods]
impl PyFlexibleTextNode {
    #[new]
    pub fn new(x: f32, y: f32, w: f32, h: f32, color: &PyVec4, z: i32, text: &str) -> Self {
        PyFlexibleTextNode {
            x,
            y,
            w,
            h,
            color: color.into_inner(),
            z,
            text: text.to_string(),
        }
    }
}

// ── PyAetherEngine ────────────────────────────────────────────────────────

#[pyclass(name = "AetherEngine", unsendable)]
pub struct PyAetherEngine {
    inner: AetherEngine,
}

#[pymethods]
impl PyAetherEngine {
    #[new]
    pub fn new() -> Self {
        PyAetherEngine {
            inner: AetherEngine::new(),
        }
    }

    pub fn register_static_box(&mut self, x: f32, y: f32, w: f32, h: f32, color: &PyVec4, z: i32) {
        self.inner
            .register_element(Box::new(StaticBox::new(x, y, w, h, color.into_inner(), z)));
    }

    pub fn register_smart_panel(&mut self, padding: f32, color: &PyVec4, z: i32) {
        self.inner
            .register_element(Box::new(SmartPanel::new(padding, color.into_inner(), z)));
    }

    pub fn register_smart_button(
        &mut self,
        parent_index: usize,
        offset_x: f32,
        offset_y: f32,
        offset_w: f32,
        offset_h: f32,
        color: &PyVec4,
        z: i32,
    ) {
        self.inner.register_element(Box::new(SmartButton::new(
            parent_index,
            offset_x,
            offset_y,
            offset_w,
            offset_h,
            color.into_inner(),
            z,
        )));
    }

    pub fn register_canvas_text_node(
        &mut self,
        x: f32,
        y: f32,
        w: f32,
        h: f32,
        color: &PyVec4,
        z: i32,
        text: &str,
        font_size: u32,
        font_family: &str,
    ) {
        self.inner.register_element(Box::new(CanvasTextNode::new(
            x,
            y,
            w,
            h,
            color.into_inner(),
            z,
            text,
            font_size,
            font_family,
        )));
    }

    pub fn register_flexible_text_node(
        &mut self,
        x: f32,
        y: f32,
        w: f32,
        h: f32,
        color: &PyVec4,
        z: i32,
        text: &str,
    ) {
        self.inner.register_element(Box::new(FlexibleTextNode::new(
            x,
            y,
            w,
            h,
            color.into_inner(),
            z,
            text,
        )));
    }

    pub fn handle_pointer_down(&mut self, x: f32, y: f32) -> Option<usize> {
        self.inner.handle_pointer_down(x, y)
    }

    pub fn handle_pointer_move(&mut self, x: f32, y: f32) {
        self.inner.handle_pointer_move(x, y);
    }

    pub fn handle_pointer_up(&mut self) {
        self.inner.handle_pointer_up();
    }

    pub fn element_count(&self) -> usize {
        self.inner.element_count()
    }

    pub fn tick_benchmark(&mut self, win_w: f32, win_h: f32, iterations: usize) -> f64 {
        use std::time::Instant;
        let start = Instant::now();
        for _ in 0..iterations {
            self.inner.tick(win_w, win_h);
        }
        start.elapsed().as_secs_f64() * 1000.0
    }

    pub fn tick(&mut self, win_w: f32, win_h: f32, py: Python<'_>) -> PyResult<Vec<PyObject>> {
        let render_data = self.inner.tick(win_w, win_h);

        let mut result = Vec::with_capacity(render_data.len());
        for data in &render_data {
            let dict = PyDict::new(py);

            let rect = PyDict::new(py);
            rect.set_item("x", data.rect.x)?;
            rect.set_item("y", data.rect.y)?;
            rect.set_item("w", data.rect.w)?;
            rect.set_item("h", data.rect.h)?;
            dict.set_item("rect", rect)?;

            let color = PyDict::new(py);
            color.set_item("r", data.color.x)?;
            color.set_item("g", data.color.y)?;
            color.set_item("b", data.color.w)?;
            color.set_item("a", data.color.h)?;
            dict.set_item("color", color)?;

            dict.set_item("z", data.z)?;

            result.push(dict.into());
        }

        Ok(result)
    }

    pub fn get_ui_metadata(&self) -> String {
        self.inner.get_ui_metadata()
    }

    pub fn __repr__(&self) -> String {
        format!("AetherEngine(elements={})", self.inner.element_count())
    }
}

// ── Module Definition ─────────────────────────────────────────────────────

#[pymodule]
fn aether_pyo3(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyVec4>()?;
    m.add_class::<PyAetherEngine>()?;
    m.add_class::<PyStaticBox>()?;
    m.add_class::<PySmartPanel>()?;
    m.add_class::<PySmartButton>()?;
    m.add_class::<PyCanvasTextNode>()?;
    m.add_class::<PyFlexibleTextNode>()?;
    Ok(())
}
