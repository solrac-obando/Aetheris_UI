pub mod elements;
pub mod engine;
pub mod input_manager;
pub mod solver;
pub mod state_manager;

pub use elements::*;
pub use engine::AetherEngine;
pub use input_manager::InputManager;
pub use solver::*;
pub use state_manager::StateManager;

#[cfg(test)]
mod solver_tests {
    use super::*;
    use aether_math::Vec4;
    const TOL: f32 = 1e-5;

    #[test]
    fn test_restoring_force_basic() {
        let f = calculate_restoring_force(
            Vec4::new(0.0, 0.0, 100.0, 100.0),
            Vec4::new(100.0, 100.0, 100.0, 100.0),
            0.1,
        );
        assert!((f.x - 10.0).abs() < TOL);
        assert!((f.y - 10.0).abs() < TOL);
    }
    #[test]
    fn test_restoring_force_zero_error() {
        let f = calculate_restoring_force(
            Vec4::new(100.0, 100.0, 50.0, 50.0),
            Vec4::new(100.0, 100.0, 50.0, 50.0),
            0.1,
        );
        assert!(f.magnitude() < TOL);
    }
    #[test]
    fn test_restoring_force_k1() {
        let f = calculate_restoring_force(
            Vec4::new(0.0, 0.0, 100.0, 100.0),
            Vec4::new(100.0, 100.0, 100.0, 100.0),
            1.0,
        );
        assert!((f.x - 100.0).abs() < TOL);
    }
    #[test]
    fn test_restoring_force_k10() {
        let f = calculate_restoring_force(
            Vec4::new(0.0, 0.0, 100.0, 100.0),
            Vec4::new(100.0, 100.0, 100.0, 100.0),
            10.0,
        );
        assert!((f.x - 1000.0).abs() < TOL);
    }
    #[test]
    fn test_restoring_force_negative() {
        let f = calculate_restoring_force(
            Vec4::new(200.0, 200.0, 100.0, 100.0),
            Vec4::new(100.0, 100.0, 100.0, 100.0),
            0.1,
        );
        assert!(f.x < 0.0);
        assert!(f.y < 0.0);
    }
    #[test]
    fn test_restoring_force_invalid_k_negative() {
        let f = calculate_restoring_force(
            Vec4::new(0.0, 0.0, 100.0, 100.0),
            Vec4::new(100.0, 100.0, 100.0, 100.0),
            -1.0,
        );
        assert!((f.x - 10.0).abs() < TOL);
    }
    #[test]
    fn test_restoring_force_invalid_k_huge() {
        let f = calculate_restoring_force(
            Vec4::new(0.0, 0.0, 100.0, 100.0),
            Vec4::new(100.0, 100.0, 100.0, 100.0),
            1e20,
        );
        assert!(f.magnitude() <= 10000.0 + TOL);
    }
    #[test]
    fn test_restoring_force_clamped() {
        let f = calculate_restoring_force(
            Vec4::new(0.0, 0.0, 0.0, 0.0),
            Vec4::new(10000.0, 10000.0, 0.0, 0.0),
            100.0,
        );
        assert!(f.magnitude() <= 10000.0 + TOL);
    }
    #[test]
    fn test_restoring_force_only_x() {
        let f = calculate_restoring_force(
            Vec4::new(0.0, 0.0, 100.0, 100.0),
            Vec4::new(50.0, 0.0, 100.0, 100.0),
            0.1,
        );
        assert!((f.x - 5.0).abs() < TOL);
        assert!((f.y - 0.0).abs() < TOL);
    }
    #[test]
    fn test_restoring_force_only_w() {
        let f = calculate_restoring_force(
            Vec4::new(0.0, 0.0, 100.0, 100.0),
            Vec4::new(0.0, 0.0, 200.0, 100.0),
            0.1,
        );
        assert!((f.w - 10.0).abs() < TOL);
    }

