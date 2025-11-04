#!/usr/bin/env python3
import sys
import os
import subprocess
from pathlib import Path

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def find_venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        candidate = venv_dir / "Scripts" / "python.exe"
    else:
        candidate = venv_dir / "bin" / "python"
    return candidate if candidate.exists() else None

def clear_screen():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

def main():
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)

    venv_dir = script_dir / "keitaiFSextractor" / "virtual_env"
    venv_python = find_venv_python(venv_dir)

    if venv_python is None:
        eprint("A Python virtual environment has not been created. Please run Install_tools.bat (or the equivalent) first.")
        sys.exit(1)

    if len(sys.argv) <= 1:
        print("There are no arguments.")
        print("Usage: extract.py input_file [input_file ...]")
        try:
            input("Press Enter to exit...")
        except KeyboardInterrupt:
            pass
        sys.exit(1)

    clear_screen()

    main_py = script_dir / "keitaiFSextractor" / "main.py"
    if not main_py.exists():
        eprint(f"Could not find {main_py}.")
        sys.exit(1)

    cmd = [str(venv_python), str(main_py)] + sys.argv[1:]
    try:
        res = subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        res = None

    try:
        input("Finished. Press Enter to exit...")
    except KeyboardInterrupt:
        pass

    if res is None:
        sys.exit(1)
    else:
        sys.exit(res.returncode)

if __name__ == "__main__":
    main()