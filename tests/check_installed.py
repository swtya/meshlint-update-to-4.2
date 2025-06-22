# SPDX-FileCopyrightText: 2025 Swtya
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Called by main.py to check if the extension is available for the version of Blender.
"""

import sys
import traceback

import addon_utils
import bmesh
import bpy

EXTENSION_NAME = "MeshLint"     # Case matters
MIN_VERSION = (0,1,2)


def test_loaded() -> None:
    """
    A corrupted py file would still appear with a version but not be in the loaded state.
    When all is well addon_utils.check('bl_ext.blender_org.MeshLint') should return (True, True).
    :return: None
    """
    for ext_id in addon_utils.modules().mapping:
        if ext_id.split(".")[-1] == EXTENSION_NAME:
            (loaded_default, loaded_state) = addon_utils.check(ext_id)
            assert loaded_default, f"Extension {EXTENSION_NAME} not loaded by default."
            assert loaded_state, f"Extension {EXTENSION_NAME} not currently loaded."
            break       # Once the extension has been found we can stop looking.


def test_version() -> None:
    """
    Checks the version number of the extension.
    :return: None
    """
    prefs = bpy.context.preferences
    used_ext = {ext.module for ext in prefs.addons}
    addons = [(mod, addon_utils.module_bl_info(mod))
              for mod in addon_utils.modules(refresh=False)]
    for mod, info in addons:
        modname = mod.__name__
        if modname in used_ext:
            if modname.split(".")[-1] == EXTENSION_NAME:
                version = info['version'] if info['version'] else (0,0,0)
                # print(modname, version)
                # Version must be >= 0.1.0 otherwise it's too old
                assert (version[0] > MIN_VERSION[0] or
                        (version[0]==MIN_VERSION[0] and version[1]>MIN_VERSION[1]) or
                        (version[0]==MIN_VERSION[0] and version[1]==MIN_VERSION[1] and version[2]>=MIN_VERSION[2])),\
                    f"Extension Version too old, {version}. Minimum is {MIN_VERSION}."


def main() -> None:
    """
    Checks to see if the extension is listed as an addon.
    If a match is found then further tests are conducted for the version and loading status.
    :return:
    """
    for ext_id in addon_utils.modules().mapping:
        if ext_id.split(".")[-1] == EXTENSION_NAME:
            assert addon_utils.check_extension(ext_id)
            #print("Found the extension")
            break
    else:
        assert False, f"No Extension with the name {EXTENSION_NAME} was found."

    for name, test in globals().items():
        if name.startswith("test"):
            test()


try:
    main()
except:
    traceback.print_exc()
    sys.exit(1)