    #[test]
    fn test_boundary_inside() {
        let f = calculate_boundary_forces(Vec4::new(50.0, 50.0, 100.0, 100.0), 800.0, 600.0, 0.5);
        assert!(f.magnitude() < TOL);
    }
    #[test]
    fn test_boundary_left() {
        let f = calculate_boundary_forces(Vec4::new(-50.0, 50.0, 100.0, 100.0), 800.0, 600.0, 0.5);
        assert!(f.x > 0.0);
        assert!((f.x - 25.0).abs() < TOL);
    }
    #[test]
    fn test_boundary_right() {
        let f = calculate_boundary_forces(Vec4::new(750.0, 50.0, 100.0, 100.0), 800.0, 600.0, 0.5);
        assert!(f.x < 0.0);
        assert!((f.x - (-25.0)).abs() < TOL);
    }
    #[test]
    fn test_boundary_top() {
        let f = calculate_boundary_forces(Vec4::new(50.0, -50.0, 100.0, 100.0), 800.0, 600.0, 0.5);
        assert!(f.y > 0.0);
        assert!((f.y - 25.0).abs() < TOL);
    }
    #[test]
    fn test_boundary_bottom() {
        let f = calculate_boundary_forces(Vec4::new(50.0, 550.0, 100.0, 100.0), 800.0, 600.0, 0.5);
        assert!(f.y < 0.0);
        assert!((f.y - (-25.0)).abs() < TOL);
    }
    #[test]
    fn test_boundary_clamped() {
        let f =
            calculate_boundary_forces(Vec4::new(-100000.0, 0.0, 100.0, 100.0), 800.0, 600.0, 0.5);
        assert!(f.magnitude() <= 5000.0 + TOL);
    }
    #[test]
    fn test_boundary_both_axes() {
        let f = calculate_boundary_forces(Vec4::new(-50.0, -50.0, 100.0, 100.0), 800.0, 600.0, 0.5);
        assert!(f.x > 0.0);
        assert!(f.y > 0.0);
    }
    #[test]
    fn test_boundary_exact_edge() {
        let f = calculate_boundary_forces(Vec4::new(0.0, 0.0, 100.0, 100.0), 800.0, 600.0, 0.5);
        assert!(f.magnitude() < TOL);
    }
    #[test]
    fn test_boundary_right_exact() {
        let f = calculate_boundary_forces(Vec4::new(700.0, 50.0, 100.0, 100.0), 800.0, 600.0, 0.5);
        assert!(f.magnitude() < TOL);
    }
    #[test]
    fn test_boundary_zero_container() {
        let f = calculate_boundary_forces(Vec4::new(10.0, 10.0, 100.0, 100.0), 0.0, 0.0, 0.5);
        assert!(f.magnitude() > 0.0);
    }

    #[test]
    fn test_lerp_t0() {
        let r = lerp(
            Vec4::new(0.0, 0.0, 0.0, 0.0),
            Vec4::new(100.0, 100.0, 100.0, 100.0),
            0.0,
        );
        assert!((r.x - 0.0).abs() < TOL);
    }
    #[test]
    fn test_lerp_t1() {
        let r = lerp(
            Vec4::new(0.0, 0.0, 0.0, 0.0),
            Vec4::new(100.0, 100.0, 100.0, 100.0),
            1.0,
        );
        assert!((r.x - 100.0).abs() < TOL);
    }
    #[test]
    fn test_lerp_t05() {
        let r = lerp(
            Vec4::new(0.0, 0.0, 0.0, 0.0),
            Vec4::new(100.0, 100.0, 100.0, 100.0),
            0.5,
        );
        assert!((r.x - 50.0).abs() < TOL);
    }
    #[test]
    fn test_lerp_t025() {
        let r = lerp(
            Vec4::new(0.0, 0.0, 0.0, 0.0),
            Vec4::new(100.0, 100.0, 100.0, 100.0),
            0.25,
        );
        assert!((r.x - 25.0).abs() < TOL);
    }
    #[test]
    fn test_lerp_t075() {
        let r = lerp(
            Vec4::new(0.0, 0.0, 0.0, 0.0),
            Vec4::new(100.0, 100.0, 100.0, 100.0),
            0.75,
        );
        assert!((r.x - 75.0).abs() < TOL);
    }

    #[test]
    fn test_speed_to_stiffness_zero() {
        assert!((speed_to_stiffness(0.0) - 0.1).abs() < TOL);
    }
    #[test]
    fn test_speed_to_stiffness_negative() {
        assert!((speed_to_stiffness(-100.0) - 0.1).abs() < TOL);
    }
    #[test]
    fn test_speed_to_stiffness_300ms() {
        let expected = 16.0 / (0.3 * 0.3);
        assert!((speed_to_stiffness(300.0) - expected).abs() < TOL);
    }
    #[test]
    fn test_speed_to_stiffness_1000ms() {
        assert!((speed_to_stiffness(1000.0) - 16.0).abs() < TOL);
    }
    #[test]
    fn test_speed_to_stiffness_10ms() {
        assert!((speed_to_stiffness(10.0) - 10000.0).abs() < TOL);
    }
    #[test]
    fn test_speed_to_stiffness_capped() {
        assert!(speed_to_stiffness(1.0) <= 10000.0 + TOL);
    }
    #[test]
    fn test_speed_to_stiffness_tiny() {
        assert!(speed_to_stiffness(0.001) <= 10000.0 + TOL);
    }

