#[cfg(test)]
mod tests {
    #[test]
    fn test_tauri_package_exists() {
        let package_name = env!("CARGO_PKG_NAME");
        assert_eq!(package_name, "aetheris-tauri");
    }

    #[test]
    fn test_tauri_version() {
        let version = env!("CARGO_PKG_VERSION");
        assert_eq!(version, "0.1.0");
    }

    #[test]
    fn test_build_works() {
        // The mere fact that this compiles means the build is healthy
        assert!(true);
    }
}