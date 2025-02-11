"""  Welcome to MeshLint 2024.
#   This is a derivative work taken as a fork from ryanjosephking/meshlint. The purpose is to make the required
# updates so that it is compatible with Blender 4.2 onwards. Add-on management has been significantly modified
# and these third party plugins are now referred to as "Extensions".
#   I found this tool useful while debugging errors in BoltFactory generated mesh objects when making 3D print
# parts. In order to keep using it I required a port to the latest Blender release and could not find it having
# already been done.
#   Code is hosted on GitHub where the ancestry can be traced back.
# https://github.com/swtya/meshlint-update-to-4.2
# Issues can be raised, but to set expectations I'm not a software developer!
#   Credit remains with rking. The contribution from SavMartin, who completed the port to the Blender 2.80
# family, made this step possible for me.
"""

# The TO DO list:
#  - Exempt mirror-plane verts. You should not get penalised for them.
#  - Check for intersected faces??
#   - Would probably be O(n^m) or something.
#   - Would need to check the post-modified mesh (e.g., Armature-deformed)
#  - Coplanar check, especially good for Ngons.
#  - Check Normal consistency? I've had several people request this, though I still feel like the Ctrl+n tool
#    has problems solving it, so I am unconfident that I will be able to do as good or better. It is true,
#    though, that you can simply allow the user to enable the check, and if it is acting wonky they can disable it.
#  - Consider adding to the 'n' Properties Panel instead of Object Data. Or, perhaps, a user preference.
#  - Maybe add a "Skip to Next" option. So far at least 1 user has reported this. Personally, I think you
#    should hit Tab and deselect the one you want to skip, but I haven't thought it through too far.

if "bpy" not in locals():
    import bpy
    import bmesh
    import time
    import re
    from mathutils import Vector
else:
    import importlib
    importlib.reload(bmesh)
    importlib.reload(time)
    importlib.reload(re)

# Start here with some constants:
SUBPANEL_LABEL = 'MeshLint'
COMPLAINT_TIMEOUT = 3  # seconds
ELEM_TYPES = ['verts', 'edges', 'faces']

N_A_STR = '(N/A - disabled)'
TBD_STR = '...'

def is_edit_mode():
    """Tests for if the context is edit mode"""
    return 'EDIT_MESH' == bpy.context.mode

def ensure_edit_mode():
    """Forces the object into edit mode"""
    if not is_edit_mode():
        bpy.ops.object.editmode_toggle()

def ensure_not_edit_mode():
    """If in edit mode returns to object mode"""
    if is_edit_mode():
        bpy.ops.object.editmode_toggle()

def has_active_mesh(context):
    """Returns a bool of the active object being a mesh"""
    obj = context.active_object
    return obj and 'MESH' == obj.type