    #[test]
    fn test_speed_to_viscosity_zero() {
        assert!((speed_to_viscosity(0.0) - 0.1).abs() < TOL);
    }
    #[test]
    fn test_speed_to_viscosity_negative() {
        assert!((speed_to_viscosity(-100.0) - 0.1).abs() < TOL);
    }
    #[test]
    fn test_speed_to_viscosity_300ms() {
        assert!((speed_to_viscosity(300.0) - 0.7).abs() < TOL);
    }
    #[test]
    fn test_speed_to_viscosity_950ms() {
        assert!((speed_to_viscosity(950.0) - 0.05).abs() < TOL);
    }
    #[test]
    fn test_speed_to_viscosity_50ms() {
        assert!((speed_to_viscosity(50.0) - 0.95).abs() < TOL);
    }
    #[test]
    fn test_speed_to_viscosity_clamped_min() {
        assert!(speed_to_viscosity(999.0) >= 0.05 - TOL);
    }
    #[test]
    fn test_speed_to_viscosity_clamped_max() {
        assert!(speed_to_viscosity(10.0) <= 0.95 + TOL);
    }

    #[test]
    fn test_batch_restoring_1_element() {
        let states = [Vec4::new(0.0, 0.0, 100.0, 100.0)];
        let targets = [Vec4::new(100.0, 100.0, 100.0, 100.0)];
        let mut forces = [Vec4::ZERO];
        batch_restoring_forces(&states, &targets, 0.1, &mut forces);
        assert!((forces[0].x - 10.0).abs() < TOL);
    }
    #[test]
    fn test_batch_restoring_3_elements() {
        let states = [
            Vec4::new(0.0, 0.0, 100.0, 100.0),
            Vec4::new(0.0, 0.0, 100.0, 100.0),
            Vec4::new(0.0, 0.0, 100.0, 100.0),
        ];
        let targets = [
            Vec4::new(100.0, 100.0, 100.0, 100.0),
            Vec4::new(200.0, 200.0, 100.0, 100.0),
            Vec4::new(300.0, 300.0, 100.0, 100.0),
        ];
        let mut forces = [Vec4::ZERO; 3];
        batch_restoring_forces(&states, &targets, 0.1, &mut forces);
        assert!((forces[0].x - 10.0).abs() < TOL);
        assert!((forces[1].x - 20.0).abs() < TOL);
        assert!((forces[2].x - 30.0).abs() < TOL);
    }
    #[test]
    fn test_batch_boundary_2_elements() {
        let states = [
            Vec4::new(-50.0, 50.0, 100.0, 100.0),
            Vec4::new(50.0, -50.0, 100.0, 100.0),
        ];
        let mut forces = [Vec4::ZERO; 2];
        batch_boundary_forces(&states, 800.0, 600.0, 0.5, &mut forces);
        assert!(forces[0].x > 0.0);
        assert!(forces[1].y > 0.0);
    }
    #[test]
    fn test_batch_integrate_basic() {
        let mut states = [Vec4::new(0.0, 0.0, 100.0, 100.0)];
        let mut velocities = [Vec4::ZERO];
        let forces = [Vec4::new(100.0, 100.0, 0.0, 0.0)];
        batch_integrate(&mut states, &mut velocities, &forces, 0.016, 0.1, 5000.0);
        assert!(states[0].x > 0.0);
        assert!(velocities[0].x > 0.0);
    }
    #[test]
    fn test_batch_integrate_velocity_clamped() {
        let mut states = [Vec4::new(0.0, 0.0, 100.0, 100.0)];
        let mut velocities = [Vec4::new(10000.0, 10000.0, 0.0, 0.0)];
        let forces = [Vec4::new(1000000.0, 1000000.0, 0.0, 0.0)];
        batch_integrate(&mut states, &mut velocities, &forces, 1.0, 0.0, 5000.0);
        assert!(velocities[0].magnitude_xy() <= 5000.0 + TOL);
    }
    #[test]
    fn test_batch_integrate_wh_clamped() {
        let mut states = [Vec4::new(0.0, 0.0, 100.0, 100.0)];
        let mut velocities = [Vec4::new(0.0, 0.0, -500.0, -500.0)];
        let forces = [Vec4::ZERO];
        batch_integrate(&mut states, &mut velocities, &forces, 1.0, 0.0, 5000.0);
        assert!(states[0].w >= 0.0);
        assert!(states[0].h >= 0.0);
    }
    #[test]
    fn test_batch_integrate_damping() {
        let mut states = [Vec4::new(0.0, 0.0, 100.0, 100.0)];
        let mut velocities = [Vec4::new(100.0, 0.0, 0.0, 0.0)];
        let forces = [Vec4::ZERO];
        batch_integrate(&mut states, &mut velocities, &forces, 0.016, 0.5, 5000.0);
        assert!(velocities[0].x < 100.0);
    }
    #[test]
    fn test_batch_integrate_zero_dt() {
        let mut states = [Vec4::new(100.0, 100.0, 50.0, 50.0)];
        let mut velocities = [Vec4::new(100.0, 0.0, 0.0, 0.0)];
        let forces = [Vec4::new(100.0, 0.0, 0.0, 0.0)];
        let old_state = states[0];
        batch_integrate(&mut states, &mut velocities, &forces, 0.0, 0.1, 5000.0);
        assert!((states[0].x - old_state.x).abs() < TOL);
    }
}

