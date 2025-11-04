import os
import subprocess
import shutil
from functools import lru_cache

BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools")
VENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "virtual_env")


def get_python_from_venv(venv_path):
    if os.name == "nt":
        return os.path.join(venv_path, "Scripts", "python.exe")
    else:
        return os.path.join(venv_path, "bin", "python")


@lru_cache(maxsize=1)
def _get_cached_venv_python(venv_path):
    if venv_path is None:
        venv_path = VENV_PATH
    
    python_path = get_python_from_venv(venv_path)
    if os.path.isfile(python_path):
        return python_path
    
    return None


def run(commands, stdout=None, stderr=None, cwd=None, print_command=True):
    if print_command: print(" ".join(commands))
    subprocess.run(
        commands,
        stdout=stdout,
        stderr=stderr,
        check=True,
        cwd=cwd
    )


def run_python(py_path, commands, stdout=None, stderr=None, cwd=None, print_command=True):
    venv_python = _get_cached_venv_python(VENV_PATH)
    if venv_python is None:
        raise FileNotFoundError("Virtualenv python not found. Create virtual_env")

    _commands = [venv_python] + commands
    if os.path.isfile(py_path):
        run(_commands, stdout, stderr, cwd, print_command)
    else:
        raise FileNotFoundError(f"Not Found {py_path}")
    

def run_exe(exe_path, commands, stdout=None, stderr=None, cwd=None, print_command=True):
    if not os.path.isfile(exe_path):
        raise FileNotFoundError(f"{exe_path} does not exist.")

    _commands = [exe_path] + commands
    run(_commands, stdout, stderr, cwd, print_command)


def run_module(commands, stdout=None, stderr=None, cwd=None, print_command=True):
    run(commands, stdout, stderr, cwd, print_command)


def run_linux_package(pkg, commands, stdout=None, stderr=None, cwd=None, print_command=True):
    if os.name == "nt":
        raise Exception("os not linux")
    
    if not shutil.which(pkg):
        print(f"{pkg} is not installed.")

    _commands = [pkg] + commands

    run(_commands, stdout, stderr, cwd, print_command)


def separate_nand_oob(input, layout, out_nand, out_oob):
    py_path = os.path.join(BASE_PATH, "k", "separate_nand_oob.py")
    commands = [
        py_path,
        input,
        "--layout", str(layout),
        "--output_nand", out_nand,
        "--output_oob", out_oob,
    ]
    run_python(py_path, commands, subprocess.DEVNULL)


def run_keitai_tools(input):
    py_path = os.path.join(BASE_PATH, "keitai-tools", "kttools.py")
    commands = [
        py_path,
        input,
    ]
    run_python(py_path, commands)


def run_7zip(input, output, fullsize_7z):
    commands = [
        "a",
        "-t7z",  # 7z
        "-mx=9", # compression level
    ]
    if not fullsize_7z:
        commands.append("-v10m") # Split Compression (MB)

    commands += [output, input]
    if os.name == "nt":
        exe_path = os.path.join(BASE_PATH, "7-Zip", "7z.exe")
        run_exe(exe_path, commands, stdout=subprocess.DEVNULL)
    else:
        run_linux_package("7z", commands, stdout=subprocess.DEVNULL)


def run_scan_and_extract_by_extension(input, output, profile, scan_only_magics=None, search_window=0x1000):
    py_path = os.path.join(BASE_PATH, "k", "scan_and_extract_by_extension.py")
    commands = [
        py_path,
        "--extract",
        "--profile", profile,
        "--search-window", str(search_window),
        input,
        output,
    ]
    if scan_only_magics is not None:
        commands.append("--scan-only-magics")
    run_python(py_path, commands)


def run_scan_and_extract_sh900i_media(input, output):
    py_path = os.path.join(BASE_PATH, "k", "scan_and_extract_sh900i_media.py")
    commands = [
        py_path,
        input,
        output,
    ]
    run_python(py_path, commands, stdout=subprocess.DEVNULL)


def run_extract_mld(input, output):
    py_path = os.path.join(BASE_PATH, "mld-tools", "extract_mld.py")
    commands = [
        py_path,
        input,
        "--out_dir", output,
    ]
    run_python(py_path, commands, stdout=subprocess.DEVNULL, print_command=False)


def remap_xsr1(in_nand, output):
    commands = [
        in_nand,
        output,
    ]

    if os.name == "nt":
        exe_path = os.path.join(BASE_PATH, "rfs_dumper", "rfs_dumper_xsr1app.exe")
    else:
        exe_path = os.path.join(BASE_PATH, "keitai_fs_tools", "xsr1", "xsr1app", "rfs_dumper_xsr1app")

    run_exe(exe_path, commands)


def remap_xsr2(in_nand, in_oob, output):
    py_path = os.path.join(BASE_PATH, "various-keitai-assemble", "assemble_xsr2.py")
    commands = [
        py_path,
        in_nand,
        "--input-oob", in_oob,
        output,
    ]
    run_python(py_path, commands)


def remap_fsr_f(in_nand, in_oob, partition, output):
    py_path = os.path.join(BASE_PATH, "fs-tools", "fsr_f", "emu.py")
    commands = [
        py_path,
        partition,
        in_nand,
        in_oob,
        output,
    ]
    run_python(py_path, commands)


def remap_fsr_ll(in_nand, in_oob, output):
    py_path = os.path.join(BASE_PATH, "fs-tools", "fsr_ll", "emu.py")
    commands = [
        py_path,
        in_nand,
        in_oob,
        output,
    ]
    run_python(py_path, commands)