class MeshLintAnalyzer:
    """The main brain of the application: Finds the problems and defines the checks"""
    CHECKS = []

    def __init__(self):
        ensure_edit_mode()
        self.obj = bpy.context.active_object
        self.b = bmesh.from_edit_mesh(self.obj.data)
        self.num_problems_found = None

    def find_problems(self):
        """Finds the problems"""
        analysis = []
        self.num_problems_found = 0
        for lint in MeshLintAnalyzer.CHECKS:
            should_check = getattr(bpy.context.scene, f"{lint['check_prop']}")
            if not should_check:
                lint['count'] = N_A_STR
                continue
            lint['count'] = 0
            check_method_name = 'check_' + f"{lint['symbol']}"
            check_method = getattr(type(self), check_method_name)
            bad = check_method(self)
            report = {'lint': lint}
            for elemtype in ELEM_TYPES:
                indices = bad.get(elemtype, [])
                report[elemtype] = indices
                lint['count'] += len(indices)
                self.num_problems_found += len(indices)
            analysis.append(report)
        return analysis

    def found_zero_problems(self):
        """Just a quick way to have a bool for finding any problems"""
        return 0 == self.num_problems_found

    @classmethod
    def none_analysis(cls):
        """Builds an empty analysis"""
        analysis = []
        for lint in cls.CHECKS:
            row = {elemtype: [] for elemtype in ELEM_TYPES}
            row['lint'] = lint
            analysis.append(row)
        return analysis

    CHECKS.append({
        'symbol': 'tris',
        'label': 'Tris',
        'definition': 'A face with 3 edges. Often bad for modelling because it stops edge loops and does not ' +
                      'deform well around bent areas. A mesh might look good until you animate, so beware!',
        'default': True
    })

    def check_tris(self):
        """Check for Tris"""
        bad = {'faces': []}
        for fff in self.b.faces:
            if 3 == len(fff.verts):
                bad['faces'].append(fff.index)
        return bad

    CHECKS.append({
        'symbol': 'ngons',
        'label': 'Ngons',
        'definition': 'A face with >4 edges. Is generally bad in exactly the same ways as Tris',
        'default': True
    })

    def check_ngons(self):
        """Check for Ngons"""
        bad = {'faces': []}
        for fff in self.b.faces:
            if 4 < len(fff.verts):
                bad['faces'].append(fff.index)
        return bad

    CHECKS.append({
        'symbol': 'nonmanifold',
        'label': 'Nonmanifold Elements',
        'definition': 'Simply, shapes that won\'t hold water. More precisely, nonmanifold edges ' +
                      'are those that do not have exactly 2 faces attached to them (either more ' +
                      'or less). Nonmanifold verts are more complicated -- you can see their ' +
                      'definition in BM_vert_is_manifold() in bmesh_queries.c',
        'default': True
    })

    def check_nonmanifold(self):
        """Check for Nonmanifold"""
        bad = {}
        for elemtype in 'verts', 'edges':
            bad[elemtype] = []
            for elem in getattr(self.b, elemtype):
                if not elem.is_manifold:
                    bad[elemtype].append(elem.index)
        # Exempt mirror-plane verts would go in here.
        # Plus: ...anybody wanna tackle Mirrors with an Object Offset?
        return bad

    CHECKS.append({
        'symbol': 'interior_faces',
        'label': 'Interior Faces',
        'definition': 'This confuses people. It is very specific: A face whose edges ALL have >2 faces ' +
                      'attached. The simplest way to see this is to Ctrl+r a Default Cube and hit \'f\'',
        'default': True
    })

    def check_interior_faces(self):
        """Check for Interior Faces
        # translated from editmesh_select.c
        """
        bad = {'faces': []}
        for fff in self.b.faces:
            if not any(3 > len(eee.link_faces) for eee in fff.edges):
                bad['faces'].append(fff.index)
        return bad

    CHECKS.append({
        'symbol': 'three_poles',
        'label': '3-edge Poles',
        'definition': 'A vertex with 3 edges connected to it. Also known as an N-Pole',
        'default': False
    })

    def check_three_poles(self):
        """Check for 3-edge Poles"""
        bad = {'verts': []}
        for vvv in self.b.verts:
            if 3 == len(vvv.link_edges):
                bad['verts'].append(vvv.index)
        return bad

    CHECKS.append({
        'symbol': 'five_poles',
        'label': '5-edge Poles',
        'definition': 'A vertex with 5 edges connected to it. Also known as an E-Pole',
        'default': False
    })

    def check_five_poles(self):
        """Check for 5-edge Poles"""
        bad = {'verts': []}
        for vvv in self.b.verts:
            if 5 == len(vvv.link_edges):
                bad['verts'].append(vvv.index)
        return bad

    CHECKS.append({
        'symbol': 'sixplus_poles',
        'label': '6+-edge Poles',
        'definition': 'A vertex with 6 or more edges connected to it. Generally this is not something you ' +
                      'want, but since some kinds of extrusions will legitimately cause such a pole (imagine ' +
                      'extruding each face of a Cube outward, the inner corners are rightful 6+-poles). ' +
                      'Still, if you don\'t know for sure that you want them, it is good to enable this',
        'default': True
    })

    def check_sixplus_poles(self):
        """Check for 6+-edge Poles"""
        bad = {'verts': []}
        for vvv in self.b.verts:
            if 5 < len(vvv.link_edges):
                bad['verts'].append(vvv.index)
        return bad
    # [Your great new idea here] -> Tell me about it: rking@panoptic.com

    # ...plus the 'Default Name' check.

    def enable_anything_select_mode(self):
        """Makes sure that we can select 'VERT', 'EDGE', 'FACE' """
        self.b.select_mode = {'VERT', 'EDGE', 'FACE'}

    def select_indices(self, elemtype, indices):
        """For a given element ('VERT', 'EDGE', 'FACE') then select that index """
        for inc in indices:
            if 'verts' == elemtype:
                self.select_vert(inc)
            elif 'edges' == elemtype:
                self.select_edge(inc)
            elif 'faces' == elemtype:
                self.select_face(inc)
            else:
                print(f"MeshLint says: Huh?? → elemtype of {elemtype}.")

    def select_vert(self, index):
        """Select the given VERT index in the mesh"""
        ob1 = bpy.context.edit_object
        me1 = ob1.data
        bm1 = bmesh.from_edit_mesh(me1)
        bm1.verts.ensure_lookup_table()  # sav
        self.b.verts[index].select = True

    def select_edge(self, index):
        """Select the given EDGE index in the mesh and its VERTS"""
        ob2 = bpy.context.edit_object
        me2 = ob2.data
        bm2 = bmesh.from_edit_mesh(me2)
        bm2.edges.ensure_lookup_table()  # sav
        edge = self.b.edges[index]
        edge.select = True
        for each in edge.verts:
            self.select_vert(each.index)

    def select_face(self, index):
        """Select the given FACE index in the mesh amd its EDGES"""
        ob3 = bpy.context.edit_object
        me3 = ob3.data
        bm3 = bmesh.from_edit_mesh(me3)
        bm3.faces.ensure_lookup_table()  # sav
        face = self.b.faces[index]
        face.select = True
        for each in face.edges:
            self.select_edge(each.index)

    def topology_counts(self):
        """Returns object data and number of faces, edges & verts"""
        return {
            'data': self.obj.data,
            'faces': len(self.b.faces),
            'edges': len(self.b.edges),
            'verts': len(self.b.verts)}

    for lint in CHECKS:
        lint['count'] = TBD_STR
        lint['check_prop'] = 'meshlint_check_' + f"{lint['symbol']}"
        setattr(
            bpy.types.Scene,
            f"{lint['check_prop']}",
            bpy.props.BoolProperty(
                default=lint['default'],
                description=lint['definition']))
        if hasattr(bpy.context, 'scene'):
            # At first startup then context does not have a scene attribute
            if hasattr(bpy.context.scene, f"{lint['check_prop']}"):
                # When reloading the check_prop attribute, it might not have been created
                # If it has, then proceed with defaulting the toggles settings.
                setattr(bpy.context.scene, f"{lint['check_prop']}", lint['default'])