#[cfg(test)]
mod elements_tests {
    use super::*;
    use aether_math::Vec4;
    const TOL: f32 = 1e-5;

    #[test]
    fn test_static_box_asymptote() {
        let b = StaticBox::new(30.0, 30.0, 150.0, 200.0, Vec4::new(1.0, 0.0, 0.0, 1.0), 0);
        let a = b.calculate_asymptotes(800.0, 600.0);
        assert!((a.x - 30.0).abs() < TOL);
        assert!((a.y - 30.0).abs() < TOL);
        assert!((a.w - 150.0).abs() < TOL);
        assert!((a.h - 200.0).abs() < TOL);
    }
    #[test]
    fn test_static_box_color() {
        let b = StaticBox::new(0.0, 0.0, 100.0, 100.0, Vec4::new(0.8, 0.2, 0.3, 0.9), 2);
        assert!((b.color().x - 0.8).abs() < TOL);
    }
    #[test]
    fn test_static_box_z() {
        let b = StaticBox::new(0.0, 0.0, 100.0, 100.0, Vec4::new(1.0, 0.0, 0.0, 1.0), 5);
        assert_eq!(b.z_index(), 5);
    }
    #[test]
    fn test_static_box_metadata() {
        let b = StaticBox::new(0.0, 0.0, 100.0, 100.0, Vec4::new(1.0, 0.0, 0.0, 1.0), 3);
        assert!(b.metadata().is_some());
    }

    #[test]
    fn test_smart_panel_5pct() {
        let p = SmartPanel::new(0.05, Vec4::new(0.2, 0.2, 0.3, 0.9), 1);
        let a = p.calculate_asymptotes(800.0, 600.0);
        assert!((a.x - 40.0).abs() < TOL);
        assert!((a.y - 30.0).abs() < TOL);
        assert!((a.w - 720.0).abs() < TOL);
        assert!((a.h - 540.0).abs() < TOL);
    }
    #[test]
    fn test_smart_panel_3pct() {
        let p = SmartPanel::new(0.03, Vec4::new(0.15, 0.15, 0.25, 1.0), 0);
        let a = p.calculate_asymptotes(800.0, 600.0);
        assert!((a.x - 24.0).abs() < TOL);
        assert!((a.w - 752.0).abs() < TOL);
    }
    #[test]
    fn test_smart_panel_10pct() {
        let p = SmartPanel::new(0.1, Vec4::new(0.0, 0.0, 0.0, 1.0), 0);
        let a = p.calculate_asymptotes(1000.0, 800.0);
        assert!((a.x - 100.0).abs() < TOL);
        assert!((a.w - 800.0).abs() < TOL);
    }
    #[test]
    fn test_smart_panel_zero_padding() {
        let p = SmartPanel::new(0.0, Vec4::new(0.0, 0.0, 0.0, 1.0), 0);
        let a = p.calculate_asymptotes(800.0, 600.0);
        assert!((a.x - 0.0).abs() < TOL);
        assert!((a.w - 800.0).abs() < TOL);
    }
    #[test]
    fn test_smart_panel_50pct() {
        let p = SmartPanel::new(0.5, Vec4::new(0.0, 0.0, 0.0, 1.0), 0);
        let a = p.calculate_asymptotes(800.0, 600.0);
        assert!((a.x - 400.0).abs() < TOL);
        assert!((a.w - 0.0).abs() < TOL);
    }
    #[test]
    fn test_smart_panel_responsive() {
        let p = SmartPanel::new(0.05, Vec4::new(0.2, 0.2, 0.3, 0.9), 1);
        let a1 = p.calculate_asymptotes(800.0, 600.0);
        let a2 = p.calculate_asymptotes(1200.0, 900.0);
        assert!((a2.x - 60.0).abs() < TOL);
        assert!((a2.w - 1080.0).abs() < TOL);
    }

