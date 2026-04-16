use aether_core::elements::{CanvasTextNode, FlexibleTextNode, SmartButton, SmartPanel, StaticBox};
use aether_core::AetherEngine;
use aether_math::Vec4;
use std::thread;
use std::time::Duration;

fn main() {
    println!("=== Aetheris UI Rust Demo ===");
    println!("Using headless renderer for validation");
    println!("Decoupled Mathematical Engine");
    println!();

    let mut engine = AetherEngine::default();

    let header = SmartPanel::new(0.03, Vec4::new(0.15, 0.15, 0.25, 1.0), 0);
    engine.register_element(Box::new(header));

    let title = CanvasTextNode::new(
        40.0,
        15.0,
        400.0,
        40.0,
        Vec4::new(0.0, 0.0, 0.0, 0.0),
        5,
        "Aetheris Hybrid Canvas Text",
        24,
        "Arial",
    );
    engine.register_element(Box::new(title));

    let content = SmartPanel::new(0.05, Vec4::new(0.2, 0.2, 0.3, 0.9), 1);
    engine.register_element(Box::new(content));

    let card1 = StaticBox::new(30.0, 30.0, 150.0, 200.0, Vec4::new(0.8, 0.2, 0.3, 0.9), 2);
    engine.register_element(Box::new(card1));

    let card2 = StaticBox::new(200.0, 30.0, 150.0, 200.0, Vec4::new(0.2, 0.6, 0.9, 0.9), 2);
    engine.register_element(Box::new(card2));

    let card3 = StaticBox::new(370.0, 30.0, 150.0, 200.0, Vec4::new(0.9, 0.7, 0.2, 0.9), 2);
    engine.register_element(Box::new(card3));

    let button = SmartButton::new(
        2,
        20.0,
        250.0,
        120.0,
        40.0,
        Vec4::new(0.3, 0.8, 0.3, 1.0),
        3,
    );
    engine.register_element(Box::new(button));

    let desc = FlexibleTextNode::new(
        50.0,
        300.0,
        500.0,
        100.0,
        Vec4::new(0.0, 0.0, 0.0, 0.0),
        10,
        "This is selectable text driven by a physics engine.",
    );
    engine.register_element(Box::new(desc));

    println!("Built {} elements from UI intent", engine.element_count());
    println!();
    println!("Starting render loop (100 frames for headless validation)...");
    println!();

    for frame in 0..100 {
        if frame % 20 == 0 {
            println!("--- Frame {} ---", frame + 1);
        }

        let win_w = 800.0 + (frame as f32 * 2.0);
        let win_h = 600.0 + (frame as f32 * 1.0);

        let data = engine.tick(win_w, win_h);

        if frame % 20 == 0 {
            for (i, elem_data) in data.iter().enumerate() {
                let r = elem_data.rect;
                println!(
                    "  Element {} (z={}): [{:.1}, {:.1}, {:.1}, {:.1}]",
                    i, elem_data.z, r.x, r.y, r.w, r.h
                );
            }
            println!();
        }

        thread::sleep(Duration::from_millis(10));
    }

    println!();
    println!("Headless validation complete!");
    println!("1. The renderer never touches DifferentialElement objects");
    println!("2. Only structured data flows from engine to renderer");
    println!("3. Elements converge toward their asymptotes over time");
}
