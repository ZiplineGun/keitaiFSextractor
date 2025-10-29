from utils import call_tools
import csv
import argparse
import os
import shutil
import re
from datetime import datetime


def main(input_files, model_infos, skip_confirm):
    input_dir = os.path.dirname(input_files[0])
    input_filename = os.path.basename(input_files[0])

    # detect the model infomation
    model_info = detect_model_info(input_files[0], model_infos)

    if model_info is None:
        raise Exception(f"No matching model found.")

    print(f"Detected: {model_info["Phone_Model"]}")

    model_name = read_model_info("Phone_Model", model_info)
    service = read_model_info("Service", model_info)
    ftl = read_model_info("FTL", model_info)
    ftl_parameter = read_model_info("FTL_Parameter", model_info)
    filesystem = read_model_info("File_System", model_info)
    fs_parameter = read_model_info("FS_Parameter", model_info)
    java_path = read_model_info("Java_Path", model_info)
    java_tool = read_model_info("Java_Tool", model_info)
    java_type = read_model_info("Java_Type", model_info)
    storage_type = read_model_info("Storage_Type", model_info)
    chip_name = read_model_info("Chip_Name", model_info)
    media_type = read_model_info("Media_Type", model_info)
                   
    if ftl is None and filesystem is None:
        raise ValueError(f"The FTL and filesystem of this {model_name} are currently under investigation.")
    
    print(f"First input file: {input_filename}")
    if storage_type is not None:
         temp = "⭕️" if storage_type.lower() in os.path.basename(input_filename).lower() else "❌️"
         print(f"Storage_Type: {storage_type} (Included in the filename?: {temp})).")

    if chip_name is not None:
         temp = "⭕️" if chip_name.lower() in os.path.basename(input_filename).lower() else "❌️"
         print(f"Chip_Name: {chip_name} (Included in the filename?: {temp})).")

    if not skip_confirm:
        input("\nIf there are no mistakes, press Enter.")

    # get OOB files
    if os.path.basename(input_filename) == "nand_mixed.bin":
        print("\nSeparating NAND and OOB...")
        out_nand = os.path.join(input_dir, "nand.bin")
        out_oob = os.path.join(input_dir, "nand.oob")
        call_tools.separate_nand_oob(
            input = input_files,
            layout = 0,
            out_nand = out_nand,
            out_oob = out_oob,
        )
        input_files = [out_nand]
        input_oobs = [out_oob]
    else:
        input_oobs = get_oob_paths(input_files)

    print("Input files:", input_files)
    print("Input OOB files:", input_oobs)

    # FTL processing
    if ftl is not None:
        print("=" * 50, "\nRemapping the FTL...")
        print(f"FTL: {ftl}")
        out_ftl_dir = os.path.join(input_dir, "ftl_remapped")
        os.makedirs(out_ftl_dir, exist_ok=True)
        convert_ftl(input_files, input_oobs, ftl, out_ftl_dir, ftl_parameter)
        print("done.")

    # FS processing
    # a three-level folder structure
    # fs_extracted / Folder per FTL output file / Folder per FS partition
    print("=" * 50, "\nExtracting the file system...")
    print(f"File System: {filesystem}")
    out_fs_dir = os.path.join(input_dir, "fs_extracted")
    os.makedirs(out_fs_dir, exist_ok=True)

    if ftl is None:
        convert_fs(
            dump_path=input_files[0],
            oob_path=input_oobs[0],
            fs_type=filesystem,
            fs_parameter=fs_parameter,
            out_dir=os.path.join(out_fs_dir, f"00_{os.path.splitext(input_filename)[0]}"),
            model_name=model_name, storage_type=storage_type,
        )
    else:
        ftlfiles = [entry for entry in os.scandir(out_ftl_dir) if entry.is_file()]
        # The number of FTL files output may become extremely large due to individual files unrelated to FAT, so limit the number of files.
        for e in sorted(ftlfiles, key=lambda e: e.stat().st_size, reverse=True)[:10]:
            f = e.name
            print(f"\n[{f}]")
            convert_fs(
                dump_path=os.path.join(out_ftl_dir, f),
                oob_path=None,
                fs_type=filesystem,
                fs_parameter=fs_parameter,
                out_dir=os.path.join(out_fs_dir, os.path.splitext(f)[0]),
                model_name=model_name, storage_type=storage_type,
            )

    print("done.")

    # collecting processing
    print("=" * 50, "\nCollecting the necessary files...")
    out_collected_dir = os.path.join(input_dir, "collected_files")
    fs_roots = [
        os.path.join(out_fs_dir, second, third)
        for second in os.listdir(out_fs_dir)
        if os.path.isdir(os.path.join(out_fs_dir, second))
        for third in os.listdir(os.path.join(out_fs_dir, second))
        if os.path.isdir(os.path.join(out_fs_dir, second, third))
    ]

    print("Starting the Java folder search...")
    if java_path is None:
        print("Skipped. The java_path is missing from the CSV.")
    else:
        collected_java_dir = os.path.join(out_collected_dir, "java")
        os.makedirs(collected_java_dir, exist_ok=True)

        if java_type == "fs_path":
            for fs_root in fs_roots:
                candidate_path = os.path.join(fs_root, java_path)
                if os.path.isdir(candidate_path):
                    print(f"Found: {candidate_path}")
                    out_java = os.path.join(collected_java_dir, os.path.basename(java_path))
                    shutil.copytree(candidate_path, out_java, dirs_exist_ok=True)
                    break
            else:
                raise ValueError(f"The Java folder could not be obtained, CSV's value: {java_path}")
        else:
            print("Skipped.")
        
        output_java_dir = None
        if java_type == "keitai-tools":
            print("\nUsing keitai-tools to convert Java files for the emulator...")
            call_tools.run_keitai_tools(input=out_java)
            output_java_dir = os.path.join(collected_java_dir, "output")

        if output_java_dir and os.path.isdir(output_java_dir):
            print("\nCompressing for Discord with 7-Zip...")
            out_7z_filename = f"{datetime.now().strftime("%Y%m%d")}_{model_name}_javaout"

            # If the 7z file already exists, 7-Zip throw an error.
            for f in [
                f for f
                in os.listdir(out_collected_dir)
                if (os.path.isfile(os.path.join(out_collected_dir, f))
                    and f.startswith(out_7z_filename))
            ]:
                os.remove(os.path.join(out_collected_dir, f))

            call_tools.run_7zip(
                input=output_java_dir + "/",
                output=os.path.join(out_collected_dir, out_7z_filename)
            )

    print("\nCollecting media files...")
    out_media_dir = os.path.join(out_collected_dir, "media")
    os.makedirs(out_media_dir, exist_ok=True)

    if service in ["FOMA", "mova"]:
        profile = "docomo"
    elif service in ["Softbank_Vodafone", "J-PHONE"]:
        profile = "softbank"
    elif service in ["kddi"]:
        profile = "kddi"
    elif service in ["willcom"]:
        profile = "willcom"
    else:
        raise ValueError(service)

    extract_media(media_type, out_ftl_dir, out_fs_dir, fs_roots, out_media_dir, profile)

    # Duplicate Removal and Renaming of MLD Files
    if os.path.isdir(os.path.join(out_media_dir, "MLD_files")):
        call_tools.run_extract_mld(
            input=os.path.join(out_media_dir, "MLD_files"),
            output=os.path.join(out_media_dir, "temp"),
        )
        shutil.rmtree(os.path.join(out_media_dir, "MLD_files"))
        os.rename(
            os.path.join(out_media_dir, "temp"),
            os.path.join(out_media_dir, "MLD_files")
        )

    print("\nCollecting files which are orphaned from the file system....")
    out_orphan_dir = os.path.join(out_collected_dir, "OrphanFiles")
    for fs_root in fs_roots:
        candidate_path = os.path.join(fs_root, "$OrphanFiles")
        if os.path.isdir(candidate_path):
            shutil.copytree(candidate_path, out_orphan_dir, dirs_exist_ok=True)
    
    print("=" * 50, f"\nProcessing is complete. => {out_collected_dir}")