    #[test]
    fn test_smart_button_asymptote() {
        let parent = StaticBox::new(100.0, 100.0, 200.0, 100.0, Vec4::new(1.0, 0.0, 0.0, 1.0), 0);
        let btn = SmartButton::new(
            0,
            20.0,
            250.0,
            120.0,
            40.0,
            Vec4::new(0.3, 0.8, 0.3, 1.0),
            3,
        );
        let a = btn.calculate_asymptotes_with_parent(parent.tensor.state);
        assert!((a.x - 120.0).abs() < TOL);
        assert!((a.y - 350.0).abs() < TOL);
        assert!((a.w - 120.0).abs() < TOL);
        assert!((a.h - 40.0).abs() < TOL);
    }
    #[test]
    fn test_smart_button_parent_index() {
        let btn = SmartButton::new(2, 0.0, 0.0, 100.0, 50.0, Vec4::new(1.0, 0.0, 0.0, 1.0), 0);
        assert_eq!(btn.parent_index(), 2);
    }

    #[test]
    fn test_canvas_text_asymptote() {
        let t = CanvasTextNode::new(
            40.0,
            15.0,
            400.0,
            40.0,
            Vec4::new(0.0, 0.0, 0.0, 0.0),
            5,
            "Hello",
            24,
            "Arial",
        );
        let a = t.calculate_asymptotes(800.0, 600.0);
        assert!((a.x - 40.0).abs() < TOL);
        assert!((a.y - 15.0).abs() < TOL);
    }
    #[test]
    fn test_canvas_text_metadata() {
        let t = CanvasTextNode::new(
            0.0,
            0.0,
            100.0,
            50.0,
            Vec4::new(1.0, 1.0, 1.0, 1.0),
            0,
            "Test",
            16,
            "Arial",
        );
        assert!(t.metadata().is_some());
    }

    #[test]
    fn test_flexible_text_asymptote() {
        let t = FlexibleTextNode::new(
            50.0,
            300.0,
            500.0,
            100.0,
            Vec4::new(0.0, 0.0, 0.0, 0.0),
            10,
            "Text",
        );
        let a = t.calculate_asymptotes(800.0, 600.0);
        assert!((a.x - 50.0).abs() < TOL);
    }
    #[test]
    fn test_flexible_text_metadata() {
        let t = FlexibleTextNode::new(
            0.0,
            0.0,
            100.0,
            50.0,
            Vec4::new(0.0, 0.0, 0.0, 0.0),
            0,
            "Test",
        );
        assert!(t.metadata().is_some());
    }

    #[test]
    fn test_static_box_tensor() {
        let mut b = StaticBox::new(10.0, 20.0, 100.0, 50.0, Vec4::new(1.0, 0.0, 0.0, 1.0), 0);
        assert!((b.tensor().state.x - 10.0).abs() < TOL);
        b.tensor_mut().state.x = 99.0;
        assert!((b.tensor().state.x - 99.0).abs() < TOL);
    }
    #[test]
    fn test_smart_panel_tensor() {
        let mut p = SmartPanel::new(0.05, Vec4::new(0.2, 0.2, 0.3, 0.9), 1);
        assert!((p.tensor().state.w - 100.0).abs() < TOL);
        p.tensor_mut().state.w = 200.0;
        assert!((p.tensor().state.w - 200.0).abs() < TOL);
    }
}

#[cfg(test)]
mod input_manager_tests {
    use super::*;
    use aether_math::Vec4;
    const TOL: f32 = 1e-5;

