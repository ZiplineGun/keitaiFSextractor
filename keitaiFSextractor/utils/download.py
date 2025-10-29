# -*- coding: utf-8 -*-
"""
GitHub downloader utilities.

Contains:
- download_latest_github_release(...) : download a release asset (keeps manifest per output folder)
- download_latest_repo_snapshot(...) : check latest commit for a ref and download zipball if commit changed

Both functions share helpers for manifest handling, download/extract, and use GITHUB_TOKEN if present.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import os
import requests
import tempfile
import shutil
import zipfile
import json
import hashlib
import re

MANIFEST_FILENAME = "manifest.json"


# ----------------------
# Shared helper helpers
# ----------------------
def _compute_sha256(path: Path) -> str:
    """Compute SHA256 hex digest for a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_manifest(output_folder: Path) -> Optional[Dict[str, Any]]:
    """Load manifest.json from output_folder if present and valid, otherwise return None."""
    mf = output_folder / MANIFEST_FILENAME
    if not mf.exists():
        return None
    try:
        with mf.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        # treat corrupt manifest as absent
        return None


def _save_manifest(output_folder: Path, data: Dict[str, Any]):
    """Write manifest.json (pretty-printed) into output_folder (creates folder if needed)."""
    output_folder.mkdir(parents=True, exist_ok=True)
    mf = output_folder / MANIFEST_FILENAME
    with mf.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def download_file(url: str, out_path: Path, session: requests.Session):
    """
    Download file to out_path (atomic via .part file). Raises on HTTP errors.
    """
    tmp = out_path.with_suffix(out_path.suffix + ".part")
    with session.get(url, stream=True) as r:
        r.raise_for_status()
        tmp.parent.mkdir(parents=True, exist_ok=True)
        with tmp.open("wb") as fh:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    fh.write(chunk)
    tmp.replace(out_path)  # atomic-ish rename
    return out_path


def extract_zip(zip_path: Path, output_folder: Path, remove_zip: bool = True, flatten_single_top_level: bool = True):
    """
    Extract zip to output_folder using a temp dir; if zip contains a single top-level directory
    and flatten_single_top_level is True, move that directory's contents into output_folder.

    Existing files/dirs in output_folder with the same names are removed/replaced.
    """
    if not zipfile.is_zipfile(zip_path):
        raise Exception("File is not a valid ZIP archive")

    temp_dir = Path(tempfile.mkdtemp(prefix="extract_zip_"))
    try:
        with zipfile.ZipFile(str(zip_path), "r") as z:
            z.extractall(temp_dir)

        entries = [e for e in os.listdir(temp_dir) if e not in ("__MACOSX",) and not e.startswith(".DS_Store")]

        if flatten_single_top_level and len(entries) == 1:
            single = entries[0]
            single_path = temp_dir / single
            source_root = single_path if single_path.exists() else temp_dir
        else:
            source_root = temp_dir

        # ensure output folder exists
        output_folder.mkdir(parents=True, exist_ok=True)

        # Move each item, replacing existing
        for name in os.listdir(source_root):
            s = Path(source_root) / name
            d = output_folder / name

            if d.exists():
                if d.is_dir() and not d.is_symlink():
                    shutil.rmtree(d)
                else:
                    d.unlink()
            shutil.move(str(s), str(d))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    if remove_zip:
        try:
            zip_path.unlink()
        except OSError:
            pass

    return output_folder


def _get_github_session():
    """Return a requests.Session configured with optional GITHUB_TOKEN and a User-Agent."""
    s = requests.Session()
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        s.headers.update({"Authorization": f"token {token}"})
    s.headers.update({"User-Agent": "manifest-downloader/1.0"})
    return s


