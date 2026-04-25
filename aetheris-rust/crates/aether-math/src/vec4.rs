use std::ops::{Add, Div, Mul, Sub};

#[derive(Clone, Copy, Debug, Default, PartialEq, bytemuck::Pod, bytemuck::Zeroable)]
#[repr(C)]
pub struct Vec4 {
    pub x: f32,
    pub y: f32,
    pub w: f32,
    pub h: f32,
}

impl Vec4 {
    pub const ZERO: Vec4 = Vec4 {
        x: 0.0,
        y: 0.0,
        w: 0.0,
        h: 0.0,
    };

    pub fn new(x: f32, y: f32, w: f32, h: f32) -> Self {
        Vec4 { x, y, w, h }
    }

    pub fn magnitude(&self) -> f32 {
        (self.x * self.x + self.y * self.y + self.w * self.w + self.h * self.h).sqrt()
    }

    pub fn magnitude_xy(&self) -> f32 {
        (self.x * self.x + self.y * self.y).sqrt()
    }

    pub fn normalize(&self) -> Self {
        let mag = self.magnitude();
        if mag > 1e-9 {
            return *self / mag;
        }
        *self
    }

    pub fn clamp_magnitude(&self, max: f32) -> Self {
        let mag = self.magnitude();
        if mag > max && mag > 1e-9 {
            return (*self / mag) * max;
        }
        *self
    }

    pub fn is_nan(&self) -> bool {
        self.x.is_nan()
            || self.x.is_infinite()
            || self.y.is_nan()
            || self.y.is_infinite()
            || self.w.is_nan()
            || self.w.is_infinite()
            || self.h.is_nan()
            || self.h.is_infinite()
    }

    pub fn sanitize(&self) -> Self {
        if self.is_nan() {
            return Vec4::ZERO;
        }
        *self
    }

    pub fn distance_to(&self, other: &Vec4) -> f32 {
        (*self - *other).magnitude()
    }

    pub fn lerp(a: &Vec4, b: &Vec4, t: f32) -> Vec4 {
        *a * (1.0 - t) + *b * t
    }
}

impl Add for Vec4 {
    type Output = Vec4;

    fn add(self, rhs: Vec4) -> Vec4 {
        Vec4 {
            x: self.x + rhs.x,
            y: self.y + rhs.y,
            w: self.w + rhs.w,
            h: self.h + rhs.h,
        }
    }
}

impl Sub for Vec4 {
    type Output = Vec4;

    fn sub(self, rhs: Vec4) -> Vec4 {
        Vec4 {
            x: self.x - rhs.x,
            y: self.y - rhs.y,
            w: self.w - rhs.w,
            h: self.h - rhs.h,
        }
    }
}

impl Mul<f32> for Vec4 {
    type Output = Vec4;

    fn mul(self, rhs: f32) -> Vec4 {
        Vec4 {
            x: self.x * rhs,
            y: self.y * rhs,
            w: self.w * rhs,
            h: self.h * rhs,
        }
    }
}

impl Mul<Vec4> for Vec4 {
    type Output = Vec4;

    fn mul(self, rhs: Vec4) -> Vec4 {
        Vec4 {
            x: self.x * rhs.x,
            y: self.y * rhs.y,
            w: self.w * rhs.w,
            h: self.h * rhs.h,
        }
    }
}

impl Div<f32> for Vec4 {
    type Output = Vec4;

    fn div(self, rhs: f32) -> Vec4 {
        Vec4 {
            x: self.x / rhs,
            y: self.y / rhs,
            w: self.w / rhs,
            h: self.h / rhs,
        }
    }
}