    #[test]
    fn test_new_not_dragging() {
        let im = InputManager::new();
        assert!(!im.is_dragging());
        assert!(im.dragged_element_index().is_none());
    }
    #[test]
    fn test_pointer_down() {
        let mut im = InputManager::new();
        im.pointer_down(0, 100.0, 200.0, 1.0);
        assert!(im.is_dragging());
        assert_eq!(im.dragged_element_index(), Some(0));
    }
    #[test]
    fn test_pointer_move() {
        let mut im = InputManager::new();
        im.pointer_down(0, 100.0, 200.0, 1.0);
        im.pointer_move(110.0, 210.0, 1.016);
        assert!(im.is_dragging());
    }
    #[test]
    fn test_pointer_up() {
        let mut im = InputManager::new();
        im.pointer_down(0, 100.0, 200.0, 1.0);
        im.pointer_up();
        assert!(!im.is_dragging());
        assert!(im.dragged_element_index().is_none());
    }
    #[test]
    fn test_throw_velocity_2point() {
        let mut im = InputManager::new();
        im.pointer_down(0, 100.0, 100.0, 1.0);
        im.pointer_move(110.0, 110.0, 1.016);
        let (vx, vy) = im.get_throw_velocity();
        let expected = 10.0 / 0.016;
        assert!((vx - expected).abs() < TOL * expected);
        assert!((vy - expected).abs() < TOL * expected);
    }
    #[test]
    fn test_throw_velocity_3point() {
        let mut im = InputManager::new();
        im.pointer_down(0, 100.0, 100.0, 1.0);
        im.pointer_move(110.0, 110.0, 1.016);
        im.pointer_move(125.0, 125.0, 1.032);
        let (vx, vy) = im.get_throw_velocity();
        let expected = (3.0 * 125.0 - 4.0 * 110.0 + 100.0) / (2.0 * 0.016);
        assert!((vx - expected).abs() < TOL * expected.abs());
    }
    #[test]
    fn test_throw_velocity_not_enough() {
        let mut im = InputManager::new();
        im.pointer_down(0, 100.0, 100.0, 1.0);
        let (vx, vy) = im.get_throw_velocity();
        assert_eq!(vx, 0.0);
        assert_eq!(vy, 0.0);
    }
    #[test]
    fn test_drag_force() {
        let mut im = InputManager::new();
        im.pointer_down(0, 200.0, 200.0, 1.0);
        let f = im.calculate_drag_force(100.0, 100.0, 100.0, 100.0);
        let expected_fx = (200.0 - 150.0) * 5.0;
        assert!((f.x - expected_fx).abs() < TOL);
    }
    #[test]
    fn test_drag_force_centered() {
        let mut im = InputManager::new();
        im.pointer_down(0, 150.0, 150.0, 1.0);
        let f = im.calculate_drag_force(100.0, 100.0, 100.0, 100.0);
        assert!((f.x - 0.0).abs() < TOL);
    }
    #[test]
    fn test_reset() {
        let mut im = InputManager::new();
        im.pointer_down(0, 100.0, 200.0, 1.0);
        im.reset();
        assert!(!im.is_dragging());
    }
    #[test]
    fn test_history_capped() {
        let mut im = InputManager::new();
        im.pointer_down(0, 0.0, 0.0, 0.0);
        for i in 0..10 {
            im.pointer_move(i as f32, i as f32, i as f64 * 0.016);
        }
    }
    #[test]
    fn test_throw_velocity_zero_dt() {
        let mut im = InputManager::new();
        im.pointer_down(0, 100.0, 100.0, 1.0);
        im.pointer_move(110.0, 110.0, 1.0);
        let (vx, vy) = im.get_throw_velocity();
        assert_eq!(vx, 0.0);
        assert_eq!(vy, 0.0);
    }
}

#[cfg(test)]
mod state_manager_tests {
    use super::*;
    use aether_math::Vec4;
    const TOL: f32 = 1e-5;