def read_model_info(key, model_info):
    striped = model_info[key].strip()
    return None if striped in ["", "-"] else striped


def to_ktdumper_modelname(model_name):
    model_name = model_name.replace("μ", "u").replace("+", "p").lower()
    model_name = re.sub(r"ii$", "2", model_name)
    return model_name


# e.g. KTdumper_2025-09-26_08-37-38_p902i_dump_nand
def parse_ktfolder(folder_name):
    parts = folder_name.split("_")
    model = parts[3]
    type = "_".join(parts[4:])
    return model, type


def convert_ftl(input_files, input_oobs, ftl_type, out_dir, ftl_parameter):
    match ftl_type:
        case "SH/D904i FTL":
            if input_oobs[0] is None: raise FileNotFoundError("OOB file is missing.")
            
            call_tools.remap_sh_d904i(
                in_nand=input_files[0],
                in_oob=input_oobs[0],
                output=os.path.join(out_dir, "remapped.bin"),
            )
        case "B4B4 FTL":
            if input_oobs[0] is None: raise FileNotFoundError("OOB file is missing.")
            
            call_tools.remap_b4b4(
                in_nand=input_files[0],
                in_oob=input_oobs[0],
                output=out_dir,
            )
        case "Fugue NAND":
            if input_oobs[0] is None: raise FileNotFoundError("OOB file is missing.")

            call_tools.remap_fugue(
                in_nand=input_files[0],
                in_oob=input_oobs[0],
                output=os.path.join(out_dir, "remapped.bin"),
            )
        case "Fugue NAND (A+B)":
            pass
        case "SSR200":
            if input_oobs[0] is None: raise FileNotFoundError("OOB file is missing.")

            call_tools.remap_ssr200(
                in_nand=input_files[0],
                in_oob=input_oobs[0],
                output=os.path.join(out_dir, "remapped.bin"),
            )
        case "SSR200 (old flavor)":
            if input_oobs[0] is None: raise FileNotFoundError("OOB file is missing.")
            
            call_tools.remap_old_ssr200(
                in_nand=input_files[0],
                in_oob=input_oobs[0],
                output=os.path.join(out_dir, "remapped.bin"),
            )
        case "XSR1":
            call_tools.remap_xsr1(
                in_nand=input_files[0],
                output=os.path.join(out_dir, "remapped.bin"),
            )
        case "XSR2":
            if input_oobs[0] is None: raise FileNotFoundError("OOB file is missing.")
            
            call_tools.remap_xsr2(
                in_nand=input_files[0],
                in_oob=input_oobs[0],
                output=out_dir,
            )
        case "XSR3":
            raise NotImplementedError("This tool is still a work in progress.")
        case "FSR_F":
            if input_oobs[0] is None: raise FileNotFoundError("OOB file is missing.")
            if ftl_parameter is None: raise ValueError("partition parameter is missing.")
            
            print("This process will take about 5 minutes...")
            call_tools.remap_fsr_f(
                partition=ftl_parameter,
                in_nand=input_files[0],
                in_oob=input_oobs[0],
                output=os.path.join(out_dir, "remapped.bin"),
            )
        case "FSR_ll":
            if input_oobs[0] is None: raise FileNotFoundError("OOB file is missing.")
            
            print("This process will take about 10 minutes...")
            call_tools.remap_fsr_ll(
                in_nand=input_files[0],
                in_oob=input_oobs[0],
                output=os.path.join(out_dir, "remapped.bin"),
            )
        case "F900i FTL":
            raise NotImplementedError("This tool is still a work in progress.")
        case "FlashFX 3.00 NOR":
            pass
        case "00F0F0 Structure":
            call_tools.remap_f0(
                in_nand=input_files[0],
                output=out_dir,
                ftl_parameter=ftl_parameter,
            )
        case "SH900i FTL":
            call_tools.remap_sh900i(
                in_nand=input_files[0],
                output=out_dir,
                ftl_parameter=ftl_parameter,
            )
        case _:
            raise NotImplementedError(f"Unsupported FTL: {ftl_type}")
        

