pub mod aether_guard;
pub mod state_tensor;
pub mod vec4;

pub use aether_guard::*;
pub use state_tensor::StateTensor;
pub use vec4::Vec4;

#[cfg(test)]
mod vec4_tests {
    use super::Vec4;

    const TOL: f32 = 1e-5;

    #[test]
    fn test_vec4_zero() {
        let v = Vec4::ZERO;
        assert_eq!(v.x, 0.0);
        assert_eq!(v.y, 0.0);
        assert_eq!(v.w, 0.0);
        assert_eq!(v.h, 0.0);
    }
    #[test]
    fn test_vec4_new() {
        let v = Vec4::new(1.0, 2.0, 3.0, 4.0);
        assert_eq!(v.x, 1.0);
        assert_eq!(v.y, 2.0);
        assert_eq!(v.w, 3.0);
        assert_eq!(v.h, 4.0);
    }
    #[test]
    fn test_vec4_default() {
        let v = Vec4::default();
        assert_eq!(v, Vec4::ZERO);
    }
    #[test]
    fn test_vec4_copy() {
        let a = Vec4::new(1.0, 2.0, 3.0, 4.0);
        let b = a;
        assert_eq!(a, b);
    }
    #[test]
    fn test_vec4_debug() {
        let v = Vec4::new(1.0, 0.0, 0.0, 0.0);
        let s = format!("{:?}", v);
        assert!(s.contains("1.0"));
    }
    #[test]
    fn test_magnitude_zero() {
        assert_eq!(Vec4::ZERO.magnitude(), 0.0);
    }
    #[test]
    fn test_magnitude_unit_x() {
        assert!((Vec4::new(1.0, 0.0, 0.0, 0.0).magnitude() - 1.0).abs() < TOL);
    }
    #[test]
    fn test_magnitude_unit_y() {
        assert!((Vec4::new(0.0, 1.0, 0.0, 0.0).magnitude() - 1.0).abs() < TOL);
    }
    #[test]
    fn test_magnitude_345() {
        assert!((Vec4::new(3.0, 4.0, 0.0, 0.0).magnitude() - 5.0).abs() < TOL);
    }
    #[test]
    fn test_magnitude_1234() {
        let m = Vec4::new(1.0, 2.0, 3.0, 4.0).magnitude();
        assert!((m - 30.0_f32.sqrt()).abs() < TOL);
    }
    #[test]
    fn test_magnitude_negative() {
        assert!((Vec4::new(-3.0, -4.0, 0.0, 0.0).magnitude() - 5.0).abs() < TOL);
    }
    #[test]
    fn test_magnitude_large() {
        let m = Vec4::new(100.0, 200.0, 300.0, 400.0).magnitude();
        assert!((m - 547.72253).abs() < 0.01);
    }
    #[test]
    fn test_magnitude_tiny() {
        let m = Vec4::new(0.001, 0.002, 0.003, 0.004).magnitude();
        assert!(m > 0.0);
    }
    #[test]
    fn test_magnitude_all_equal() {
        let m = Vec4::new(5.0, 5.0, 5.0, 5.0).magnitude();
        assert!((m - 10.0).abs() < TOL);
    }
    #[test]
    fn test_magnitude_xy_zero() {
        assert_eq!(Vec4::ZERO.magnitude_xy(), 0.0);
    }
    #[test]
    fn test_magnitude_xy_34() {
        assert!((Vec4::new(3.0, 4.0, 100.0, 100.0).magnitude_xy() - 5.0).abs() < TOL);
    }
    #[test]
    fn test_magnitude_xy_512() {
        assert!((Vec4::new(5.0, 12.0, 0.0, 0.0).magnitude_xy() - 13.0).abs() < TOL);
    }
    #[test]
    fn test_magnitude_xy_ignores_wh() {
        assert!((Vec4::new(1.0, 0.0, 999.0, 999.0).magnitude_xy() - 1.0).abs() < TOL);
    }
    #[test]
    fn test_normalize_unit_x() {
        let v = Vec4::new(1.0, 0.0, 0.0, 0.0).normalize();
        assert!((v.x - 1.0).abs() < TOL);
    }
    #[test]
    fn test_normalize_34() {
        let v = Vec4::new(3.0, 4.0, 0.0, 0.0).normalize();
        assert!((v.x - 0.6).abs() < TOL);
        assert!((v.y - 0.8).abs() < TOL);
    }
    #[test]
    fn test_normalize_1234() {
        let v = Vec4::new(1.0, 2.0, 3.0, 4.0).normalize();
        let m = v.magnitude();
        assert!((m - 1.0).abs() < TOL);
    }
    #[test]
    fn test_normalize_zero_stays_zero() {
        let v = Vec4::ZERO.normalize();
        assert_eq!(v, Vec4::ZERO);
    }
    #[test]
    fn test_normalize_negative() {
        let v = Vec4::new(-3.0, 0.0, 0.0, 0.0).normalize();
        assert!((v.x - (-1.0)).abs() < TOL);
    }
    #[test]
    fn test_clamp_magnitude_under() {
        let v = Vec4::new(3.0, 0.0, 0.0, 0.0).clamp_magnitude(5.0);
        assert_eq!(v, Vec4::new(3.0, 0.0, 0.0, 0.0));
    }
    #[test]
    fn test_clamp_magnitude_over() {
        let v = Vec4::new(10.0, 0.0, 0.0, 0.0).clamp_magnitude(5.0);
        assert!((v.magnitude() - 5.0).abs() < TOL);
    }
    #[test]
    fn test_clamp_magnitude_34_to_5() {
        let v = Vec4::new(3.0, 4.0, 0.0, 0.0).clamp_magnitude(5.0);
        assert_eq!(v, Vec4::new(3.0, 4.0, 0.0, 0.0));
    }
    #[test]
    fn test_clamp_magnitude_100_200_to_100() {
        let v = Vec4::new(100.0, 200.0, 0.0, 0.0).clamp_magnitude(100.0);
        assert!((v.magnitude() - 100.0).abs() < TOL);
    }
    #[test]
    fn test_clamp_magnitude_preserves_direction() {
        let orig = Vec4::new(3.0, 4.0, 0.0, 0.0);
        let c = orig.clamp_magnitude(2.5);
        let ratio = if orig.x != 0.0 { c.x / orig.x } else { 1.0 };
        assert!((ratio - 0.5).abs() < TOL);
    }
    #[test]
    fn test_clamp_magnitude_zero_vec() {
        let v = Vec4::ZERO.clamp_magnitude(5.0);
        assert_eq!(v, Vec4::ZERO);
    }
    #[test]
    fn test_clamp_magnitude_1111_to_1() {
        let v = Vec4::new(1.0, 1.0, 1.0, 1.0).clamp_magnitude(1.0);
        assert!((v.magnitude() - 1.0).abs() < TOL);
    }
    #[test]
    fn test_clamp_magnitude_max_velocity() {
        let v = Vec4::new(3000.0, 4000.0, 0.0, 0.0).clamp_magnitude(5000.0);
        assert_eq!(v, Vec4::new(3000.0, 4000.0, 0.0, 0.0));
    }
    #[test]
    fn test_clamp_magnitude_over_max_vel() {
        let v = Vec4::new(6000.0, 8000.0, 0.0, 0.0).clamp_magnitude(5000.0);
        assert!((v.magnitude() - 5000.0).abs() < TOL);
    }
    #[test]
    fn test_clamp_magnitude_negative_components() {
        let v = Vec4::new(-3000.0, -4000.0, 0.0, 0.0).clamp_magnitude(5000.0);
        assert_eq!(v, Vec4::new(-3000.0, -4000.0, 0.0, 0.0));
    }
    #[test]
    fn test_is_nan_clean() {
        assert!(!Vec4::new(1.0, 2.0, 3.0, 4.0).is_nan());
    }
    #[test]
    fn test_is_nan_zero() {
        assert!(!Vec4::ZERO.is_nan());
    }
    #[test]
    fn test_is_nan_x() {
        assert!(Vec4::new(f32::NAN, 0.0, 0.0, 0.0).is_nan());
    }
    #[test]
    fn test_is_nan_y() {
        assert!(Vec4::new(0.0, f32::NAN, 0.0, 0.0).is_nan());
    }
    #[test]
    fn test_is_nan_w() {
        assert!(Vec4::new(0.0, 0.0, f32::NAN, 0.0).is_nan());
    }
    #[test]
    fn test_is_nan_h() {
        assert!(Vec4::new(0.0, 0.0, 0.0, f32::NAN).is_nan());
    }
    #[test]
    fn test_is_inf_x() {
        assert!(Vec4::new(f32::INFINITY, 0.0, 0.0, 0.0).is_nan());
    }
    #[test]
    fn test_is_neg_inf_y() {
        assert!(Vec4::new(0.0, f32::NEG_INFINITY, 0.0, 0.0).is_nan());
    }
    #[test]
    fn test_is_nan_all() {
        assert!(Vec4::new(f32::NAN, f32::NAN, f32::NAN, f32::NAN).is_nan());
    }
    #[test]
    fn test_is_nan_negative_vals() {
        assert!(!Vec4::new(-1.0, -2.0, -3.0, -4.0).is_nan());
    }
    #[test]
    fn test_sanitize_clean() {
        let v = Vec4::new(1.0, 2.0, 3.0, 4.0).sanitize();
        assert_eq!(v.x, 1.0);
    }
    #[test]
    fn test_sanitize_nan_x() {
        let v = Vec4::new(f32::NAN, 2.0, 3.0, 4.0).sanitize();
        assert_eq!(v, Vec4::ZERO);
    }
    #[test]
    fn test_sanitize_inf_y() {
        let v = Vec4::new(1.0, f32::INFINITY, 0.0, 0.0).sanitize();
        assert_eq!(v, Vec4::ZERO);
    }
    #[test]
    fn test_sanitize_zero() {
        let v = Vec4::ZERO.sanitize();
        assert_eq!(v, Vec4::ZERO);
    }
    #[test]
    fn test_distance_to_same() {
        assert_eq!(
            Vec4::new(1.0, 2.0, 3.0, 4.0).distance_to(&Vec4::new(1.0, 2.0, 3.0, 4.0)),
            0.0
        );
    }
    #[test]
    fn test_distance_to_zero() {
        assert!((Vec4::new(3.0, 4.0, 0.0, 0.0).distance_to(&Vec4::ZERO) - 5.0).abs() < TOL);
    }
    #[test]
    fn test_distance_to_1unit() {
        assert!(
            (Vec4::new(0.0, 0.0, 0.0, 0.0).distance_to(&Vec4::new(1.0, 0.0, 0.0, 0.0)) - 1.0).abs()
                < TOL
        );
    }
    #[test]
    fn test_distance_to_negative() {
        let d = Vec4::new(0.0, 0.0, 0.0, 0.0).distance_to(&Vec4::new(-3.0, -4.0, 0.0, 0.0));
        assert!((d - 5.0).abs() < TOL);
    }
    #[test]
    fn test_lerp_t0() {
        let r = Vec4::lerp(
            &Vec4::new(0.0, 0.0, 0.0, 0.0),
            &Vec4::new(10.0, 20.0, 30.0, 40.0),
            0.0,
        );
        assert!((r.x - 0.0).abs() < TOL);
    }
    #[test]
    fn test_lerp_t1() {
        let r = Vec4::lerp(
            &Vec4::new(0.0, 0.0, 0.0, 0.0),
            &Vec4::new(10.0, 20.0, 30.0, 40.0),
            1.0,
        );
        assert!((r.x - 10.0).abs() < TOL);
        assert!((r.y - 20.0).abs() < TOL);
    }
    #[test]
    fn test_lerp_t05() {
        let r = Vec4::lerp(
            &Vec4::new(0.0, 0.0, 0.0, 0.0),
            &Vec4::new(10.0, 20.0, 30.0, 40.0),
            0.5,
        );
        assert!((r.x - 5.0).abs() < TOL);
        assert!((r.y - 10.0).abs() < TOL);
    }
    #[test]
    fn test_lerp_t025() {
        let r = Vec4::lerp(
            &Vec4::new(0.0, 0.0, 0.0, 0.0),
            &Vec4::new(100.0, 100.0, 100.0, 100.0),
            0.25,
        );
        assert!((r.x - 25.0).abs() < TOL);
    }
    #[test]
    fn test_lerp_same_point() {
        let a = Vec4::new(5.0, 5.0, 5.0, 5.0);
        let r = Vec4::lerp(&a, &a, 0.5);
        assert_eq!(r, a);
    }
    #[test]
    fn test_lerp_negative() {
        let r = Vec4::lerp(
            &Vec4::new(-10.0, 0.0, 0.0, 0.0),
            &Vec4::new(10.0, 0.0, 0.0, 0.0),
            0.5,
        );
        assert!((r.x - 0.0).abs() < TOL);
    }
    #[test]
    fn test_add() {
        let r = Vec4::new(1.0, 2.0, 3.0, 4.0) + Vec4::new(5.0, 6.0, 7.0, 8.0);
        assert_eq!(r, Vec4::new(6.0, 8.0, 10.0, 12.0));
    }
    #[test]
    fn test_add_zero() {
        let r = Vec4::new(1.0, 2.0, 3.0, 4.0) + Vec4::ZERO;
        assert_eq!(r, Vec4::new(1.0, 2.0, 3.0, 4.0));
    }
    #[test]
    fn test_add_negative() {
        let r = Vec4::new(1.0, 2.0, 3.0, 4.0) + Vec4::new(-1.0, -2.0, -3.0, -4.0);
        assert_eq!(r, Vec4::ZERO);
    }
    #[test]
    fn test_add_commutative() {
        let a = Vec4::new(1.0, 2.0, 3.0, 4.0);
        let b = Vec4::new(5.0, 6.0, 7.0, 8.0);
        assert_eq!(a + b, b + a);
    }
    #[test]
    fn test_add_associative() {
        let a = Vec4::new(1.0, 0.0, 0.0, 0.0);
        let b = Vec4::new(2.0, 0.0, 0.0, 0.0);
        let c = Vec4::new(3.0, 0.0, 0.0, 0.0);
        assert_eq!((a + b) + c, a + (b + c));
    }
    #[test]
    fn test_sub() {
        let r = Vec4::new(5.0, 6.0, 7.0, 8.0) - Vec4::new(1.0, 2.0, 3.0, 4.0);
        assert_eq!(r, Vec4::new(4.0, 4.0, 4.0, 4.0));
    }
    #[test]
    fn test_sub_zero() {
        let r = Vec4::new(1.0, 2.0, 3.0, 4.0) - Vec4::ZERO;
        assert_eq!(r, Vec4::new(1.0, 2.0, 3.0, 4.0));
    }
    #[test]
    fn test_sub_self() {
        let a = Vec4::new(1.0, 2.0, 3.0, 4.0);
        assert_eq!(a - a, Vec4::ZERO);
    }
    #[test]
    fn test_sub_negative_result() {
        let r = Vec4::new(1.0, 1.0, 1.0, 1.0) - Vec4::new(2.0, 2.0, 2.0, 2.0);
        assert_eq!(r, Vec4::new(-1.0, -1.0, -1.0, -1.0));
    }
    #[test]
    fn test_mul_scalar_2() {
        let r = Vec4::new(1.0, 2.0, 3.0, 4.0) * 2.0;
        assert_eq!(r, Vec4::new(2.0, 4.0, 6.0, 8.0));
    }
    #[test]
    fn test_mul_scalar_0() {
        let r = Vec4::new(1.0, 2.0, 3.0, 4.0) * 0.0;
        assert_eq!(r, Vec4::ZERO);
    }
    #[test]
    fn test_mul_scalar_neg() {
        let r = Vec4::new(1.0, 2.0, 3.0, 4.0) * (-1.0);
        assert_eq!(r, Vec4::new(-1.0, -2.0, -3.0, -4.0));
    }
    #[test]
    fn test_mul_scalar_05() {
        let r = Vec4::new(2.0, 4.0, 6.0, 8.0) * 0.5;
        assert_eq!(r, Vec4::new(1.0, 2.0, 3.0, 4.0));
    }
    #[test]
    fn test_mul_scalar_distributive() {
        let a = Vec4::new(1.0, 2.0, 3.0, 4.0);
        let b = Vec4::new(5.0, 6.0, 7.0, 8.0);
        let s = 2.0;
        assert_eq!((a + b) * s, a * s + b * s);
    }
    #[test]
    fn test_mul_vec4() {
        let r = Vec4::new(1.0, 2.0, 3.0, 4.0) * Vec4::new(5.0, 6.0, 7.0, 8.0);
        assert_eq!(r, Vec4::new(5.0, 12.0, 21.0, 32.0));
    }
    #[test]
    fn test_mul_vec4_zero() {
        let r = Vec4::new(1.0, 2.0, 3.0, 4.0) * Vec4::ZERO;
        assert_eq!(r, Vec4::ZERO);
    }
    #[test]
    fn test_mul_vec4_ones() {
        let r = Vec4::new(1.0, 2.0, 3.0, 4.0) * Vec4::new(1.0, 1.0, 1.0, 1.0);
        assert_eq!(r, Vec4::new(1.0, 2.0, 3.0, 4.0));
    }
    #[test]
    fn test_mul_vec4_commutative() {
        let a = Vec4::new(1.0, 2.0, 3.0, 4.0);
        let b = Vec4::new(5.0, 6.0, 7.0, 8.0);
        assert_eq!(a * b, b * a);
    }
    #[test]
    fn test_div_scalar_2() {
        let r = Vec4::new(2.0, 4.0, 6.0, 8.0) / 2.0;
        assert_eq!(r, Vec4::new(1.0, 2.0, 3.0, 4.0));
    }
    #[test]
    fn test_div_scalar_05() {
        let r = Vec4::new(1.0, 2.0, 3.0, 4.0) / 0.5;
        assert_eq!(r, Vec4::new(2.0, 4.0, 6.0, 8.0));
    }
    #[test]
    fn test_div_scalar_neg() {
        let r = Vec4::new(2.0, 4.0, 6.0, 8.0) / (-2.0);
        assert_eq!(r, Vec4::new(-1.0, -2.0, -3.0, -4.0));
    }
    #[test]
    fn test_div_mul_inverse() {
        let a = Vec4::new(2.0, 4.0, 6.0, 8.0);
        let r = (a * 3.0) / 3.0;
        assert!((r.x - 2.0).abs() < TOL);
        assert!((r.y - 4.0).abs() < TOL);
    }
    #[test]
    fn test_lerp_commutativity_endpoints() {
        let a = Vec4::new(0.0, 0.0, 0.0, 0.0);
        let b = Vec4::new(100.0, 100.0, 100.0, 100.0);
        let r1 = Vec4::lerp(&a, &b, 0.3);
        let r2 = Vec4::lerp(&b, &a, 0.7);
        assert!((r1.x - r2.x).abs() < TOL);
    }
    #[test]
    fn test_lerp_bounds_t_negative() {
        let r = Vec4::lerp(
            &Vec4::new(0.0, 0.0, 0.0, 0.0),
            &Vec4::new(10.0, 10.0, 10.0, 10.0),
            -1.0,
        );
        assert!((r.x - (-10.0)).abs() < TOL);
    }
    #[test]
    fn test_lerp_bounds_t_over_1() {
        let r = Vec4::lerp(
            &Vec4::new(0.0, 0.0, 0.0, 0.0),
            &Vec4::new(10.0, 10.0, 10.0, 10.0),
            2.0,
        );
        assert!((r.x - 20.0).abs() < TOL);
    }
    #[test]
    fn test_lerp_extreme_values() {
        let r = Vec4::lerp(
            &Vec4::new(-1e6, -1e6, -1e6, -1e6),
            &Vec4::new(1e6, 1e6, 1e6, 1e6),
            0.5,
        );
        assert!((r.x - 0.0).abs() < 1.0);
    }
    #[test]
    fn test_lerp_identical() {
        let a = Vec4::new(42.0, 42.0, 42.0, 42.0);
        let r = Vec4::lerp(&a, &a, 0.999);
        assert!((r.x - 42.0).abs() < TOL);
    }
    #[test]
    fn test_magnitude_pythagorean() {
        assert!((Vec4::new(5.0, 12.0, 0.0, 0.0).magnitude() - 13.0).abs() < TOL);
    }
    #[test]
    fn test_magnitude_8_15_17() {
        assert!((Vec4::new(8.0, 15.0, 0.0, 0.0).magnitude() - 17.0).abs() < TOL);
    }
    #[test]
    fn test_normalize_result_magnitude() {
        let v = Vec4::new(7.0, 24.0, 0.0, 0.0).normalize();
        assert!((v.magnitude() - 1.0).abs() < TOL);
    }
    #[test]
    fn test_clamp_does_not_change_under() {
        let v = Vec4::new(1.0, 1.0, 1.0, 1.0);
        let c = v.clamp_magnitude(10.0);
        assert_eq!(v, c);
    }
    #[test]
    fn test_distance_triangle_inequality() {
        let a = Vec4::new(0.0, 0.0, 0.0, 0.0);
        let b = Vec4::new(3.0, 0.0, 0.0, 0.0);
        let c = Vec4::new(3.0, 4.0, 0.0, 0.0);
        assert!(a.distance_to(&c) <= a.distance_to(&b) + b.distance_to(&c) + TOL);
    }
    #[test]
    fn test_distance_symmetric() {
        let a = Vec4::new(1.0, 2.0, 3.0, 4.0);
        let b = Vec4::new(5.0, 6.0, 7.0, 8.0);
        assert!((a.distance_to(&b) - b.distance_to(&a)).abs() < TOL);
    }
    #[test]
    fn test_add_then_sub_identity() {
        let a = Vec4::new(1.0, 2.0, 3.0, 4.0);
        let b = Vec4::new(5.0, 6.0, 7.0, 8.0);
        assert_eq!((a + b) - b, a);
    }
    #[test]
    fn test_mul_then_div_identity() {
        let a = Vec4::new(2.0, 4.0, 6.0, 8.0);
        let s = 3.0;
        let r = (a * s) / s;
        assert!((r.x - a.x).abs() < TOL);
        assert!((r.y - a.y).abs() < TOL);
    }
    #[test]
    fn test_vec4_equality_negative_zero() {
        let a = Vec4::new(-0.0, -0.0, -0.0, -0.0);
        let b = Vec4::new(0.0, 0.0, 0.0, 0.0);
        assert_eq!(a, b);
    }
    #[test]
    fn test_vec4_partial_eq_reflexive() {
        let a = Vec4::new(1.0, 2.0, 3.0, 4.0);
        assert_eq!(a, a);
    }
    #[test]
    fn test_vec4_partial_eq_symmetric() {
        let a = Vec4::new(1.0, 2.0, 3.0, 4.0);
        let b = Vec4::new(1.0, 2.0, 3.0, 4.0);
        assert_eq!(a, b);
        assert_eq!(b, a);
    }
    #[test]
    fn test_vec4_partial_eq_transitive() {
        let a = Vec4::new(1.0, 2.0, 3.0, 4.0);
        let b = Vec4::new(1.0, 2.0, 3.0, 4.0);
        let c = Vec4::new(1.0, 2.0, 3.0, 4.0);
        if a == b && b == c {
            assert_eq!(a, c);
        }
    }
    #[test]
    fn test_vec4_clone_identity() {
        let a = Vec4::new(1.0, 2.0, 3.0, 4.0);
        let b = a.clone();
        assert_eq!(a, b);
    }
    #[test]
    fn test_vec4_debug_format() {
        let v = Vec4::new(1.5, 2.5, 3.5, 4.5);
        let s = format!("{:?}", v);
        assert!(s.contains("1.5"));
        assert!(s.contains("4.5"));
    }
    #[test]
    fn test_vec4_magnitude_non_negative() {
        let v = Vec4::new(-100.0, -200.0, -300.0, -400.0);
        assert!(v.magnitude() >= 0.0);
    }
    #[test]
    fn test_vec4_clamp_zero_max() {
        let v = Vec4::new(1.0, 2.0, 3.0, 4.0).clamp_magnitude(0.0);
        assert_eq!(v, Vec4::ZERO);
    }
    #[test]
    fn test_vec4_normalize_large_values() {
        let v = Vec4::new(10000.0, 20000.0, 30000.0, 40000.0).normalize();
        assert!((v.magnitude() - 1.0).abs() < 0.001);
    }
    #[test]
    fn test_vec4_lerp_midpoint() {
        let a = Vec4::new(0.0, 0.0, 0.0, 0.0);
        let b = Vec4::new(2.0, 2.0, 2.0, 2.0);
        let m = Vec4::lerp(&a, &b, 0.5);
        assert!((m.x - 1.0).abs() < TOL);
        assert!((m.y - 1.0).abs() < TOL);
    }
    #[test]
    fn test_vec4_add_large_values() {
        let r = Vec4::new(1e10, 1e10, 1e10, 1e10) + Vec4::new(1e10, 1e10, 1e10, 1e10);
        assert!((r.x - 2e10).abs() < 1.0);
    }
    #[test]
    fn test_vec4_sub_large_values() {
        let r = Vec4::new(1e10, 1e10, 1e10, 1e10) - Vec4::new(1e10, 1e10, 1e10, 1e10);
        assert_eq!(r, Vec4::ZERO);
    }
    #[test]
    fn test_vec4_mul_scalar_large() {
        let r = Vec4::new(1.0, 1.0, 1.0, 1.0) * 1e10;
        assert!((r.x - 1e10).abs() < 1e5);
    }
    #[test]
    fn test_vec4_div_scalar_large() {
        let r = Vec4::new(1e10, 1e10, 1e10, 1e10) / 1e10;
        assert!((r.x - 1.0).abs() < TOL);
    }
    #[test]
    fn test_vec4_magnitude_overflow_protection() {
        let v = Vec4::new(1e15, 1e15, 1e15, 1e15);
        let m = v.magnitude();
        assert!(m.is_finite());
    }
    #[test]
    fn test_vec4_sanitize_all_inf() {
        let v = Vec4::new(f32::INFINITY, f32::INFINITY, f32::INFINITY, f32::INFINITY).sanitize();
        assert_eq!(v, Vec4::ZERO);
    }
    #[test]
    fn test_vec4_sanitize_mixed() {
        let v = Vec4::new(1.0, f32::NAN, 3.0, f32::INFINITY).sanitize();
        assert_eq!(v, Vec4::ZERO);
    }
}