    #[test]
    fn test_new() {
        let mut sm = StateManager::new();
        let r = sm.check_teleportation_shock(0.0, 0.0);
        assert!((r - 1.0).abs() < 1e-5);
    }
    #[test]
    fn test_first_call_returns_1() {
        let mut sm = StateManager::new();
        let r = sm.check_teleportation_shock(800.0, 600.0);
        assert!((r - 1.0).abs() < TOL);
    }
    #[test]
    fn test_no_shock() {
        let mut sm = StateManager::new();
        sm.check_teleportation_shock(800.0, 600.0);
        let r = sm.check_teleportation_shock(810.0, 610.0);
        assert!((r - 1.0).abs() < TOL);
    }
    #[test]
    fn test_shock_detected() {
        let mut sm = StateManager::new();
        sm.check_teleportation_shock(800.0, 600.0);
        let r = sm.check_teleportation_shock(1100.0, 600.0);
        assert!((r - 5.0).abs() < TOL);
    }
    #[test]
    fn test_hyper_damping_15_frames() {
        let mut sm = StateManager::new();
        sm.check_teleportation_shock(800.0, 600.0);
        sm.check_teleportation_shock(1200.0, 600.0);
        for _ in 0..14 {
            let r = sm.check_teleportation_shock(1200.0, 600.0);
            assert!((r - 5.0).abs() < TOL);
        }
    }
    #[test]
    fn test_hyper_damping_expires() {
        let mut sm = StateManager::new();
        sm.check_teleportation_shock(800.0, 600.0);
        sm.check_teleportation_shock(1200.0, 600.0);
        for _ in 0..15 {
            sm.check_teleportation_shock(1200.0, 600.0);
        }
        let r = sm.check_teleportation_shock(1200.0, 600.0);
        assert!((r - 1.0).abs() < TOL);
    }
    #[test]
    fn test_lerp_t0() {
        let r = StateManager::lerp(
            Vec4::new(0.0, 0.0, 0.0, 0.0),
            Vec4::new(100.0, 100.0, 100.0, 100.0),
            0.0,
        );
        assert!((r.x - 0.0).abs() < TOL);
    }
    #[test]
    fn test_lerp_t1() {
        let r = StateManager::lerp(
            Vec4::new(0.0, 0.0, 0.0, 0.0),
            Vec4::new(100.0, 100.0, 100.0, 100.0),
            1.0,
        );
        assert!((r.x - 100.0).abs() < TOL);
    }
    #[test]
    fn test_lerp_t01() {
        let r = StateManager::lerp(
            Vec4::new(0.0, 0.0, 0.0, 0.0),
            Vec4::new(100.0, 100.0, 100.0, 100.0),
            0.1,
        );
        assert!((r.x - 10.0).abs() < TOL);
    }
    #[test]
    fn test_shock_negative_delta() {
        let mut sm = StateManager::new();
        sm.check_teleportation_shock(1200.0, 600.0);
        let r = sm.check_teleportation_shock(800.0, 600.0);
        assert!((r - 5.0).abs() < TOL);
    }
}

#[cfg(test)]
mod engine_tests {
    use super::*;
    use aether_math::Vec4;

