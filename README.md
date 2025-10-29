# keitaiFSextractor
Thanks: [@irdkwia](https://github.com/irdkwia), [@xyzz](https://github.com/xyzz), [@usernameak](https://github.com/usernameak), [@memory-hunter](https://github.com/memory-hunter), [@bkerler](https://github.com/bkerler), [@Crawlerop](https://github.com/Crawlerop), authors of other tools, and the keitaiwiki community
## Environment
- Windows only.
- Python must be installed and available in your PATH.
  - Minimum (likely): Python 3.10
- If Git is not available in the environment, various tools will be downloaded via the GitHub API (But the GitHub API has a rate limit per hour.).

## Installation
Downloads the required external tools. Python packages are installed inside a virtual environment:
- `Install_tools.bat`

To update the tools (Downloads only updated tools; skips unchanged ones.):
- `Update_tools.bat`

## Usage
For NAND dumps, the OOB file is automatically detected (matching FILENAME.oob or FILENAME_oob.bin).
- `Extract.bat dump.bin`

When multiple dumps are required (e.g., Fugue (A+B) FTL):
- `Extract.bat dump1.bin dump2.bin`

## Behavior / Specification
- Detects the phone model from the filename or directory name with the ktdumper style normalization:
  - lowercase, `μ` → `u`, `+` → `p`, `ii` → `2`
- Reads per-model settings from a CSV and runs extraction accordingly.
  - models.csv is generated from my spreadsheet.


## Bundled Software

### 7-Zip
This tool uses 7-Zip for file compression.

* Copyright: 1999-2025 Igor Pavlov
* License: 7-Zip is free software. Most of the code is licensed under the GNU LGPL. Some parts of the code
  are licensed under the BSD 3-clause License. Also, there is an unRAR license restriction for some parts of
  the code. For more details, please see the 7-Zip/License.txt file.
* Website: https://www.7-zip.org/ (https://www.7-zip.org/)


Users of this tool must also comply with the 7-Zip license terms. For details, please refer to the bundled
[7-Zip/License.txt](keitaiFSextractor/tools/7-Zip/License.txt) and [7-Zip/readme.txt](keitaiFSextractor/tools/7-Zip/readme.txt) files.
