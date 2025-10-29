import os
import subprocess
import shutil

BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools")

def run(exe_path, commands, stdout=None, stderr=None, cwd=None, print_command=True):
    if print_command: print(" ".join(commands))
    if os.path.isfile(exe_path):
        subprocess.run(
            commands,
            stdout=stdout,
            stderr=stderr,
            check=True,
            cwd=cwd
        )
    else:
        raise FileNotFoundError(f"Not Found {exe_path}")

def run_module(commands, stdout=None, stderr=None, cwd=None):
    print(" ".join(commands))
    subprocess.run(
        commands,
        stdout=stdout,
        stderr=stderr,
        check=True,
        cwd=cwd
    )


def separate_nand_oob(input, layout, out_nand, out_oob):
    exe_path = os.path.join(BASE_PATH, "k", "separate_nand_oob.py")
    commands = [
        "python",
        exe_path,
        input,
        "--layout", str(layout),
        "--output_nand", out_nand,
        "--output_oob", out_oob,
    ]
    run(exe_path, commands, subprocess.DEVNULL)


def run_keitai_tools(input):
    exe_path = os.path.join(BASE_PATH, "keitai-tools", "kttools.py")
    commands = [
        "python",
        exe_path,
        input,
    ]
    run(exe_path, commands)


def run_7zip(input, output, fullsize_7z):
    exe_path = os.path.join(BASE_PATH, "7-Zip", "7z.exe")
    commands = [
        exe_path,
        "a",
        "-t7z",  # 7z
        "-mx=9", # compression level
    ]
    if not fullsize_7z:
        commands.append("-v10m") # Split Compression (MB)

    commands += [output, input]
    run(exe_path, commands, stdout=subprocess.DEVNULL)


def run_scan_and_extract_by_extension(input, output, profile, scan_only_magics=None, search_window=0x1000):
    exe_path = os.path.join(BASE_PATH, "k", "scan_and_extract_by_extension.py")
    commands = [
        "python",
        exe_path,
        "--extract",
        "--profile", profile,
        "--search-window", str(search_window),
        input,
        output,
    ]
    if scan_only_magics is not None:
        commands.append("--scan-only-magics")
    run(exe_path, commands)


def run_scan_and_extract_sh900i_media(input, output):
    exe_path = os.path.join(BASE_PATH, "k", "scan_and_extract_sh900i_media.py")
    commands = [
        "python",
        exe_path,
        input,
        output,
    ]
    run(exe_path, commands, stdout=subprocess.DEVNULL)


def run_extract_mld(input, output):
    exe_path = os.path.join(BASE_PATH, "mld-tools", "extract_mld.py")
    commands = [
        "python",
        exe_path,
        input,
        "--out_dir", output,
    ]
    run(exe_path, commands, stdout=subprocess.DEVNULL, print_command=False)


def remap_xsr1(in_nand, output):
    exe_path = os.path.join(BASE_PATH, "rfs_dumper", "rfs_dumper_xsr1app.exe")
    commands = [
        exe_path,
        in_nand,
        output,
    ]
    run(exe_path, commands)


def remap_xsr2(in_nand, in_oob, output):
    exe_path = os.path.join(BASE_PATH, "various-keitai-assemble", "assemble_xsr2.py")
    commands = [
        "python",
        exe_path,
        in_nand,
        "--input-oob", in_oob,
        output,
    ]
    run(exe_path, commands)


def remap_fsr_f(in_nand, in_oob, partition, output):
    exe_path = os.path.join(BASE_PATH, "fs-tools", "fsr_f", "emu.py")
    commands = [
        "python",
        exe_path,
        partition,
        in_nand,
        in_oob,
        output,
    ]
    run(exe_path, commands)


def remap_fsr_ll(in_nand, in_oob, output):
    exe_path = os.path.join(BASE_PATH, "fs-tools", "fsr_ll", "emu.py")
    commands = [
        "python",
        exe_path,
        in_nand,
        in_oob,
        output,
    ]
    run(exe_path, commands)


def remap_b4b4(in_nand, in_oob, output):
    exe_path = os.path.join(BASE_PATH, "b4-ftl-extract", "extract.py")
    commands = [
        "python",
        exe_path,
        in_nand,
        output,
        "--mix-spare",
        "--input-oob", in_oob,
    ]
    run(exe_path, commands)


def remap_sh_d904i(in_nand, in_oob, output):
    exe_path = os.path.join(BASE_PATH, "various-keitai-assemble", "assemble_sh704i_d904i.py")
    commands = [
        "python",
        exe_path,
        in_nand,
        output,
        "--input-oob", in_oob,
    ]
    run(exe_path, commands)