    #[test]
    fn test_new_empty() {
        let engine = AetherEngine::new();
        assert_eq!(engine.element_count(), 0);
    }
    #[test]
    fn test_tick_empty() {
        let mut engine = AetherEngine::new();
        let data = engine.tick(800.0, 600.0);
        assert!(data.is_empty());
    }
    #[test]
    fn test_register_one_element() {
        let mut engine = AetherEngine::new();
        engine.register_element(Box::new(StaticBox::new(
            0.0,
            0.0,
            100.0,
            100.0,
            Vec4::new(1.0, 0.0, 0.0, 1.0),
            0,
        )));
        assert_eq!(engine.element_count(), 1);
    }
    #[test]
    fn test_tick_one_element() {
        let mut engine = AetherEngine::new();
        engine.register_element(Box::new(StaticBox::new(
            0.0,
            0.0,
            100.0,
            100.0,
            Vec4::new(1.0, 0.0, 0.0, 1.0),
            0,
        )));
        let data = engine.tick(800.0, 600.0);
        assert_eq!(data.len(), 1);
    }
    #[test]
    fn test_tick_8_elements() {
        let mut engine = AetherEngine::new();
        engine.register_element(Box::new(SmartPanel::new(
            0.03,
            Vec4::new(0.15, 0.15, 0.25, 1.0),
            0,
        )));
        engine.register_element(Box::new(CanvasTextNode::new(
            40.0,
            15.0,
            400.0,
            40.0,
            Vec4::new(0.0, 0.0, 0.0, 0.0),
            5,
            "Title",
            24,
            "Arial",
        )));
        engine.register_element(Box::new(SmartPanel::new(
            0.05,
            Vec4::new(0.2, 0.2, 0.3, 0.9),
            1,
        )));
        engine.register_element(Box::new(StaticBox::new(
            30.0,
            30.0,
            150.0,
            200.0,
            Vec4::new(0.8, 0.2, 0.3, 0.9),
            2,
        )));
        engine.register_element(Box::new(StaticBox::new(
            200.0,
            30.0,
            150.0,
            200.0,
            Vec4::new(0.2, 0.6, 0.9, 0.9),
            2,
        )));
        engine.register_element(Box::new(StaticBox::new(
            370.0,
            30.0,
            150.0,
            200.0,
            Vec4::new(0.9, 0.7, 0.2, 0.9),
            2,
        )));
        engine.register_element(Box::new(SmartButton::new(
            2,
            20.0,
            250.0,
            120.0,
            40.0,
            Vec4::new(0.3, 0.8, 0.3, 1.0),
            3,
        )));
        engine.register_element(Box::new(FlexibleTextNode::new(
            50.0,
            300.0,
            500.0,
            100.0,
            Vec4::new(0.0, 0.0, 0.0, 0.0),
            10,
            "Desc",
        )));
        assert_eq!(engine.element_count(), 8);
        let data = engine.tick(800.0, 600.0);
        assert_eq!(data.len(), 8);
    }
    #[test]
    fn test_tick_convergence_60_frames() {
        let mut engine = AetherEngine::new();
        engine.register_element(Box::new(SmartPanel::new(
            0.05,
            Vec4::new(0.2, 0.2, 0.3, 0.9),
            0,
        )));
        for _ in 0..60 {
            engine.tick(800.0, 600.0);
        }
        let data = engine.tick(800.0, 600.0);
        let target_x = 800.0 * 0.05;
        assert!(data[0].rect.x > 0.0);
        assert!(data[0].rect.x < target_x);
    }
    #[test]
    fn test_tick_responsive_resize() {
        let mut engine = AetherEngine::new();
        engine.register_element(Box::new(SmartPanel::new(
            0.05,
            Vec4::new(0.2, 0.2, 0.3, 0.9),
            0,
        )));
        for _ in 0..30 {
            engine.tick(800.0, 600.0);
        }
        let data_before = engine.tick(800.0, 600.0);
        for _ in 0..30 {
            engine.tick(1200.0, 900.0);
        }
        let data = engine.tick(1200.0, 900.0);
        let target_x = 1200.0 * 0.05;
        assert!(data[0].rect.x > data_before[0].rect.x);
        assert!(data[0].rect.x < target_x + 10.0);
    }
    #[test]
    fn test_handle_pointer_down() {
        let mut engine = AetherEngine::new();
        engine.register_element(Box::new(StaticBox::new(
            0.0,
            0.0,
            100.0,
            100.0,
            Vec4::new(1.0, 0.0, 0.0, 1.0),
            0,
        )));
        let result = engine.handle_pointer_down(50.0, 50.0);
        assert!(result.is_some());
    }
    #[test]
    fn test_handle_pointer_down_miss() {
        let mut engine = AetherEngine::new();
        engine.register_element(Box::new(StaticBox::new(
            0.0,
            0.0,
            100.0,
            100.0,
            Vec4::new(1.0, 0.0, 0.0, 1.0),
            0,
        )));
        let result = engine.handle_pointer_down(500.0, 500.0);
        assert!(result.is_none());
    }
    #[test]
    fn test_metadata_non_empty() {
        let mut engine = AetherEngine::new();
        engine.register_element(Box::new(StaticBox::new(
            0.0,
            0.0,
            100.0,
            100.0,
            Vec4::new(1.0, 0.0, 0.0, 1.0),
            0,
        )));
        let meta = engine.get_ui_metadata();
        assert!(!meta.is_empty());
    }
    #[test]
    fn test_batch_path_10_elements() {
        let mut engine = AetherEngine::new();
        for i in 0..10 {
            engine.register_element(Box::new(StaticBox::new(
                i as f32 * 100.0,
                0.0,
                50.0,
                50.0,
                Vec4::new(1.0, 0.0, 0.0, 1.0),
                i as i32,
            )));
        }
        let data = engine.tick(800.0, 600.0);
        assert_eq!(data.len(), 10);
    }
    #[test]
    fn test_multiple_ticks_stable() {
        let mut engine = AetherEngine::new();
        engine.register_element(Box::new(StaticBox::new(
            0.0,
            0.0,
            100.0,
            100.0,
            Vec4::new(1.0, 0.0, 0.0, 1.0),
            0,
        )));
        for _ in 0..100 {
            let data = engine.tick(800.0, 600.0);
            assert_eq!(data.len(), 1);
            assert!(data[0].rect.x.is_finite());
        }
    }
}
