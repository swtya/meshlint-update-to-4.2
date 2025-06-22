# SPDX-FileCopyrightText: 2025 Swtya
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Welcome to the Mesh Lint regression test suite.
This tool will run a range of tests on the MeshLint using multiple versions of Blender.
    Warning: If there is a parsing error in the test_xxxx.py file then Blender does not return an error which
             results in this test runner saying that it passes!
    How to run this:
        From the terminal / cmd prompt call main() with the system installed python.
        e.g. @AMD5600g:~/github-git/meshlint-update-to-4.2/tests$ python3 main.py
        From within PyCharm the main.py can simply be "Run".
    Output should look like this:
        BEGIN
        blender-4.2.0-linux-x64 check_installed PASSED
        blender-4.2.0-linux-x64 test_default PASSED
          etc.
        END
"""

import subprocess
from pathlib import Path

TEST_VERSIONS = {
    "4.2.0",
    "4.3.2",
    "4.4.0",
    "4.5.0",
}

# Color codes
RED = "\033[91m"
GREEN = "\033[92m"
INVERSE = "\033[7m"
RESET = "\033[0m"

def main(app_location_path) -> None:
    """
    :param app_location_path: optional path to find installed versions of blender on the system.
    :return: None, just a print output to the terminal.
    """

    if app_location_path:
        app_location = Path(app_location_path)
    elif Path().home().joinpath('Blender_apps').is_dir():
        app_location = Path().home().joinpath('Blender_apps')
    else:
        app_location = Path().home()
    # print(app_location)

    ## Build an array of the directories which contain Blender that are included in the set we want to test with.
    blender_apps = []
    for entry in app_location.iterdir():
        if entry.is_dir() and entry.name.startswith("blender") and entry.name.split("-")[1] in TEST_VERSIONS:
            blender_apps.append(entry)
    # print(blender_apps)

    ## Find the test files to run, allows for expansible set.
    tests = []
    for entry in Path(__file__).parent.iterdir():
        if entry.is_file() and entry.suffix == ".py" and entry.name.startswith("test"):
            tests.append(entry)
    print(tests)

    print(INVERSE + "BEGIN" + RESET)

    ## Call headless Blender versions, checking for Addon installation before calling tests.
    for blender in blender_apps:
        check_install = Path(__file__).with_name('check_installed.py')
        cmd = [blender / "blender", "-b", "-P", check_install]
        proc = subprocess.run(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE, text = True)
        # print(proc.stdout)      # Debug printing
        if proc.returncode:
            print(f"{RED + blender.name} {check_install.stem} {INVERSE}FAILED{RESET}")
            # print(proc.stderr.decode().strip())
            print(proc.stderr)
            continue   # skip the rest of the for loop for this Blender version
        else:
            print(f"{blender.name} {check_install.stem} {GREEN + INVERSE}PASSED{RESET}")

        for test in tests:
            #cmd = [blender / "blender.exe", "-b", "-P", test]      # Windows ?
            cmd = [blender / "blender", "-b", "-P", test]           # Works on Linux for extracted tar.xz.
            proc = subprocess.run(cmd, capture_output=True)
            # print(proc.stdout)  # Debug printing
            if proc.returncode:
                print(f"{RED + blender.name} {test.stem} {INVERSE}FAILED{RESET}")
                print(proc.stderr.decode().strip())
                continue    # Continue statement so it runs all test files
            else:
                print(f"{blender.name} {test.stem} {GREEN + INVERSE}PASSED{RESET}")

    print(INVERSE + "END" + RESET)


print(f"Welcome to the test runner.")
print(f"Please enter the path to your Blender installs or press return to accept the default.")
#main(input())      # Allow user to specify a path to folder of their Blender applications.
main([])            # Straight run from file run in PyCharm.
