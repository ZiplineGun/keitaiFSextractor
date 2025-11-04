import utils.download as download
from pathlib import Path
import shutil
import subprocess
import os

TOOL_REPOSITORIES = [
    {
        "toolname": "fugue-tools",
        "repo_owner": "irdkwia",
        "ref": "main",
    },
    {
        "toolname": "yaffs-tools",
        "repo_owner": "irdkwia",
        "ref": "main",
    },
    {
        "toolname": "various-keitai-assemble",
        "repo_owner": "irdkwia",
        "ref": "main",
    },
    {
        "toolname": "b4-ftl-extract",
        "repo_owner": "irdkwia",
        "ref": "main",
    },
    {
        "toolname": "flash-ftl",
        "repo_owner": "irdkwia",
        "ref": "main",
    },
    {
        "toolname": "c5a3-assemble",
        "repo_owner": "irdkwia",
        "ref": "main",
    },
    {
        "toolname": "w-series-extract-fs",
        "repo_owner": "irdkwia",
        "ref": "main",
    },
    {
        "toolname": "fs-tools",
        "repo_owner": "ZiplineGun",
        "ref": "main",
    },
    {
        "toolname": "TSK-FAT-AutoRecover",
        "repo_owner": "ZiplineGun",
        "ref": "main",
    },
    {
        "toolname": "k",
        "repo_owner": "ZiplineGun",
        "ref": "main",
    },
    {
        "toolname": "jefferson",
        "repo_owner": "ZiplineGun",
        "ref": "master",
    },
    {
        "toolname": "xsr3_reconstruct",
        "repo_owner": "bkerler",
        "ref": "main",
    },
    {
        "toolname": "dumpefs2",
        "repo_owner": "Crawlerop",
        "ref": "main",
    },
    {
        "toolname": "keitai-tools",
        "repo_owner": "memory-hunter",
        "ref": "main",
    },
    {
        "toolname": "mld-tools",
        "repo_owner": "kagekiyo7",
        "ref": "main",
    },
]

if os.name == "posix":
    TOOL_REPOSITORIES.append(
        {
            "toolname": "keitai_fs_tools",
            "repo_owner": "usernameak",
            "ref": "master",
        },
    )

if __name__ == "__main__":
    root = Path(__file__).resolve().parent / "tools"

    if not root.is_dir():
        raise FileNotFoundError("The tools folder that should be there is missing.")

    if os.name == "nt":
        # sleuthkit
        output_dir = root / "sleuthkit"
        res = download.download_latest_github_release(
            repo_owner="sleuthkit",
            repo_name="sleuthkit",
            asset_pattern=r"sleuthkit-.*-win32\.zip$",
            output_folder=str(output_dir),
            enable_extract_zip=True,
            force=False,
        )
        print(f"SleuthKit result: {res}")
        print("=" * 40)

        # rfs_dumper
        output_dir = root / "rfs_dumper"
        res = download.download_latest_github_release(
            repo_owner="usernameak",
            repo_name="keitai_fs_tools",
            asset_pattern=r"rfs_dumper_xsr1app\.exe$",
            output_folder=str(output_dir),
            enable_extract_zip=False,
            force=False,
        )
        print(f"rfs_dumper result: {res}")
        print("=" * 40)

        # toshiba_remap
        output_dir = root / "toshiba_remap"
        res = download.download_latest_github_release(
            repo_owner="usernameak",
            repo_name="keitai_fs_tools",
            asset_pattern=r"toshiba_remap\.exe$",
            output_folder=str(output_dir),
            enable_extract_zip=False,
            force=False,
        )
        print(f"toshiba_remap result: {res}")
        print("=" * 40)


    def download_github_helper(toolname, repo_owner, ref="main"):
        output_dir = root / toolname
        res = download.download_latest_repo_snapshot(
            repo_owner=repo_owner,
            repo_name=toolname,
            output_folder=str(output_dir),
            enable_extract_zip=True,
            ref=ref
        )
        print(f"{toolname} result: {res}")
        print("=" * 40)

    for repository in TOOL_REPOSITORIES:
        tool_path = root / repository["toolname"]
        print(f"[{tool_path.name}]")
        if shutil.which("git"):
            if (tool_path).is_dir():
                commands = ["git", "reset", "--hard"]
                print(" ".join(commands))
                subprocess.run(commands, check=True, cwd=tool_path)

                commands2 = ["git", "pull"]
                print(" ".join(commands2))
                subprocess.run(commands2, check=True, cwd=tool_path)
                print("=" * 40)
            else:
                commands = ["git", "clone", fr"https://github.com/{repository['repo_owner']}/{repository['toolname']}.git"]
                print(" ".join(commands))
                subprocess.run(commands, check=True, cwd=root)
                print("=" * 40)
        else:
            print(
                "Git is not found in PATH, using GitHub API. "
                "Errors may occur if the API rate limit is reached."
            )
            download_github_helper(toolname=repository["toolname"], repo_owner=repository["repo_owner"], ref=repository["ref"])

    # compile
    if os.name == "posix":
        commands = ["dub", "build", "--force"]
        subprocess.run(commands, check=True, cwd=os.path.join(root, "keitai_fs_tools", "xsr1"))
        

