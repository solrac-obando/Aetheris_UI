"""
Aetheris UI — Release Preparation Script (v1.0.0)

Automates the creation of a clean release_v1/ directory for public distribution.

What gets INCLUDED:
  - core/          (physics engine, solvers, renderers, data bridge)
  - demo/          (odyssey database and master orchestrator)
  - wasm/          (Pyodide bridge and HTML templates)
  - templates/     (Flask/Jinja2 templates including odyssey.html)
  - docs/          (all documentation in EN, ES, PT)
  - scripts/       (this script and future utilities)
  - main.py        (multi-platform entry point)
  - app_server.py  (Flask server for web deployment)
  - pyproject.toml (professional packaging metadata)
  - LICENSE        (MIT License — Carlos Ivan Obando Aure)
  - requirements.txt
  - README.md / README_ES.md / README_PT.md

What gets SHIELDED (excluded from release):
  - tests/         (private quality-control IP)
  - .pytest_cache/ (test artifacts)
  - __pycache__/   (compiled Python)
  - .nbc / .nbi    (Numba cache files)
  - *.pyc          (compiled bytecode)
  - release_v1/    (the release directory itself)
  - .git/          (version control)
  - .venv/         (virtual environment)
  - *.db           (generated databases — recreated by odyssey_db.py)
"""

import os
import shutil
import stat
import sys
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RELEASE_DIR = PROJECT_ROOT / "release_v1"
VERSION = "1.0.0"

# Directories to INCLUDE in the release
INCLUDE_DIRS = [
    "core",
    "demo",
    "wasm",
    "templates",
    "docs",
    "scripts",
]

# Root-level files to INCLUDE
INCLUDE_FILES = [
    "main.py",
    "app_server.py",
    "pyproject.toml",
    "LICENSE",
    "requirements.txt",
    "README.md",
    "README_ES.md",
    "README_PT.md",
    "Dockerfile",
]

# Patterns to EXCLUDE (shielded assets)
EXCLUDE_PATTERNS = [
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".venv",
    "release_v1",
    ".nbc",
    ".nbi",
    ".pyc",
    "tests",
    ".db",
    ".pyo",
    ".egg-info",
]


def should_exclude(path: Path) -> bool:
    """Check if a path should be excluded from the release."""
    name = path.name
    # Check exact name matches
    if name in EXCLUDE_PATTERNS:
        return True
    # Check extension matches
    for pattern in EXCLUDE_PATTERNS:
        if pattern.startswith(".") and name.endswith(pattern):
            return True
    # Check if any parent is excluded
    for parent in path.parents:
        if parent.name in EXCLUDE_PATTERNS:
            return True
    return False


def clean_directory(path: Path):
    """Remove a directory if it exists."""
    if path.exists():
        print(f"  🧹 Cleaning existing {path.name}/")
        shutil.rmtree(path)


def copy_with_exclusions(src: Path, dst: Path):
    """Copy directory tree while respecting exclusion patterns."""
    if should_exclude(src):
        return
    
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return
    
    if src.is_dir():
        for item in src.iterdir():
            copy_with_exclusions(item, dst / item.name)


def create_release():
    """Create the release_v1/ directory with all public assets."""
    print("=" * 60)
    print(f"AETHERIS UI — Release Preparation v{VERSION}")
    print("=" * 60)
    print()
    
    # Step 1: Clean existing release
    print("Step 1: Cleaning existing release directory...")
    clean_directory(RELEASE_DIR)
    print()
    
    # Step 2: Create release directory
    print(f"Step 2: Creating {RELEASE_DIR.name}/")
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    print()
    
    # Step 3: Copy included directories
    print("Step 3: Copying source directories...")
    for dir_name in INCLUDE_DIRS:
        src = PROJECT_ROOT / dir_name
        if src.exists():
            dst = RELEASE_DIR / dir_name
            copy_with_exclusions(src, dst)
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ⚠️  {dir_name}/ not found (skipped)")
    print()
    
    # Step 4: Copy root-level files
    print("Step 4: Copying root-level files...")
    for file_name in INCLUDE_FILES:
        src = PROJECT_ROOT / file_name
        if src.exists():
            dst = RELEASE_DIR / file_name
            shutil.copy2(src, dst)
            print(f"  ✅ {file_name}")
        else:
            print(f"  ⚠️  {file_name} not found (skipped)")
    print()
    
    # Step 5: Shield verification
    print("Step 5: Verifying shielded assets are excluded...")
    shielded = ["tests", ".pytest_cache", "__pycache__", ".git", ".nbc", ".nbi"]
    all_clear = True
    for item in shielded:
        if (RELEASE_DIR / item).exists():
            print(f"  ❌ SHIELD BREACH: {item}/ found in release!")
            all_clear = False
    if all_clear:
        print("  ✅ All private assets properly shielded")
    print()
    
    # Step 6: Generate release manifest
    print("Step 6: Generating release manifest...")
    manifest_path = RELEASE_DIR / "RELEASE_MANIFEST.txt"
    with open(manifest_path, 'w') as f:
        f.write(f"AETHERIS UI RELEASE MANIFEST\n")
        f.write(f"{'=' * 50}\n")
        f.write(f"Version: {VERSION}\n")
        f.write(f"Author: Carlos Ivan Obando Aure\n")
        f.write(f"License: MIT\n")
        f.write(f"Python: >=3.12\n")
        f.write(f"\n")
        f.write(f"INCLUDED:\n")
        for dir_name in INCLUDE_DIRS:
            src = PROJECT_ROOT / dir_name
            if src.exists():
                file_count = sum(1 for _ in src.rglob("*.py") if not should_exclude(_))
                f.write(f"  - {dir_name}/ ({file_count} Python files)\n")
        for file_name in INCLUDE_FILES:
            if (PROJECT_ROOT / file_name).exists():
                f.write(f"  - {file_name}\n")
        f.write(f"\n")
        f.write(f"SHIELDED (not included):\n")
        f.write(f"  - tests/ (private quality-control IP)\n")
        f.write(f"  - .pytest_cache/ (test artifacts)\n")
        f.write(f"  - __pycache__/ (compiled Python)\n")
        f.write(f"  - *.nbc / *.nbi (Numba cache)\n")
        f.write(f"  - *.db (generated databases)\n")
        f.write(f"  - .git/ (version control)\n")
    print(f"  ✅ RELEASE_MANIFEST.txt generated")
    print()
    
    # Step 7: Summary
    total_files = sum(1 for _ in RELEASE_DIR.rglob("*") if _.is_file())
    total_size = sum(f.stat().st_size for f in RELEASE_DIR.rglob("*") if f.is_file())
    size_mb = total_size / (1024 * 1024)
    
    print("=" * 60)
    print(f"RELEASE v{VERSION} READY")
    print(f"{'=' * 60}")
    print(f"  Location: {RELEASE_DIR}")
    print(f"  Files: {total_files}")
    print(f"  Size: {size_mb:.1f} MB")
    print(f"  Shielded: tests/, .pytest_cache/, __pycache__/, *.nbc, *.nbi")
    print()
    print("To verify the release:")
    print(f"  cd {RELEASE_DIR}")
    print("  pip install -r requirements.txt")
    print("  python3 demo/odyssey_db.py")
    print("  python3 main.py --odyssey")
    print("=" * 60)


if __name__ == "__main__":
    create_release()