# ----------------------------------------
# Existing function: release asset download
# (left unchanged in behavior; shared helpers used)
# ----------------------------------------
def download_latest_github_release(
    repo_owner: str,
    repo_name: str,
    asset_pattern: str,
    output_folder: str,
    enable_extract_zip: bool = False,
    force: bool = False,
) -> Path:
    """
    Download the latest GitHub release asset matching asset_pattern and save/extract it into output_folder.

    Behavior:
    - A manifest.json is stored in output_folder describing the downloaded release (tag, asset, sha256, etc).
    - If manifest's release_tag matches the latest tag and force is False, the function will skip download.
    - If enable_extract_zip is True and the asset is a .zip, it will be extracted into output_folder.
    """
    output_folder = Path(output_folder)
    manifest = _load_manifest(output_folder)

    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
    session = _get_github_session()

    print(f"Querying GitHub releases for {repo_owner}/{repo_name}...")
    resp = session.get(api_url)
    resp.raise_for_status()
    release_data = resp.json()

    tag_name = release_data.get("tag_name") or release_data.get("name") or ""
    release_id = release_data.get("id")

    # find matching asset
    matched_asset = None
    for asset in release_data.get("assets", []):
        if re.search(asset_pattern, asset.get("name", "")):
            matched_asset = asset
            break

    if not matched_asset:
        raise Exception(f"No asset matching pattern '{asset_pattern}' found in latest release.")

    asset_name = matched_asset["name"]
    asset_id = matched_asset.get("id")
    asset_size = matched_asset.get("size")

    print(f"Latest release tag: {tag_name}, asset: {asset_name}")

    # decide whether to skip based on manifest (tag comparison)
    if not force and manifest:
        old_tag = manifest.get("release_tag")
        old_asset_name = manifest.get("asset_name")
        if old_tag and old_tag == tag_name:
            # Tag hasn't changed -> skip
            print(f"Skipping download: release tag unchanged ({tag_name}).")
            if enable_extract_zip:
                return output_folder
            else:
                local_file = output_folder / asset_name
                if local_file.exists():
                    return local_file
                return output_folder

    # Proceed to download
    download_url = matched_asset.get("browser_download_url")
    if not download_url:
        raise Exception("No browser_download_url for matched asset.")

    downloads_dir = output_folder / ".downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    dest_file = downloads_dir / asset_name

    print(f"Downloading asset to {dest_file} ...")
    download_file(download_url, dest_file, session)
    print("Download completed. Computing checksum...")

    sha256 = _compute_sha256(dest_file)
    print(f"SHA256: {sha256}")

    # Extract if requested
    if enable_extract_zip and dest_file.suffix.lower() == ".zip":
        print("Extracting zip...")
        extract_zip(dest_file, output_folder, remove_zip=True, flatten_single_top_level=True)
        final_path = output_folder
    else:
        output_folder.mkdir(parents=True, exist_ok=True)
        final_path = output_folder / asset_name
        if final_path.exists():
            final_path.unlink()
        shutil.move(str(dest_file), str(final_path))
        try:
            if not any(downloads_dir.iterdir()):
                downloads_dir.rmdir()
        except Exception:
            pass
        print(f"Saved asset to {final_path}")

    # Update manifest
    manifest_data = {
        "repo": f"{repo_owner}/{repo_name}",
        "release_tag": tag_name,
        "release_id": release_id,
        "asset_name": asset_name,
        "asset_id": asset_id,
        "size": asset_size,
        "sha256": sha256,
        "downloaded_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "extracted_to": str(output_folder) if enable_extract_zip else None,
        "source_type": "release_asset",
    }
    _save_manifest(output_folder, manifest_data)
    print(f"Manifest written to {output_folder / MANIFEST_FILENAME}")

    return final_path