@bpy.app.handlers.persistent
def meshlint_gbl_continuous_check(scene, depsgraph):
    """Function decorator for callback functions not to be removed when loading new files"""
    MeshLintContinuousChecker.check()

class MeshLintContinuousChecker:
    """This is the continuous checker routine"""
    current_message = ''
    time_complained = 0
    # previous_topology_counts = None
    previous_analysis = None
    previous_data_name = None

    @classmethod
    def check(cls):
        """This is the check function"""
        if not is_edit_mode():
            return
        analyzer = MeshLintAnalyzer()
        now_counts = analyzer.topology_counts()
        if hasattr(cls, 'previous_topology_counts'):
            previous_topology_counts = cls.previous_topology_counts
            if previous_topology_counts is not None:
                try:
                    if 'data' not in previous_topology_counts:
                        print('no "data" in previous topology counts')
                    # print(previous_topology_counts['data'])
                    if not hasattr(previous_topology_counts['data'], 'name'):
                        print('no "name" attribute')
                except ReferenceError:
                    print('Must be "data" that did not exist')
                    print(previous_topology_counts)
        else:
            # print('previous_topology_counts did not exist')
            previous_topology_counts = None

        # print(previous_topology_counts)
        # analyzer.find_problems()    # putting this here makes it run more often
        if None is previous_topology_counts \
                or now_counts != previous_topology_counts:
            analysis = analyzer.find_problems()
            diff_msg = cls.diff_analyses(cls.previous_analysis, analysis)
            if diff_msg is not None:
                cls.announce(diff_msg)
                cls.time_complained = time.time()
            cls.previous_topology_counts = now_counts
            cls.previous_analysis = analysis

        if cls.time_complained is not None \
                and COMPLAINT_TIMEOUT < time.time() - cls.time_complained:
            cls.announce(None)
            cls.time_complained = None

    @classmethod
    def diff_analyses(cls, before, after):
        """Compares before and after; well previous to now"""
        if None is before:
            before = MeshLintAnalyzer.none_analysis()
        report_strings = []
        dict_before = cls.make_labels_dict(before)
        dict_now = cls.make_labels_dict(after)
        for check in MeshLintAnalyzer.CHECKS:
            check_name = check['label']
            if check_name not in dict_now:
                continue
            report = dict_now[check_name]
            report_before = dict_before.get(check_name, {})
            check_elem_strings = []
            for elemtype, elem_list in report.items():
                elem_list_before = report_before.get(elemtype, [])
                if len(elem_list) > len(elem_list_before):
                    count_diff = len(elem_list) - len(elem_list_before)
                    check_elem_strings.append(str(count_diff) + ' ' +
                                              depluralize(count=count_diff, string=elemtype))
            if check_elem_strings:
                report_strings.append(check_name + ': ' + ', '.join(check_elem_strings))
        if report_strings:
            return 'Found ' + ', '.join(report_strings)
        return None

    @classmethod
    def make_labels_dict(cls, analysis):
        """Takes in an analysis and returns a dictionary of labels"""
        if None is analysis:
            return {}
        labels_dict = {}
        for check in analysis:
            label = check['lint']['label']
            new_val = check.copy()
            del new_val['lint']
            labels_dict[label] = new_val
        return labels_dict

    @classmethod
    def announce(cls, message):
        """If the INFO box is open then print a message to the header area
        This is way easier than writing into that confounded box"""
        for area in bpy.context.screen.areas:
            if 'INFO' != area.type:
                continue
            if None is message:
                area.header_text_set(None)
            else:
                area.header_text_set('MeshLint: ' + message)