#[cfg(test)]
mod aether_guard_tests {
    use super::aether_guard::*;
    use super::Vec4;

    const TOL: f32 = 1e-5;

    #[test]
    fn test_epsilon_value() {
        assert_eq!(EPSILON, 1e-9);
    }
    #[test]
    fn test_max_velocity_value() {
        assert_eq!(MAX_VELOCITY, 5000.0);
    }
    #[test]
    fn test_max_acceleration_value() {
        assert_eq!(MAX_ACCELERATION, 10000.0);
    }
    #[test]
    fn test_snap_distance_value() {
        assert_eq!(SNAP_DISTANCE, 0.5);
    }
    #[test]
    fn test_snap_velocity_value() {
        assert_eq!(SNAP_VELOCITY, 5.0);
    }
    #[test]
    fn test_max_physics_k_value() {
        assert_eq!(MAX_PHYSICS_K, 10000.0);
    }
    #[test]
    fn test_safe_divide_normal() {
        assert!((safe_divide(10.0, 2.0) - 5.0).abs() < TOL);
    }
    #[test]
    fn test_safe_divide_zero_denom() {
        let r = safe_divide(10.0, 0.0);
        assert!((r - 10.0 / 1e-9).abs() < 1.0);
    }
    #[test]
    fn test_safe_divide_negative_num() {
        assert!((safe_divide(-10.0, 2.0) - (-5.0)).abs() < TOL);
    }
    #[test]
    fn test_safe_divide_zero_num() {
        assert!((safe_divide(0.0, 5.0) - 0.0).abs() < TOL);
    }
    #[test]
    fn test_safe_divide_tiny_denom() {
        let r = safe_divide(1.0, 1e-10);
        assert!((r - 1.0 / 1e-9).abs() < 1.0);
    }
    #[test]
    fn test_safe_divide_both_zero() {
        assert!((safe_divide(0.0, 0.0) - 0.0).abs() < TOL);
    }
    #[test]
    fn test_safe_divide_negative_denom() {
        assert!((safe_divide(10.0, -2.0) - (-5.0)).abs() < TOL);
    }
    #[test]
    fn test_safe_divide_large_values() {
        let r = safe_divide(1e10, 1e5);
        assert!((r - 1e5).abs() < 1.0);
    }
    #[test]
    fn test_safe_divide_one() {
        assert!((safe_divide(1.0, 1.0) - 1.0).abs() < TOL);
    }
    #[test]
    fn test_safe_divide_neg_neg() {
        assert!((safe_divide(-6.0, -3.0) - 2.0).abs() < TOL);
    }
    #[test]
    fn test_safe_divide_epsilon_denom() {
        let r = safe_divide(1.0, EPSILON);
        assert!((r - 1e9).abs() < 1.0);
    }
    #[test]
    fn test_safe_divide_neg_epsilon() {
        let r = safe_divide(1.0, -EPSILON);
        assert!((r - (-1e9)).abs() < 1.0);
    }
    #[test]
    fn test_clamp_velocity_under() {
        let v = Vec4::new(100.0, 200.0, 0.0, 0.0).clamp_magnitude(MAX_VELOCITY);
        assert!(v.magnitude() <= MAX_VELOCITY + TOL);
    }
    #[test]
    fn test_clamp_velocity_over() {
        let v = Vec4::new(10000.0, 20000.0, 0.0, 0.0).clamp_magnitude(MAX_VELOCITY);
        assert!((v.magnitude() - MAX_VELOCITY).abs() < TOL);
    }
    #[test]
    fn test_clamp_velocity_zero() {
        let v = Vec4::ZERO.clamp_magnitude(MAX_VELOCITY);
        assert_eq!(v, Vec4::ZERO);
    }
    #[test]
    fn test_clamp_velocity_exact() {
        let v = Vec4::new(3000.0, 4000.0, 0.0, 0.0).clamp_magnitude(MAX_VELOCITY);
        assert_eq!(v, Vec4::new(3000.0, 4000.0, 0.0, 0.0));
    }
    #[test]
    fn test_clamp_acceleration_under() {
        let a = Vec4::new(100.0, 200.0, 0.0, 0.0).clamp_magnitude(MAX_ACCELERATION);
        assert!(a.magnitude() <= MAX_ACCELERATION + TOL);
    }
    #[test]
    fn test_clamp_acceleration_over() {
        let a = Vec4::new(100000.0, 200000.0, 0.0, 0.0).clamp_magnitude(MAX_ACCELERATION);
        assert!((a.magnitude() - MAX_ACCELERATION).abs() < TOL);
    }
    #[test]
    fn test_clamp_acceleration_exact() {
        let a = Vec4::new(6000.0, 8000.0, 0.0, 0.0).clamp_magnitude(MAX_ACCELERATION);
        assert_eq!(a, Vec4::new(6000.0, 8000.0, 0.0, 0.0));
    }
    #[test]
    fn test_clamp_force_under() {
        let f = Vec4::new(100.0, 200.0, 0.0, 0.0).clamp_magnitude(MAX_PHYSICS_K);
        assert!(f.magnitude() <= MAX_PHYSICS_K + TOL);
    }
    #[test]
    fn test_clamp_force_over() {
        let f = Vec4::new(50000.0, 100000.0, 0.0, 0.0).clamp_magnitude(MAX_PHYSICS_K);
        assert!((f.magnitude() - MAX_PHYSICS_K).abs() < TOL);
    }
    #[test]
    fn test_clamp_force_zero() {
        let f = Vec4::ZERO.clamp_magnitude(MAX_PHYSICS_K);
        assert_eq!(f, Vec4::ZERO);
    }
    #[test]
    fn test_sanitize_dt_normal() {
        assert!((sanitize_dt(0.016) - 0.016).abs() < TOL);
    }
    #[test]
    fn test_sanitize_dt_zero() {
        assert!((sanitize_dt(0.0) - 0.0).abs() < TOL);
    }
    #[test]
    fn test_sanitize_dt_negative() {
        assert!((sanitize_dt(-1.0) - 0.0).abs() < TOL);
    }
    #[test]
    fn test_sanitize_dt_over_one() {
        assert!((sanitize_dt(2.0) - 1.0).abs() < TOL);
    }
    #[test]
    fn test_sanitize_dt_60fps() {
        assert!((sanitize_dt(1.0 / 60.0) - (1.0 / 60.0)).abs() < TOL);
    }
    #[test]
    fn test_sanitize_dt_120fps() {
        assert!((sanitize_dt(1.0 / 120.0) - (1.0 / 120.0)).abs() < TOL);
    }
    #[test]
    fn test_sanitize_dt_very_small() {
        assert!(sanitize_dt(1e-10) >= 0.0);
    }
    #[test]
    fn test_sanitize_dt_huge() {
        assert!((sanitize_dt(1e10) - 1.0).abs() < TOL);
    }
    #[test]
    fn test_check_snap_true() {
        assert!(check_snap(
            &Vec4::new(100.0, 100.0, 50.0, 50.0),
            &Vec4::new(100.1, 100.1, 50.0, 50.0),
            &Vec4::new(1.0, 1.0, 0.0, 0.0)
        ));
    }
    #[test]
    fn test_check_snap_false_distance() {
        assert!(!check_snap(
            &Vec4::new(100.0, 100.0, 50.0, 50.0),
            &Vec4::new(200.0, 200.0, 50.0, 50.0),
            &Vec4::new(1.0, 1.0, 0.0, 0.0)
        ));
    }
    #[test]
    fn test_check_snap_false_velocity() {
        assert!(!check_snap(
            &Vec4::new(100.0, 100.0, 50.0, 50.0),
            &Vec4::new(100.1, 100.1, 50.0, 50.0),
            &Vec4::new(10.0, 10.0, 0.0, 0.0)
        ));
    }
    #[test]
    fn test_check_snap_exact_distance() {
        assert!(!check_snap(
            &Vec4::new(100.0, 100.0, 50.0, 50.0),
            &Vec4::new(100.5, 100.0, 50.0, 50.0),
            &Vec4::new(1.0, 1.0, 0.0, 0.0)
        ));
    }
    #[test]
    fn test_check_snap_exact_velocity() {
        assert!(!check_snap(
            &Vec4::new(100.0, 100.0, 50.0, 50.0),
            &Vec4::new(100.1, 100.1, 50.0, 50.0),
            &Vec4::new(5.0, 0.0, 0.0, 0.0)
        ));
    }
    #[test]
    fn test_check_snap_at_target() {
        assert!(check_snap(
            &Vec4::new(100.0, 100.0, 50.0, 50.0),
            &Vec4::new(100.0, 100.0, 50.0, 50.0),
            &Vec4::new(0.0, 0.0, 0.0, 0.0)
        ));
    }
    #[test]
    fn test_check_snap_very_close() {
        assert!(check_snap(
            &Vec4::new(100.0, 100.0, 50.0, 50.0),
            &Vec4::new(100.001, 100.001, 50.0, 50.0),
            &Vec4::new(0.01, 0.01, 0.0, 0.0)
        ));
    }
    #[test]
    fn test_check_snap_zero_velocity() {
        assert!(check_snap(
            &Vec4::new(100.0, 100.0, 50.0, 50.0),
            &Vec4::new(100.2, 100.2, 50.0, 50.0),
            &Vec4::new(0.0, 0.0, 0.0, 0.0)
        ));
    }
}