# ----------------------------------------
# New function: repo snapshot (zipball) based on latest commit
# ----------------------------------------
def download_latest_repo_snapshot(
    repo_owner: str,
    repo_name: str,
    ref: str = "master",
    output_folder: str = "./output",
    enable_extract_zip: bool = True,
    force: bool = False,
    archive_format: str = "zip",  # currently only 'zip' supported
) -> Path:
    """
    Check the latest commit SHA for repo_owner/repo_name at `ref` (branch/tag/commit-ish).
    If the commit SHA differs from the recorded manifest (or force=True), download the repository
    zipball for that ref and extract (or save) into output_folder.

    The manifest records commit_sha so subsequent runs can skip when unchanged.
    """
    if archive_format.lower() != "zip":
        raise NotImplementedError("Currently only 'zip' archive_format is supported")

    output_folder = Path(output_folder)
    manifest = _load_manifest(output_folder)
    session = _get_github_session()

    # 1) Query latest commit for given ref
    commit_api = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{ref}"
    print(f"Querying latest commit for {repo_owner}/{repo_name}@{ref} ...")
    r = session.get(commit_api)
    r.raise_for_status()
    commit_data = r.json()
    commit_sha = commit_data.get("sha")
    commit_date = None
    try:
        commit_date = commit_data.get("commit", {}).get("committer", {}).get("date")
    except Exception:
        commit_date = None

    if not commit_sha:
        raise Exception("Could not determine latest commit SHA for the specified ref.")

    print(f"Latest commit SHA: {commit_sha}")

    # 2) decide whether to skip based on manifest
    if not force and manifest:
        old_commit = manifest.get("commit_sha")
        old_ref = manifest.get("ref")
        if old_commit and old_commit == commit_sha:
            print(f"Skipping download: commit unchanged ({commit_sha}).")
            if enable_extract_zip:
                return output_folder
            else:
                archive_name = manifest.get("archive_name")
                if archive_name:
                    local_file = output_folder / archive_name
                    if local_file.exists():
                        return local_file
                return output_folder

    # 3) download zipball for the ref
    # API endpoint: https://api.github.com/repos/{owner}/{repo}/zipball/{ref}
    archive_api = f"https://api.github.com/repos/{repo_owner}/{repo_name}/zipball/{ref}"
    downloads_dir = output_folder / ".downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)

    short_sha = commit_sha[:8]
    # sanitize ref for filename
    safe_ref = re.sub(r"[^\w\.-]", "_", ref)
    archive_name = f"{repo_name}-{safe_ref}-{short_sha}.zip"
    dest_file = downloads_dir / archive_name

    print(f"Downloading archive for commit {commit_sha} to {dest_file} ...")
    download_file(archive_api, dest_file, session)
    print("Download finished. Computing SHA256...")
    sha256 = _compute_sha256(dest_file)
    size = dest_file.stat().st_size
    print(f"SHA256: {sha256}  size: {size} bytes")

    # 4) extract or store archive
    if enable_extract_zip:
        print("Extracting archive...")
        extract_zip(dest_file, output_folder, remove_zip=True, flatten_single_top_level=True)
        final_path = output_folder
        print(f"Extraction completed into {final_path}")
    else:
        output_folder.mkdir(parents=True, exist_ok=True)
        final_path = output_folder / archive_name
        if final_path.exists():
            final_path.unlink()
        shutil.move(str(dest_file), str(final_path))
        try:
            if not any(downloads_dir.iterdir()):
                downloads_dir.rmdir()
        except Exception:
            pass
        print(f"Saved archive to {final_path}")

    # 5) write manifest
    manifest_data = {
        "repo": f"{repo_owner}/{repo_name}",
        "ref": ref,
        "commit_sha": commit_sha,
        "commit_date": commit_date,
        "archive_name": archive_name,
        "archive_size": size,
        "archive_sha256": sha256,
        "downloaded_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "extracted_to": str(output_folder) if enable_extract_zip else None,
        "source_type": "zipball",
    }
    _save_manifest(output_folder, manifest_data)
    print(f"Manifest written to {output_folder / MANIFEST_FILENAME}")

    return final_path


# ----------------------------------------
# Simple CLI/demo when run as script
# ----------------------------------------
if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent

    if not os.path.isdir(root / "tools"):
        raise FileNotFoundError("The tools folder that should be there is missing.")

    # sleuthkit
    output_dir = root / "tools" / "sleuthkit"
    res = download_latest_github_release(
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
    output_dir = root / "tools" / "rfs_dumper"
    res = download_latest_github_release(
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
    output_dir = root / "tools" / "toshiba_remap"
    res = download_latest_github_release(
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
        output_dir = root / "tools" / toolname
        res = download_latest_repo_snapshot(
            repo_owner=repo_owner,
            repo_name=toolname,
            output_folder=str(output_dir),
            enable_extract_zip=True,
            ref=ref
        )
        print(f"{toolname} result: {res}")
        print("=" * 40)

    if not shutil.which("git"):
        download_github_helper(toolname="various-keitai-assemble", repo_owner="irdkwia")
        download_github_helper(toolname="fugue-tools", repo_owner="irdkwia")
        download_github_helper(toolname="yaffs-tools", repo_owner="irdkwia")
        download_github_helper(toolname="b4-ftl-extract", repo_owner="irdkwia")
        download_github_helper(toolname="flash-ftl", repo_owner="irdkwia")
        download_github_helper(toolname="c5a3-assemble", repo_owner="irdkwia")
        download_github_helper(toolname="w-series-extract-fs", repo_owner="irdkwia")
        download_github_helper(toolname="fs-tools", repo_owner="ZiplineGun", ref="master")
        download_github_helper(toolname="TSK-FAT-AutoRecover", repo_owner="ZiplineGun")
        download_github_helper(toolname="k", repo_owner="ZiplineGun")
        download_github_helper(toolname="jefferson", repo_owner="ZiplineGun", ref="master")
        download_github_helper(toolname="xsr3_reconstruct", repo_owner="bkerler")
        download_github_helper(toolname="dumpefs2", repo_owner="Crawlerop")
        download_github_helper(toolname="keitai-tools", repo_owner="memory-hunter")
        download_github_helper(toolname="mld-tools", repo_owner="kagekiyo7")