def remap_b4b4(in_nand, in_oob, output):
    py_path = os.path.join(BASE_PATH, "b4-ftl-extract", "extract.py")
    commands = [
        py_path,
        in_nand,
        output,
        "--mix-spare",
        "--input-oob", in_oob,
    ]
    run_python(py_path, commands)


def remap_sh_d904i(in_nand, in_oob, output):
    py_path = os.path.join(BASE_PATH, "various-keitai-assemble", "assemble_sh704i_d904i.py")
    commands = [
        py_path,
        in_nand,
        output,
        "--input-oob", in_oob,
    ]
    run_python(py_path, commands)


def remap_fugue(in_nands, in_oobs, output, ftl_parameter=None):
    py_path = os.path.join(BASE_PATH, "fugue-tools", "extract.py")
    common_command = [
        py_path,
    ]
    for in_nand in in_nands:
        if ftl_parameter is not None:
            in_nand += ftl_parameter
        common_command.append(in_nand)

    for in_oob in in_oobs:
        common_command.append(in_oob)

    common_command.append(output)

    try:
        run_python(py_path, common_command + ["--autocorrect"])
    except subprocess.CalledProcessError:
        print("Processing failed. Retrying with the ignore option enabled.")
        run_python(py_path, common_command + ["--ignore"])


def remap_ssr200(in_nand, in_oob, output):
    py_path = os.path.join(BASE_PATH, "fs-tools", "ssr200", "convert_ssr200.py")
    commands = [
        py_path,
        in_nand,
        in_oob,
        output,
    ]
    run_python(py_path, commands)


def remap_old_ssr200(in_nand, in_oob, output):
    py_path = os.path.join(BASE_PATH, "fs-tools", "ssr200_old_flavor", "convert_old_ssr200.py")
    commands = [
        py_path,
        in_nand,
        in_oob,
        output,
    ]
    run_python(py_path, commands)
    

def remap_f0(in_nand, output, ftl_parameter):
    py_path = os.path.join(BASE_PATH, "various-keitai-assemble", "assemble_f0.py")
    commands = [
        py_path,
        in_nand,
        output,
        "--undelete",
    ]
    if ftl_parameter is not None:
        commands += ftl_parameter.split(" ")
    run_python(py_path, commands)


def remap_sh900i(in_nand, output, ftl_parameter=None):
    py_path = os.path.join(BASE_PATH, "various-keitai-assemble", "assemble_sh900i.py")
    commands = [
        py_path,
        in_nand,
        output,
    ]
    if ftl_parameter is not None:
        commands += ftl_parameter.split(" ")
    run_python(py_path, commands)


def extract_fat(input, output):
    py_path = os.path.join(BASE_PATH, "TSK-FAT-AutoRecover", "extract_fat.py")
    commands = [
        py_path,
        input,
        "--output", output,
    ]
    run_python(py_path, commands)


def extract_ext3(input, output, offset):
    commands = [
        "-e",
        "-f", "ext3",
        "-o", str(offset // 0x200),
        input,
        output,
    ]

    if os.name == "nt":
        exe_path = os.path.join(BASE_PATH, "sleuthkit", "bin", "tsk_recover.exe")
        run_exe(exe_path, commands)
    else:
        run_linux_package("tsk_recover", commands)


def extract_jffs2(input, output):
    cwd = os.path.join(BASE_PATH, "jefferson")
    commands = [
        "-m", "jefferson.cli",
        "--dest", output,
        "--force",
        input,
    ]
    run_module(commands, cwd=cwd)


def extract_yaffs2(in_nand, in_oob, output, config_name):
    py_path = os.path.join(BASE_PATH, "yaffs-tools", "extract.py")
    config_path = os.path.join(BASE_PATH, "yaffs-tools", "config", config_name)

    if not os.path.isfile(config_path): 
        raise FileNotFoundError(f"The YAFFS2 tool configuration file does not exist: {config_path}")

    commands = [
        py_path,
        in_nand,
        output,
        config_path,
        "--input-oob", in_oob, 
        "--mix-spare", "--no-show-deleted", "--no-show-missing",
        "--try-undelete",
    ]
    try:
        shutil.rmtree(output, ignore_errors=True)
        run_python(py_path, commands)
    except subprocess.CalledProcessError:
        print("Processing failed. Retrying with the recovery option disabled.")
        shutil.rmtree(output, ignore_errors=True)
        commands2 = [
            py_path,
            in_nand,
            output,
            config_path,
            "--input-oob", in_oob, 
            "--mix-spare", "--no-show-deleted", "--no-show-missing",
        ]
        run_python(py_path, commands2)
    

def extract_sh902i(in_nors, output):
    py_path = os.path.join(BASE_PATH, "various-keitai-assemble", "assemble_sh902i.py")
    commands = [
        py_path,
        "--ignore"
    ]

    for in_nor in in_nors:
        commands.append(in_nor)
    commands.append(output)

    run_python(py_path, commands)


def carve_fat(input, output):
    py_path = os.path.join(BASE_PATH, "TSK-FAT-AutoRecover", "extract_fat.py")
    commands = [
        py_path,
        input,
        "--carve-fat",
        "--no-extract-fat",
        "--output", output,
    ]
    run_python(py_path, commands, stdout=subprocess.DEVNULL, print_command=False)


def convert_customized_fat16(input, output):
    py_path = os.path.join(BASE_PATH, "fs-tools", "ssr200", "convert_fat.py")
    commands = [
        py_path,
        input,
        output,
    ]
    run_python(py_path, commands)