class MeshLintVitalizer(bpy.types.Operator):
    """Toggles the real-time execution of the checks (Edit Mode only)"""
    bl_idname = 'meshlint.live_toggle'
    bl_label = 'MeshLint Live Toggle'
    bl_options = {'REGISTER', 'UNDO'}

    is_live = False
    text = 'Continuous Check!!'
    play_pause = 'PLAY'

    @classmethod
    def poll(cls, context):
        return has_active_mesh(context) and is_edit_mode()

    def execute(self, context):
        if MeshLintVitalizer.is_live:
            bpy.app.handlers.depsgraph_update_post.remove(meshlint_gbl_continuous_check)
            MeshLintVitalizer.is_live = False
            MeshLintVitalizer.text = 'Continuous Check!'
            MeshLintVitalizer.play_pause = 'PLAY'
            for area in bpy.context.screen.areas:
                if 'INFO' == area.type:           # Prevents the title of the INFO getting stuck
                    area.header_text_set(None)    # when stopping the continuous checker.
        else:
            bpy.app.handlers.depsgraph_update_post.append(meshlint_gbl_continuous_check)
            MeshLintVitalizer.is_live = True
            MeshLintVitalizer.text = 'Pause Checking...'
            MeshLintVitalizer.play_pause = 'PAUSE'
        return {'FINISHED'}

def activate(obj):
    """Makes the passed in object active"""
    # bpy.context.scene.objects.active = obj #sav
    bpy.context.view_layer.objects.active = obj

class MeshLintObjectLooper:
    """Routines for examining the scene objects"""
    def __init__(self):
        self.original_active = bpy.context.active_object
        self.troubled_meshes = []

    @staticmethod
    def examine_active_object():
        """Conduct lint analysis of the selected object, returns True if the Mesh is clean"""
        analyzer = MeshLintAnalyzer()
        analyzer.enable_anything_select_mode()
        # self.select_none()
        bpy.ops.mesh.select_all(action='DESELECT')
        analysis = analyzer.find_problems()
        for lint in analysis:
            for elemtype in ELEM_TYPES:
                indices = lint[elemtype]
                analyzer.select_indices(elemtype, indices)
        # print('selected all the issues')
        bpy.context.area.tag_redraw()
        return analyzer.found_zero_problems()

    def examine_all_selected_meshes(self):
        """ For the current object plus all selected objects do lint analysis"""
        examinees = [self.original_active] + bpy.context.selected_objects
        for obj in examinees:
            if 'MESH' != obj.type:
                continue            # skip everything other than meshes
            activate(obj)
            good = self.examine_active_object()
            ensure_not_edit_mode()
            if not good:
                self.troubled_meshes.append(obj)
        priorities = [self.original_active] + self.troubled_meshes
        for obj in priorities:
            if obj.select_get:
                activate(obj)
                break
        if self.troubled_meshes:
            MeshLintObjectDeselector.handle_troubled_meshes(self)
        bpy.context.area.tag_redraw()

    # def select_none(self):
        # bpy.ops.mesh.select_all(action='DESELECT')

class MeshLintSelector(MeshLintObjectLooper, bpy.types.Operator):
    """Uncheck boxes below to prevent those checks from running"""
    bl_idname = 'meshlint.select'
    bl_label = 'MeshLint Select'
    bl_options = {'REGISTER', 'UNDO'}
    text = 'Select Lint'

    @classmethod
    def poll(cls, context):
        return has_active_mesh(context)

    def execute(self, context):
        original_mode = bpy.context.mode
        if is_edit_mode():
            self.examine_active_object()
        else:
            self.examine_all_selected_meshes()
            if self.troubled_meshes:
                ensure_edit_mode()
            elif 'EDIT_MESH' != original_mode:
                ensure_not_edit_mode()
        return {'FINISHED'}

    #def handle_troubled_meshes(self):
    #    """Nothing to see here
    #    Has a kickback from:   def examine_all_selected_meshes(self):"""
    #    # future ticket might need to play with this more
    #    pass