#[cfg(test)]
mod state_tensor_tests {
    use super::aether_guard::*;
    use super::StateTensor;
    use super::Vec4;

    const TOL: f32 = 1e-4;

    #[test]
    fn test_new() {
        let s = StateTensor::new(10.0, 20.0, 100.0, 50.0);
        assert!((s.state.x - 10.0).abs() < TOL);
        assert_eq!(s.velocity, Vec4::ZERO);
        assert_eq!(s.acceleration, Vec4::ZERO);
    }
    #[test]
    fn test_new_zero() {
        let s = StateTensor::new(0.0, 0.0, 0.0, 0.0);
        assert_eq!(s.state, Vec4::ZERO);
    }
    #[test]
    fn test_new_negative() {
        let s = StateTensor::new(-10.0, -20.0, 100.0, 50.0);
        assert!((s.state.x - (-10.0)).abs() < TOL);
    }
    #[test]
    fn test_apply_force() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        s.apply_force(Vec4::new(10.0, 20.0, 0.0, 0.0));
        assert!((s.acceleration.x - 10.0).abs() < TOL);
        assert!((s.acceleration.y - 20.0).abs() < TOL);
    }
    #[test]
    fn test_apply_force_accumulates() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        s.apply_force(Vec4::new(10.0, 0.0, 0.0, 0.0));
        s.apply_force(Vec4::new(5.0, 0.0, 0.0, 0.0));
        assert!((s.acceleration.x - 15.0).abs() < TOL);
    }
    #[test]
    fn test_apply_force_nan_sanitized() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        s.apply_force(Vec4::new(f32::NAN, 0.0, 0.0, 0.0));
        assert_eq!(s.acceleration, Vec4::ZERO);
    }
    #[test]
    fn test_apply_force_clamped() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        s.apply_force(Vec4::new(100000.0, 200000.0, 0.0, 0.0));
        assert!(s.acceleration.magnitude() <= MAX_ACCELERATION + TOL);
    }
    #[test]
    fn test_apply_force_zero() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        s.apply_force(Vec4::ZERO);
        assert_eq!(s.acceleration, Vec4::ZERO);
    }
    #[test]
    fn test_apply_force_negative() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        s.apply_force(Vec4::new(-10.0, -20.0, 0.0, 0.0));
        assert!((s.acceleration.x - (-10.0)).abs() < TOL);
    }
    #[test]
    fn test_apply_force_multiple_accumulation() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        for _ in 0..10 {
            s.apply_force(Vec4::new(1.0, 0.0, 0.0, 0.0));
        }
        assert!((s.acceleration.x - 10.0).abs() < TOL);
    }
    #[test]
    fn test_euler_basic() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        s.apply_force(Vec4::new(100.0, 100.0, 0.0, 0.0));
        s.euler_integrate(0.016, 0.1, None);
        assert!(s.velocity.x > 0.0);
        assert!(s.state.x > 0.0);
    }
    #[test]
    fn test_euler_velocity_formula() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        s.acceleration = Vec4::new(100.0, 0.0, 0.0, 0.0);
        let dt = 0.016;
        let visc = 0.1;
        s.euler_integrate(dt, visc, None);
        let expected_vx = (0.0 + 100.0 * dt) * (1.0 - visc);
        assert!((s.velocity.x - expected_vx).abs() < TOL);
    }
    #[test]
    fn test_euler_position_formula() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        s.acceleration = Vec4::new(100.0, 0.0, 0.0, 0.0);
        let dt = 0.016;
        let visc = 0.1;
        s.euler_integrate(dt, visc, None);
        let expected_vx = (0.0 + 100.0 * dt) * (1.0 - visc);
        let expected_sx = 0.0 + expected_vx * dt;
        assert!((s.state.x - expected_sx).abs() < TOL);
    }
    #[test]
    fn test_euler_resets_acceleration() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        s.acceleration = Vec4::new(100.0, 100.0, 0.0, 0.0);
        s.euler_integrate(0.016, 0.1, None);
        assert_eq!(s.acceleration, Vec4::ZERO);
    }
    #[test]
    fn test_euler_clamps_negative_w() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        s.velocity = Vec4::new(0.0, 0.0, -500.0, 0.0);
        s.euler_integrate(1.0, 0.0, None);
        assert!(s.state.w >= 0.0);
    }
    #[test]
    fn test_euler_clamps_negative_h() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        s.velocity = Vec4::new(0.0, 0.0, 0.0, -500.0);
        s.euler_integrate(1.0, 0.0, None);
        assert!(s.state.h >= 0.0);
    }
    #[test]
    fn test_euler_velocity_clamped() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        s.acceleration = Vec4::new(1000000.0, 0.0, 0.0, 0.0);
        s.euler_integrate(1.0, 0.0, None);
        assert!(s.velocity.magnitude() <= MAX_VELOCITY + TOL);
    }
    #[test]
    fn test_euler_nan_state_recovery() {
        let mut s = StateTensor::new(f32::NAN, 0.0, 100.0, 100.0);
        s.euler_integrate(0.016, 0.1, None);
        assert!(!s.state.is_nan());
    }
    #[test]
    fn test_euler_nan_velocity_recovery() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        s.velocity = Vec4::new(f32::NAN, 0.0, 0.0, 0.0);
        s.euler_integrate(0.016, 0.1, None);
        assert!(!s.velocity.is_nan());
    }
    #[test]
    fn test_euler_snap_to_target() {
        let mut s = StateTensor::new(100.0, 100.0, 50.0, 50.0);
        s.velocity = Vec4::new(0.1, 0.1, 0.0, 0.0);
        let target = Vec4::new(100.0, 100.0, 50.0, 50.0);
        s.euler_integrate(0.016, 0.1, Some(&target));
        assert!((s.state.x - 100.0).abs() < TOL);
        assert_eq!(s.velocity, Vec4::ZERO);
    }
    #[test]
    fn test_euler_no_snap_far() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        let target = Vec4::new(500.0, 500.0, 100.0, 100.0);
        s.euler_integrate(0.016, 0.1, Some(&target));
        assert!((s.state.x - 500.0).abs() > TOL);
    }
    #[test]
    fn test_euler_zero_dt() {
        let mut s = StateTensor::new(100.0, 100.0, 50.0, 50.0);
        s.acceleration = Vec4::new(100.0, 0.0, 0.0, 0.0);
        let old_state = s.state;
        s.euler_integrate(0.0, 0.1, None);
        assert!((s.state.x - old_state.x).abs() < TOL);
    }
    #[test]
    fn test_euler_negative_dt() {
        let mut s = StateTensor::new(100.0, 100.0, 50.0, 50.0);
        s.acceleration = Vec4::new(100.0, 0.0, 0.0, 0.0);
        let old_state = s.state;
        s.euler_integrate(-1.0, 0.1, None);
        assert!((s.state.x - old_state.x).abs() < TOL);
    }
    #[test]
    fn test_euler_high_viscosity() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        s.acceleration = Vec4::new(100.0, 0.0, 0.0, 0.0);
        s.euler_integrate(0.016, 0.9, None);
        assert!(s.velocity.x < 2.0);
    }
    #[test]
    fn test_euler_zero_viscosity() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        s.acceleration = Vec4::new(100.0, 0.0, 0.0, 0.0);
        s.euler_integrate(0.016, 0.0, None);
        let expected_vx = 100.0 * 0.016;
        assert!((s.velocity.x - expected_vx).abs() < TOL);
    }
    #[test]
    fn test_euler_multiple_frames() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        let target = Vec4::new(400.0, 300.0, 200.0, 150.0);
        for _ in 0..60 {
            s.apply_force((target - s.state) * 0.1);
            s.euler_integrate(0.016, 0.1, Some(&target));
        }
        assert!(s.state.x > 0.0);
        assert!(s.state.x < target.x);
    }
    #[test]
    fn test_euler_convergence_100_frames() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        let target = Vec4::new(400.0, 300.0, 200.0, 150.0);
        for _ in 0..100 {
            s.apply_force((target - s.state) * 0.1);
            s.euler_integrate(0.016, 0.1, Some(&target));
        }
        assert!(s.state.x > 0.0);
        assert!(s.state.x < target.x);
        assert!(!s.state.is_nan());
        assert!(!s.velocity.is_nan());
    }
    #[test]
    fn test_euler_energy_decay() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        s.velocity = Vec4::new(1000.0, 1000.0, 0.0, 0.0);
        s.acceleration = Vec4::ZERO;
        let initial_energy = s.velocity.magnitude();
        s.euler_integrate(0.016, 0.1, None);
        let final_energy = s.velocity.magnitude();
        assert!(final_energy < initial_energy);
    }
    #[test]
    fn test_euler_symplectic_order() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        s.acceleration = Vec4::new(100.0, 0.0, 0.0, 0.0);
        let dt = 0.016;
        s.euler_integrate(dt, 0.0, None);
        let expected_v = 100.0 * dt;
        let expected_s = expected_v * dt;
        assert!((s.state.x - expected_s).abs() < TOL);
    }
    #[test]
    fn test_euler_stability_1000_frames() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        let target = Vec4::new(400.0, 300.0, 200.0, 150.0);
        for _ in 0..1000 {
            s.apply_force((target - s.state) * 0.1);
            s.euler_integrate(0.016, 0.1, Some(&target));
        }
        assert!(!s.state.is_nan());
        assert!(!s.velocity.is_nan());
    }
    #[test]
    fn test_euler_large_dt_capped() {
        let mut s = StateTensor::new(0.0, 0.0, 100.0, 100.0);
        s.acceleration = Vec4::new(100.0, 0.0, 0.0, 0.0);
        s.euler_integrate(100.0, 0.1, None);
        assert!(s.state.x.is_finite());
    }
}
