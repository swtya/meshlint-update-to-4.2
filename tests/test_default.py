# SPDX-FileCopyrightText: 2025 Swtya
# SPDX-License-Identifier: GPL-3.0-or-later

"""
This is a test runner file that is called from main.py in the same directory.
In here there are specific regression tests for the Addon / Extension.
main.py has already checked, for the version of Blender this is called headless against, the extension
is already installed and enabled.
"""

import sys
import traceback

import bmesh
import bpy

# Relative imports are taken from the Blender.EXE file location, so add file location to path.
import os
if bpy.context.space_data is None:        # Check if script is opened in Blender program.
    cwd = os.path.dirname(os.path.abspath(__file__))
else:
    cwd = os.path.dirname(bpy.context.space_data.text.filepath)
sys.path.append(cwd)
from utils import *


def test_add_cube() -> None:
    """
    Adds the default cube into the scene. Assert check on the number of vertices.
    :return: None
    """
    bpy.ops.mesh.primitive_cube_add()
    bpy.ops.meshlint.select()
    obj = bpy.context.active_object
    vert_count = count_verts(obj)
    assert vert_count == 8, f"Vert count was, {vert_count}, should have been 8."
    assert count_interior_faces(obj) == 0, f"There was some interior faces."

    delete_active_object()


def main() -> None:
    """
    Main function to collect all the test definition functions above and execute them.
    :return: None
    """
    for name, test in globals().items():
        if name.startswith("test"):
            test()


try:
    main()
    # assert 0      # Uncomment this, during development, to verify that the file did really run to completion.
except:
    panic_save_temp_file(f'tester_crash_{os.path.splitext(os.path.basename(__file__))[0]}.blend')
    traceback.print_exc()
    sys.exit(1)
