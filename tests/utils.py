# SPDX-FileCopyrightText: 2025 Swtya
# SPDX-License-Identifier: GPL-3.0-or-later

"""
This file that is called from test_xxxx.py in the same directory.
In here are a collection of utilities called common to several tests functions
part of the Addon / Extension testing framework.
"""

import bmesh
import bpy


def delete_active_object() -> None:
    """
    Deletes ths active object after switching to object mode.
    :return: None
    """
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.delete()


def count_interior_faces(obj):
    """
    :param obj: The object to test for interior faces.
    :return: The number of interior faces
    """
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_interior_faces()
    b = bmesh.from_edit_mesh(obj.data)
    # selected_verts = [vert for vert in b.verts if vert.select]
    # selected_edges = [edge for edge in b.edges if edge.select]
    selected_faces = [face for face in b.faces if face.select]
    return len(selected_faces)


def count_verts(obj):
    """
    :param obj: The object to return the vertex count of.
    :return: Total number of verts
    """
    bpy.ops.object.mode_set(mode='EDIT')
    b = bmesh.from_edit_mesh(obj.data)
    return len(b.verts)


def panic_save_temp_file(file_name='utils_tester_crash.blend') -> None:
    # Saves the scene out to a blend file for later observation.
    import os
    location = os.path.abspath(file_name)
    print(f"* Location of output file --> {location} ")
    bpy.ops.wm.save_as_mainfile(filepath=location)