class MeshLintObjectDeselector(MeshLintObjectLooper, bpy.types.Operator):
    """Uncheck boxes below to prevent those checks from running (Object Mode only)"""
    bl_idname = 'meshlint.objects_deselect'
    bl_label = 'MeshLint Objects Deselect'
    bl_options = {'REGISTER', 'UNDO'}
    text = 'Deselect all Lint-free Objects'

    @classmethod
    def poll(cls, context):
        selected_meshes = [o for o in context.selected_objects if o.type == 'MESH']
        return 1 < len(selected_meshes) and not is_edit_mode()

    def execute(self, context):
        self.examine_all_selected_meshes()
        return {'FINISHED'}

    def handle_troubled_meshes(self):
        """Does the deselection of the troubled mesh list"""
        #print("deselection happening")
        for obj in bpy.context.selected_objects:
            if obj not in self.troubled_meshes:
                obj.select_set(False)

class MESH_PT_MeshLintControl(bpy.types.Panel):
    """Responsible for building the GUI in the Properties window on the Data tab.
    The SUBPANEL title is set as a constant at the top of the file. """
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'
    bl_label = SUBPANEL_LABEL

    @classmethod
    def poll(cls, context):
        """Boolean gatekeeper for the draw"""
        return has_active_mesh(context)

    def draw(self, context):
        """Pulls together the three components in the side panel
        [ The buttons ]
        [ The report result aka criticism ]
        [ The lint tick boxes for test options to enable ]
        """
        layout = self.layout
        self.add_main_buttons(layout)
        self.add_criticism(layout, context)
        self.add_toggle_buttons(layout, context)

    @staticmethod
    def add_main_buttons(layout):
        """Puts the three buttons onto the side panel
        [  Select Lint  ]  [  Continuous Check  ]
        [    Deselect all Lint-free Objects     ]
        """
        split = layout.split()
        left = split.column()
        left.operator(MeshLintSelector.bl_idname, text=MeshLintSelector.text, icon='EDITMODE_HLT')
        right = split.column()
        right.operator(MeshLintVitalizer.bl_idname, text=MeshLintVitalizer.text, icon=MeshLintVitalizer.play_pause)
        layout.split().operator(MeshLintObjectDeselector.bl_idname,
                                text=MeshLintObjectDeselector.text, icon='UV_ISLANDSEL')

    @staticmethod
    def add_criticism(layout, context):
        """Builds the lint numerical result for each test"""
        col = layout.column()
        # active = context.active_object
        if not has_active_mesh(context):
            return
        total_problems = 0
        for lint in MeshLintAnalyzer.CHECKS:
            count = lint['count']
            if count in (TBD_STR, N_A_STR):
                label = str(count) + ' ' + f"{lint['label']}"
                reward = 'SOLO_OFF'
            elif 0 == count:
                label = f'Zero {lint["label"]}!'
                reward = 'SOLO_ON'
            else:
                total_problems += count
                label = str(count) + 'x ' + f"{lint['label']}"
                label = depluralize(count=count, string=label)
                reward = 'ERROR'
            col.row().label(text=label, icon=reward)
        name_crits = MESH_PT_MeshLintControl.build_object_criticisms(bpy.context.selected_objects, total_problems)
        for crit in name_crits:
            col.row().label(text=crit)

    @staticmethod
    def add_toggle_buttons(layout, context):
        """Builds the tick boxes for the GUI"""
        col = layout.column()
        col.row().label(text='MeshLint rules to include:')
        for lint in MeshLintAnalyzer.CHECKS:
            prop_name = lint['check_prop']
            label = 'Check ' + f"{lint['label']}"
            col.row().prop(context.scene, prop_name, text=label)

    @classmethod
    def build_object_criticisms(cls, objects, total_problems):
        """Generates the criticism text for the side panel"""
        already_complained = total_problems > 0
        criticisms = []

        def add_crit(crit):
            if already_complained:
                conjunction = 'and also'
            else:
                conjunction = 'but'
            criticisms.append(f'...{conjunction} "{obj.name}" {crit}.')
        for obj in objects:
            if MESH_PT_MeshLintControl.has_unapplied_scale(obj.scale):
                add_crit('has an unapplied scale')
                already_complained = True
            if MESH_PT_MeshLintControl.is_bad_name(obj.name):
                add_crit('is not a great name')
                already_complained = True
        return criticisms

    @classmethod
    def has_unapplied_scale(cls, scale):
        """Where an object has no outstanding scale to be applied the values will be 1.0.
        This Looks at the scale of an object and determines if it is ==1.0."""
        return 3 != len([c for c in scale if c == 1.0])

    @classmethod
    def is_bad_name(cls, name):
        """A list of names that are default"""
        default_names = [
            'BezierCircle',
            'BezierCurve',
            'Circle',
            'Cone',
            'Cube',
            'CurvePath',
            'Cylinder',
            'Grid',
            'Icosphere',
            'Mball',
            'Monkey',
            'NurbsCircle',
            'NurbsCurve',
            'NurbsPath',
            'Plane',
            'Sphere',
            'Surface',
            'SurfCircle',
            'SurfCurve',
            'SurfCylinder',
            'SurfPatch',
            'SurfSphere',
            'SurfTorus',
            'Text',
            'Torus',
        ]
        pat = rf'({"|".join(default_names)})\.?\d*$'
        return re.match(pat, name) is not None

