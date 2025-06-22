# This file contains the classes for the unit test machine

from __init__ import *


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
        debug_print = False  # Bool: Suppressing debug printing test verification

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
            start_time = time.time()
            startTestRun = getattr(result, 'startTestRun', None)
            if getattr(result, 'startTestRun', None) is not None:
                startTestRun()
            try:
                test(result)
            finally:
                stopTestRun = getattr(result, 'stopTestRun', None)
                if stopTestRun is not None:
                    stopTestRun()
            stop_time = time.time()
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
        runned = result.testsRun
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
            print(f"\nQuietTestRunner Time Taken: {stop_time - start_time} seconds")
            print(f"---Result Start---\n{result}\n---Result End---")
            print(f"---infos Start---\n{infos}\n---infos End---")
            print(f'passed = {runned}')         # Why is this always zero?
        return result


class MockBlenderObject:
    """A very simple object on which to test some properties"""

    def __init__(self, name, scale=Vector([1, 1, 1])):
        self.name = name
        self.scale = scale


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
                            depluralize(count=1, string='foxes'), "Singular of Foxes is Foxe!")
        self.assertNotEqual('Blueberry',
                            depluralize(count=1, string='Blueberries'), "Singular of Blueberries is Blueberrie")
        self.assertEqual('sheep',
                         depluralize(count=1, string='sheep'), "Singular of Sheep is Sheep")


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
