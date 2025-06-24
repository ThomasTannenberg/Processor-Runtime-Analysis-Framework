import subprocess
import os
import sys
import shutil
from pathlib import Path

# =========================
#   P-RAF: Build Manager
#   (Developer Utility)
# =========================

# --- Configuration ---
# This script determines the project's root directory by going up one level 
# from its own location ('tools/').
ROOT_DIR = Path(__file__).parent.parent.resolve()
JAVA_PROJECT_DIR = ROOT_DIR / 'java_benchmark'
RUST_PROJECT_DIR = ROOT_DIR / 'rust_benchmark'

def check_command_exists(command, purpose, install_url):
    """Checks if a command is available on the system's PATH."""
    if not shutil.which(command):
        print(f"❌ ERROR: Command '{command}' not found.")
        print(f"   Please ensure {purpose} is installed and its 'bin' directory is in your system's PATH.")
        print(f"   Installation guide: {install_url}")
        return False
    print(f"✅ Found '{command}'...")
    return True

def run_build_command(command, working_directory):
    """Runs a build command in a specified directory and captures output."""
    print(f"\n▶️  Running command: `{' '.join(command)}` in `{working_directory}`...")
    try:
        # Use shell=True for Windows compatibility with .cmd files like mvn.cmd
        # Use check=True to automatically raise an exception if the command fails
        # THE FIX: By removing capture_output, all build logs will stream to the console in real-time.
        process = subprocess.run(
            command,
            cwd=working_directory,
            check=True,
            shell=True,
            text=True
        )
        print(f"   └── ✅ Success!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   └── ❌ FAILURE: The command returned an error.")
        # Output will now be visible directly, but we can still log it for clarity.
        print(f"   └── STDOUT:\n{e.stdout}")
        print(f"   └── STDERR:\n{e.stderr}")
        return False
    except FileNotFoundError:
        print(f"   └── ❌ FAILURE: Could not find the command '{command[0]}'.")
        return False
    except Exception as e:
        print(f"   └── ❌ FAILURE: An unexpected error occurred: {e}")
        return False

def build_java_project():
    """Builds the Java Maven project."""
    print("\n--- Building Java Worker ---")
    if not JAVA_PROJECT_DIR.is_dir():
        print(f"ERROR: Java project directory not found at: {JAVA_PROJECT_DIR}")
        return False
    return run_build_command(['mvn', 'clean', 'package'], working_directory=JAVA_PROJECT_DIR)

def build_rust_project():
    """Builds the Rust Cargo project in release mode for maximum performance."""
    print("\n--- Building Rust Worker ---")
    if not RUST_PROJECT_DIR.is_dir():
        print(f"ERROR: Rust project directory not found at: {RUST_PROJECT_DIR}")
        return False
    return run_build_command(['cargo', 'build', '--release'], working_directory=RUST_PROJECT_DIR)

def main():
    """Main function to orchestrate the build process."""
    print("=============================================")
    print(" P-RAF: Build Manager for Compiled Workers")
    print("=============================================")

    # 1. Verify that the necessary build tools are installed
    print("\n--- Checking Prerequisites ---")
    mvn_ok = check_command_exists('mvn', 'Java (Maven)', 'https://maven.apache.org/install.html')
    cargo_ok = check_command_exists('cargo', 'Rust (Cargo)', 'https://www.rust-lang.org/tools/install')

    if not (mvn_ok and cargo_ok):
        sys.exit(1) # Exit if tools are missing

    # 2. Run the build commands
    java_build_success = build_java_project()
    rust_build_success = build_rust_project()

    # 3. Print a final summary
    print("\n--------------------")
    print("   Build Summary")
    print("--------------------")
    print(f"Java Build:   {'✅ SUCCESS' if java_build_success else '❌ FAILED'}")
    print(f"Rust Build:   {'✅ SUCCESS' if rust_build_success else '❌ FAILED'}")
    print("--------------------")

    if not (java_build_success and rust_build_success):
        print("\nOne or more builds failed. Please review the output above.")
        sys.exit(1)
    
    print("\nAll compiled workers built successfully!")

if __name__ == "__main__":
    main()