def convert_fs(dump_path, oob_path, fs_type, fs_parameter, out_dir, model_name, storage_type):
    match fs_type:
        case "FAT" | "FAT12"| "FAT16" | "FAT32" | "Samsung RFS" | "KFAT":
            call_tools.extract_fat(
                input=dump_path,
                output=out_dir
            )
        case "Customized FAT16":
            temp_dir = os.path.join(out_dir, "temp")
            os.makedirs(temp_dir, exist_ok=True)
            call_tools.carve_fat(
                input=dump_path,
                output=temp_dir
            )

            standard_fats = []
            for i, f in enumerate(sorted([e.path for e in os.scandir(temp_dir) if e.is_file()])):
                out_conv = os.path.join(out_dir, f"{i:02}_converted_fat.img")
                call_tools.convert_customized_fat16(
                    input=f,
                    output=out_conv,
                )
                standard_fats.append(out_conv)
                os.remove(f)

            for f in standard_fats:
                extdir = os.path.join(out_dir, os.path.splitext(os.path.basename(f))[0] + "_extracted")
                os.makedirs(extdir, exist_ok=True)

                # Extract it to a temp folder and then move it to delete the top folder.
                call_tools.extract_fat(f, temp_dir)
                for e in os.scandir(temp_dir):
                    for e2 in os.scandir(e.path):
                        shutil.move(e2.path, extdir)
                    shutil.rmtree(e.path)
            
            shutil.rmtree(temp_dir)
        case "JFFS2":
            print("Processing may take several minutes...")
            os.makedirs(out_dir, exist_ok=True)
            carved_jffs2_dir = os.path.join(out_dir, "00_JFFS2_extracted")
            call_tools.extract_jffs2(
                input=dump_path,
                output=carved_jffs2_dir,
            )
        case "YAFFS2":
            call_tools.extract_yaffs2(
                in_nand=dump_path,
                in_oob=oob_path,
                output=out_dir,
                model_name=model_name,
                storage_type=storage_type,
            )
        case "EXT3":
            if fs_parameter is None: raise ValueError("The FS Parameter is not defined")

            offsets = [int(par.strip(), 16) for par in fs_parameter.split(", ")]
            for i, offset in enumerate(offsets):
                ext_outdir = os.path.join(out_dir, f"{i:02}_EXT3_0x{offset:09X}_extracted")
                call_tools.extract_ext3(
                    input=dump_path,
                    output=ext_outdir,
                    offset=offset,
                )
        case "Qualcomm EFS2":
            pass
        #case "Intel FHS (CG2)":
            #pass
        #case "SH902i Structure":
            #pass
        #case "DATA Structure":
            #pass
        #case "Sony Ericsson Custom FS":
            #pass
        #case "ext3":
            #pass
        case "N/A":
            print("no FTL")
        case _:
            raise NotImplementedError(f"Unsupport filesystem: {fs_type}")
        

