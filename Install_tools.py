import sys
import os
import subprocess
import shutil
from pathlib import Path

MIN_PYTHON_MAJOR = 3
MIN_PYTHON_MINOR = 10


INSTALL_PACKAGES = [
    # for fs-tools
    ["Qiling==1.4.6", "unicorn==2.0.1.post1"],
    # for keitai-tools
    ["requests", "scsu"],
    # for dumpefs2
    ["reedsolo", "construct", "crcmod"],
    # for jefferson
    ["click==8.1.7", "colorama==0.4.6", "cstruct==6.1", "lzallright==0.2.6"],
]

def check_python_version():
    v = sys.version_info
    if (v.major, v.minor) < (MIN_PYTHON_MAJOR, MIN_PYTHON_MINOR):
        print(f"Warning: running Python {v.major}.{v.minor}. Recommended >= {MIN_PYTHON_MAJOR}.{MIN_PYTHON_MINOR}.")
    else:
        print(f"Using Python {v.major}.{v.minor} (OK).")

def run(cmd, **kwargs):
    print(" ".join(map(str, cmd)))
    return subprocess.run(cmd, check=False, **kwargs)

def ensure_venv(venv_path: Path):
    if venv_path.exists():
        print(f"virtual environment already exists at: {venv_path}")
        return True

    print("Creating a virtual environment for Python...")
    try:
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
    except subprocess.CalledProcessError as e:
        print("Failed to create virtual environment:", e)
        return False
    return True

def venv_executables(venv_path: Path):
    if os.name == "nt":
        py = venv_path / "Scripts" / "python.exe"
        pip = venv_path / "Scripts" / "pip.exe"
    else:
        py = venv_path / "bin" / "python"
        pip = venv_path / "bin" / "pip"
    return py, pip

def pip_install(pip_path: Path, packages, quiet=False):
    cmd = [str(pip_path), "install"] + packages
    if quiet:
        # Adding `-q` to pip will reduce the display.
        cmd.insert(2, "-q")
    res = run(cmd)
    if res.returncode != 0:
        print(f"pip install failed for: {packages} (return code {res.returncode})")
        return False
    return True

def main():
    check_python_version()

    script_dir = Path(__file__).resolve().parent
    base = script_dir / "keitaiFSextractor"
    tools_dir = base / "tools"

    if not tools_dir.exists():
        print("The keitaiFSextractor folder that should be present is missing, so the process has terminated.")
        print(f"Expected directory: {tools_dir}")
        sys.exit(1)

    os.chdir(base)
    print(f"Changed working directory to {base}")

    venv_path = base / "virtual_env"
    if not ensure_venv(venv_path):
        print("Could not create virtual environment. Exiting.")
        sys.exit(1)

    python_in_venv, pip_in_venv = venv_executables(venv_path)
    if not python_in_venv.exists():
        print(f"Virtualenv python not found at {python_in_venv}. Trying fallback to sys.executable.")
        python_in_venv = Path(sys.executable)
    if not pip_in_venv.exists():
        print(f"pip not found in venv at {pip_in_venv}. Attempting to use `python -m pip` in venv instead.")
        pip_in_venv = None

    # pip
    print("Installing Python packages...")

    # helper to run pip via python -m pip if pip executable missing
    def install_with_fallback(pkgs):
        if pip_in_venv and pip_in_venv.exists():
            return pip_install(pip_in_venv, pkgs)
        else:
            # use venv python -m pip
            cmd = [str(python_in_venv), "-m", "pip", "install"] + pkgs
            res = run(cmd)
            if res.returncode != 0:
                print(f"pip install (via python -m pip) failed for: {pkgs}")
                return False
            return True
        
    for pkgs in INSTALL_PACKAGES:
        install_with_fallback(pkgs)

    # download_tools.py
    dl_script = base / "download_tools.py"
    if dl_script.exists():
        print("Downloading the necessary tools...")
        try:
            res = run([str(python_in_venv), str(dl_script)])
            if res.returncode != 0:
                print(f"download_tools.py exited with code {res.returncode}")
        except Exception as e:
            print("Failed to run download_tools.py:", e)
    else:
        print("download_tools.py not found; skipping download step.")

    # copy tools/extract_fat.ini -> tools/TSK-FAT-AutoRecover/
    src = base / "tools" / "extract_fat.ini"
    dest_dir = base / "tools" / "TSK-FAT-AutoRecover"
    if src.exists():
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_file = dest_dir / src.name
            shutil.copy2(src, dest_file)
            print(f"Copied {src} -> {dest_file}")
        except Exception as e:
            print("Failed to copy extract_fat.ini:", e)
    else:
        print(f"Source INI not found: {src} (skipping copy)")

    # pause
    try:
        input("Finished. Press Enter to exit...")
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")

if __name__ == "__main__":
    main()