def remap_fugue(in_nands, in_oobs, output, ftl_parameter=None):
    exe_path = os.path.join(BASE_PATH, "fugue-tools", "extract.py")
    common_command = [
        "python",
        exe_path,
    ]
    for in_nand in in_nands:
        if ftl_parameter is not None:
            in_nand += ftl_parameter
        common_command.append(in_nand)

    for in_oob in in_oobs:
        common_command.append(in_oob)

    common_command.append(output)

    try:
        run(exe_path, common_command + ["--autocorrect"])
    except subprocess.CalledProcessError:
        print("Processing failed. Retrying with the ignore option enabled.")
        run(exe_path, common_command + ["--ignore"])


def remap_ssr200(in_nand, in_oob, output):
    exe_path = os.path.join(BASE_PATH, "fs-tools", "ssr200", "convert_ssr200.py")
    commands = [
        "python",
        exe_path,
        in_nand,
        in_oob,
        output,
    ]
    run(exe_path, commands)


def remap_old_ssr200(in_nand, in_oob, output):
    exe_path = os.path.join(BASE_PATH, "fs-tools", "ssr200_old_flavor", "convert_old_ssr200.py")
    commands = [
        "python",
        exe_path,
        in_nand,
        in_oob,
        output,
    ]
    run(exe_path, commands)
    

def remap_f0(in_nand, output, ftl_parameter):
    exe_path = os.path.join(BASE_PATH, "various-keitai-assemble", "assemble_f0.py")
    commands = [
        "python",
        exe_path,
        in_nand,
        output,
        "--undelete",
    ]
    if ftl_parameter is not None:
        commands += ftl_parameter.split(" ")
    run(exe_path, commands)


def remap_sh900i(in_nand, output, ftl_parameter=None):
    exe_path = os.path.join(BASE_PATH, "various-keitai-assemble", "assemble_sh900i.py")
    commands = [
        "python",
        exe_path,
        in_nand,
        output,
    ]
    if ftl_parameter is not None:
        commands += ftl_parameter.split(" ")
    run(exe_path, commands)


def extract_fat(input, output):
    exe_path = os.path.join(BASE_PATH, "TSK-FAT-AutoRecover", "extract_fat.py")
    commands = [
        "python",
        exe_path,
        input,
        "--output", output,
    ]
    run(exe_path, commands)


def extract_ext3(input, output, offset):
    exe_path = os.path.join(BASE_PATH, "sleuthkit", "bin", "tsk_recover.exe")
    commands = [
        exe_path,
        "-e",
        "-f", "ext3",
        "-o", str(offset // 0x200),
        input,
        output,
    ]
    run(exe_path, commands)


def extract_jffs2(input, output):
    cwd = os.path.join(BASE_PATH, "jefferson")
    commands = [
        "python",
        "-m", "jefferson.cli",
        "--dest", output,
        "--force",
        input,
    ]
    run_module(commands, cwd=cwd)


def extract_yaffs2(in_nand, in_oob, output, config_name):
    exe_path = os.path.join(BASE_PATH, "yaffs-tools", "extract.py")
    config_path = os.path.join(BASE_PATH, "yaffs-tools", "config", config_name)

    if not os.path.isfile(config_path): 
        raise FileNotFoundError(f"The YAFFS2 tool configuration file does not exist: {config_path}")

    commands = [
        "python",
        exe_path,
        in_nand,
        output,
        config_path,
        "--input-oob", in_oob, 
        "--mix-spare", "--no-show-deleted", "--no-show-missing",
        "--try-undelete",
    ]
    try:
        shutil.rmtree(output, ignore_errors=True)
        run(exe_path, commands)
    except subprocess.CalledProcessError:
        print("Processing failed. Retrying with the recovery option disabled.")
        shutil.rmtree(output, ignore_errors=True)
        commands2 = [
            "python",
            exe_path,
            in_nand,
            output,
            config_path,
            "--input-oob", in_oob, 
            "--mix-spare", "--no-show-deleted", "--no-show-missing",
        ]
        run(exe_path, commands2)
    

def extract_sh902i(in_nors, output):
    exe_path = os.path.join(BASE_PATH, "various-keitai-assemble", "assemble_sh902i.py")
    commands = [
        "python",
        exe_path,
        "--ignore"
    ]

    for in_nor in in_nors:
        commands.append(in_nor)
    commands.append(output)

    run(exe_path, commands)

def carve_fat(input, output):
    exe_path = os.path.join(BASE_PATH, "TSK-FAT-AutoRecover", "extract_fat.py")
    commands = [
        "python",
        exe_path,
        input,
        "--carve-fat",
        "--no-extract-fat",
        "--output", output,
    ]
    run(exe_path, commands, stdout=subprocess.DEVNULL, print_command=False)


def convert_customized_fat16(input, output):
    exe_path = os.path.join(BASE_PATH, "fs-tools", "ssr200", "convert_fat.py")
    commands = [
        "python",
        exe_path,
        input,
        output,
    ]
    run(exe_path, commands)