def depluralize(**args):
    """Singular of things is thing, this just knocks off the s at the end of a string."""
    if 1 == args['count']:
        return args['string'].rstrip('s')
    return args['string']

# Next section of the file is unittest
# Classes and registration is right at the end as required by Blender.

try:        # (Back at 2.79) Why does it work for some Blender's but not others?
    import unittest
    import warnings

    class TestControl(unittest.TestCase):
        """ Test the functions in the main block:
            # has_unapplied_scale
            # is_bad_name   """
        def test_scale_application(self):
            """Check for unapplied scale """
            for bad in [[0, 0, 0], [1, 2, 3], [1, 1, 1.1]]:
                self.assertEqual(
                    True, MESH_PT_MeshLintControl.has_unapplied_scale(bad),
                    "Unapplied scale: %s" % bad)
            self.assertEqual(
                False, MESH_PT_MeshLintControl.has_unapplied_scale([1, 1, 1]),
                "Applied scale (1,1,1)")

        def test_bad_names(self):
            """Check a couple of good & bad names likely to be in the scene"""
            for bad in ['Cube', 'Cube.001', 'Sphere.123']:
                self.assertEqual(
                    True, MESH_PT_MeshLintControl.is_bad_name(bad),
                    f"Bad name: {bad}")
            for aok in ['Whatever', 'NumbersOkToo.001']:
                self.assertEqual(
                    False, MESH_PT_MeshLintControl.is_bad_name(aok),
                    f"OK name: {aok}")

    class TestUtilities(unittest.TestCase):
        """ Test class for utilities:
                # ensure_edit_mode, is_edit_mode
                # ensure_not_edit_mode, is_edit_mode
                # depluralize  """
        def test_is_edit_mode(self):
            """Check flipping in and out of edit mode"""
            ensure_edit_mode()
            self.assertEqual(True, is_edit_mode(),
                "Ensures edit mode then checks if in edit mode")
            ensure_not_edit_mode()
            self.assertEqual(False, is_edit_mode(),
                "Ensures not edit mode then checks if not edit mode")

        def test_depluralize(self):
            """The depluralize attempts to remove a lower case 's'
            only if the count arg is exactly 1. This is obviously limited in generalist capabilities.
            I'm messing around here but "Tris" does end up at "Tri" currently."""
            self.assertEqual('foo',
                depluralize(count=1, string='foos'))
            self.assertEqual('foos',
                depluralize(count=2, string='foos'))
            self.assertNotEqual('FOO',
                depluralize(count=1, string='FOOS'))
            self.assertNotEqual('fox',
                depluralize(count=1, string='foxes'),"Singular of Foxes is Foxe!")
            self.assertNotEqual('Blueberry',
                depluralize(count=1, string='Blueberries'),"Singular of Blueberries is Blueberrie")
            self.assertEqual('sheep',
                depluralize(count=1, string='sheep'),"Singular of Sheep is Sheep")

    class TestAnalysis(unittest.TestCase):
        """Checks the making of the dictionary."""
        def test_make_labels_dict(self):
            """Checks that the format of the labels in the dictionary is good"""
            self.assertEqual(
                {
                    'Label One': {
                        'edges': [1, 2], 'verts': [], 'faces': []},
                    'Label Two': {
                        'edges': [], 'verts': [5], 'faces': [3]}
                },
                MeshLintContinuousChecker.make_labels_dict(
                    [
                        {'lint': {'label': 'Label One'},
                            'edges': [1, 2], 'verts': [], 'faces': []},
                        {'lint': {'label': 'Label Two'},
                            'edges': [], 'verts': [5], 'faces': [3]}
                    ]),
                'Conversion of incoming analysis into label-keyed dict')
            self.assertEqual({},
                MeshLintContinuousChecker.make_labels_dict(None),
                'Handles "None" OK.')

        def test_comparison(self):
            """ Test group to check the diff_analyses block of code
            1) None - None = None            # constant labels
            2) None - thing = thing          # constant labels
            3) a(set) - b(set) = (a-b)(set)  # constant labels
            4) A(B) - C(D) = (A-C)(B-D)      # labels and data both change """
            self.assertEqual(
                None,
                MeshLintContinuousChecker.diff_analyses(
                    MeshLintAnalyzer.none_analysis(),
                    MeshLintAnalyzer.none_analysis()),
                'Two none_analysis()s')
            self.assertEqual(
                'Found Tris: 4 verts',
                MeshLintContinuousChecker.diff_analyses(
                    None,
                    [
                        {
                            'lint': {'label': 'Tris'},
                            'verts': [1, 2, 3, 4],
                            'edges': [],
                            'faces': [],
                        },
                    ]),
                'When there was no previous analysis')
            self.assertEqual(
                'Found Tris: 2 edges, ' +
                'Nonmanifold Elements: 4 verts, 2 faces',
                MeshLintContinuousChecker.diff_analyses(
                    [
                        {'lint': {'label': 'Tris'},
                         'verts': [], 'edges': [1, 4], 'faces': [], },
                        {'lint': {'label': 'CheckB'},
                         'verts': [], 'edges': [2, 3], 'faces': [], },
                        {'lint': {'label': 'Nonmanifold Elements'},
                         'verts': [], 'edges': [], 'faces': [2, 3], },
                    ],
                    [
                        {'lint': {'label': 'Tris'},
                         'verts': [], 'edges': [1, 4, 5, 6], 'faces': [], },
                        {'lint': {'label': 'CheckB'},
                         'verts': [], 'edges': [2, 3], 'faces': [], },
                        {'lint': {'label': 'Nonmanifold Elements'},
                         'verts': [1, 2, 3, 4], 'edges': [], 'faces': [1, 2, 3, 5], },
                    ]),
                'Complex comparison of analyses')
            self.assertEqual(
                'Found Tris: 2 verts, Ngons: 2 faces, ' +
                'Nonmanifold Elements: 2 edges',
                MeshLintContinuousChecker.diff_analyses(
                    [
                        {'lint': {'label': '6+-edge Poles'},
                         'verts': [], 'edges': [2, 3], 'faces': [], },
                        {'lint': {'label': 'Nonmanifold Elements'},
                         'verts': [], 'edges': [2, 3], 'faces': [], },
                    ],
                    [
                        {'lint': {'label': 'Tris'},
                         'verts': [55, 56], 'edges': [], 'faces': [], },
                        {'lint': {'label': 'Ngons'},
                         'verts': [], 'edges': [], 'faces': [5, 6], },
                        {'lint': {'label': 'Nonmanifold Elements'},
                         'verts': [], 'edges': [2, 3, 4, 5], 'faces': [], },
                    ]),
                'User picked a different set of checks since last run.')

    class MockBlenderObject:
        """A very simple object on which to test some properties"""
        def __init__(self, name, scale=Vector([1, 1, 1])):
            self.name = name
            self.scale = scale

    class TestUI(unittest.TestCase):
        """This group of tests cover the UI parts of the Extension"""
        def test_complaints(self):
            """Tests for the text manipulation of the GUI
                # using build_object_criticisms
            """
            fff = MESH_PT_MeshLintControl.build_object_criticisms
            self.assertEqual([], fff([], 0), 'Nothing selected')
            self.assertEqual([],
                fff([MockBlenderObject('lsmft')], 0),
                'Ok name')
            self.assertEqual(['...but "Cube" is not a great name.'],
                fff([MockBlenderObject('Cube')], 0),
                'Bad name, otherwise problem-free.')
            self.assertEqual([],
                fff([MockBlenderObject('Hassenfrass')], 12),
                'Good name, but with problems.')
            self.assertEqual(['...and also "Cube" is not a great name.'],
                fff([MockBlenderObject('Cube')], 23),
                'Bad name, and problems, too.')
            self.assertEqual(['...but "Sphere" is not a great name.',
                                   '...and also "Cube" is not a great name.'],
                fff([MockBlenderObject('Sphere'),
                            MockBlenderObject('Cube')], 0),'Two bad names.')
            scaled = MockBlenderObject('Solartech', scale=Vector([.2, 2, 1]))
            self.assertEqual(['...but "Solartech" has an unapplied scale.'],
                fff([scaled], 0),'Only problem is unapplied scale.')

    class QuietOnSuccessTestResult(unittest.TextTestResult):
        """ This is used for overriding results print out from the unittest test runner. """
        def startTest(self, test):
            """ The pass in here prevents terminal printout from unittest """
            # pass # [unnecessary-pass]

        def addSuccess(self, test):
            """ The pass in here prevents terminal printout from unittest """
            # pass # [unnecessary-pass]

    class QuietTestRunner(unittest.TextTestRunner):
        """ The Quiet Test Runner runs tests very quietly, it only prints out to the terminal if there
         are fails. On a fail, the output text incorrectly reports the number of tests run!"""
        resultclass = QuietOnSuccessTestResult

        # Ugh. I really shouldn't have to include this much code, but they left it so unrefactored
        # I don't know what else to do. My other option is to override the stream and substitute
        # out the success case, but that's a mess, too. - rking
        def run(self, test):
            """Run the suite of test, quietly."""
            debug_print = True  # Bool: Suppressing debug printing test verification

            if debug_print:
                print("MeshLint: starting QuietTestRunner.run")
            result = self._makeResult()
            unittest.registerResult(result)
            result.failfast = self.failfast
            result.buffer = self.buffer
            with warnings.catch_warnings():
                if self.warnings:
                    # if self.warnings is set, use it to filter all the warnings
                    warnings.simplefilter(self.warnings)
                    # if the filter is 'default' or 'always', special-case the warnings from the deprecated
                    # unittest methods to show them no more than once per module, because they can be fairly
                    # noisy.  The -Wd and -Wa flags can be used to bypass this only when self.warnings is None.
                    if self.warnings in ['default', 'always']:
                        warnings.filterwarnings('module',
                                                category=DeprecationWarning,
                                                message=r'Please use assert\w+ instead.')
                startTime = time.time()
                startTestRun = getattr(result, 'startTestRun', None)
                if getattr(result, 'startTestRun', None) is not None:
                    startTestRun()
                try:
                    test(result)
                finally:
                    stopTestRun = getattr(result, 'stopTestRun', None)
                    if stopTestRun is not None:
                        stopTestRun()
                stopTime = time.time()
            result.printErrors()

            expectedFails = unexpectedSuccesses = skipped = 0
            try:
                results = map(len, (result.expectedFailures,
                                    result.unexpectedSuccesses,
                                    result.skipped))
            except AttributeError:
                pass
            else:
                expectedFails, unexpectedSuccesses, skipped = results

            infos = []
            if not result.wasSuccessful():
                self.stream.write("FAILED")
                failed, errored = len(result.failures), len(result.errors)
                if failed:
                    infos.append(f"failures={failed:d}")
                if errored:
                    infos.append(f"errors={errored:d}")
            if skipped:
                infos.append(f"skipped={skipped:d}")
            if expectedFails:
                infos.append(f"expected failures={expectedFails:d}")
            if unexpectedSuccesses:
                infos.append(f"unexpected successes={unexpectedSuccesses:d}")
            if debug_print:
                print(f"\nQuietTestRunner Time Taken: {stopTime - startTime} seconds")
                print(f"---Result Start---\n{result}\n---Result End---")
                print(f"---infos Start---\n{infos}\n---infos End---")
            return result

    if __name__ == '__main__':
        BE_QUIET = False
        """ How to run the unittest using Blender, Linux example, from a terminal:
          '/home/<<path=to-blender>>/blender-4.2.0-linux-x64/blender' --background --python '/home/<<path-to-this-file>>/__init__.py'  -- --verbose
        There are two styles, hence the two different unittest.main calls; depends on your workflow. """
        if BE_QUIET:
            # This will print nothing if it passes, but did it run...
            unittest.main(
                testRunner=QuietTestRunner,
                argv=['dummy'],
                exit=False,
                verbosity=2,
                warnings='always')
        else:
            print('   MeshLint: Hello from unittester')
            import sys
            sys.argv = [__file__] + (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
            print(sys.argv)
            unittest.main(exit=False)
            print('   MeshLint: Goodbye from unittester')

except ImportError:
    print("MeshLint complains over missing unittest module.", """
        No harm, but it is odd. If you want to help raise an issue on GitHub
        describing your system, it may be possible to track down this condition.""")

classes = (
    MESH_PT_MeshLintControl,
    MeshLintObjectDeselector,
    MeshLintSelector,
    MeshLintVitalizer,
)

def register():
    """Register the classes in Blender"""
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    """Un-Register the classes in Blender & also make sure continuous to stopped"""
    for handy in bpy.app.handlers.depsgraph_update_post:
        if handy.__name__ == 'meshlint_gbl_continuous_check':
            bpy.app.handlers.depsgraph_update_post.remove(handy)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