def extract_media(media_type, out_ftl_dir, out_fs_dir, fs_roots, out_media_dir, profile):
    match media_type:
        case "fs_extension":
            call_tools.run_scan_and_extract_by_extension(
                input=out_fs_dir,
                output=out_media_dir,
                profile=profile,
            )
        case "ftl_no_extension":
            call_tools.run_scan_and_extract_by_extension(
                input=out_ftl_dir,
                output=out_media_dir,
                profile=profile,
                scan_only_magics=True,
            )
        case "fs_sh900i":
            for fs_root in fs_roots:
                call_tools.run_scan_and_extract_sh900i_media(
                    input=fs_root,
                    output=out_media_dir,
                )
        case _:
            raise NotImplementedError(f"Unsupport media_type: {media_type}")


def detect_model_info(input_file, model_infos):
    def is_drive_root(path):
        return os.path.isdir(path) and (len(path) == 3 if os.name == 'nt' else path == '/')
    
    path = input_file
    model = None

    while True:
        if model is not None or is_drive_root(path):
            break

        name_len = 0
        for model_info in model_infos:
            name = to_ktdumper_modelname(model_info["Phone_Model"].strip())
            if name in os.path.basename(path).lower() and len(name) > name_len:
                model = model_info
                name_len = len(name)

        path = os.path.dirname(input_file)
    return model


def get_oob_paths(input_files):
    oob_paths = []

    for input_file in input_files:
        input_dir = os.path.dirname(input_file)
        input_name = os.path.basename(input_file)

        candidates = [os.path.join(input_dir, f"{os.path.splitext(input_name)[0]}.oob")]
        if "_" in input_name: candidates.append(os.path.join(input_dir, f"{input_name.split("_")[-1]}_oob.bin"))
        
        for candidate in candidates:
            if os.path.isfile(candidate):
                oob_paths.append(candidate)
                break
        else:
            oob_paths.append(None)
    
    return oob_paths



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input-file", nargs="+", dest="input_file")
    parser.add_argument("skip-confirm", action="store_true")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(base_dir, "models.csv"), encoding="utf8") as inf:
        model_infos = tuple(csv.DictReader(inf))

    main(args.input_file, model_infos, args.skip_confirm)






