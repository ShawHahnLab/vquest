"""
Tests for vquest.

These replace requests.post with a Mock object so nothing actually gets sent
out over the network.  Instead we just test that HTTP POST rqeuests *would* be
sent as expected and that the response from the web server would be parsed
correctly.

If SEND_POST_REQS is set to True, the actual POST requests will be sent to IMGT
and each response will be stored in a from-imgt.<name of test>.dat file in each
test class' associated directory.
"""

import sys
import os
import tempfile
import unittest
from unittest.mock import Mock, DEFAULT
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from io import StringIO
import yaml
from vquest.request import vquest
from vquest.util import VquestError
from vquest.__main__ import main

# If True, a mock post request function is still set up, but it also acts as a
# wrapper for real POST requests over the network and saves the real response
# data from IMGT in the test data directory.
SEND_POST_REQS = False

class TestVquestBase(unittest.TestCase):
    """Base class for supporting code.  No actual tests here."""

    def setUp(self):
        self.path = self.__setup_path()
        self.__startdir = os.getcwd()
        self.set_up_mock_post()
        # A config object to use directly with vquest().  A config.yml, if
        # present, will be used in testing the command-line interface so it can
        # be more minimal (the defaults will be applied).
        configpath = self.path / "config_inline.yml"
        if configpath.exists():
            with open(configpath) as f_in:
                self.config = yaml.load(f_in, Loader=yaml.SafeLoader)
        else:
            self.config = {}

    def tearDown(self):
        self.tear_down_mock_post()
        os.chdir(self.__startdir)

    def __setup_path(self):
        """Path for supporting files for each class."""
        # adapted from https://github.com/ShawHahnLab/umbra/blob/dev/test_umbra/test_common.py
        path = self.__class__.__module__.split(".") + [self.__class__.__name__]
        path.insert(1, "data")
        path = Path("/".join(path)).resolve()
        return path

    def set_up_mock_post(self):
        """Use fake POST request during testing."""
        reqs = sys.modules["requests"]
        reqs.post_real = reqs.post
        response = self.path / "response.dat"
        headers_path = self.path / "headers.txt"
        if response.exists():
            with open(response, "rb") as f_in:
                data = f_in.read()
        else:
            data = None
        if headers_path.exists():
            headers = {}
            with open(headers_path, "rt") as f_in:
                for line in f_in:
                    key, val = line.split(" ", 1)
                    headers[key] = val
        else:
            headers = {}
        # When the fake post function is called, it returns an object that has
        # one attribute, "content", containing the data supplied here.
        if SEND_POST_REQS:
            def actual_post_wrapper(*args, **kwargs):
                response = reqs.post_real(*args, **kwargs)
                testid = self.id().split(".")[-1]
                with open(self.path / f"from-imgt.{testid}.dat", "wb") as f_out:
                    f_out.write(response.content)
                return DEFAULT
            reqs.post = Mock(
                side_effect=actual_post_wrapper,
                return_value=Mock(content=data, headers=headers))
        else:
            reqs.post = Mock(return_value=Mock(content=data, headers=headers))
        # for easy access, though it's sys-wide
        self.post = reqs.post

    @staticmethod
    def tear_down_mock_post():
        """Put back original post function after testing."""
        reqs = sys.modules["requests"]
        reqs.post = reqs.post_real


class TestVquestSimple(TestVquestBase):
    """Basic test of vquest."""

    def test_vquest(self):
        """Test that a basic request gives the expected response."""
        result = vquest(self.config)
        # requests.post should have been called once, with this input.
        self.assertEqual(self.post.call_count, 1)
        self.assertEqual(
            self.post.call_args.args,
            ('http://www.imgt.org/IMGT_vquest/analysis', ))
        config_used = self.config.copy()
        # Whatever input type was given the actual type submitted to the form
        # will be "inline" to allow chunking of sequences if needed.  The
        # sequences are also reformatted via Biopython when chunked.
        config_used["inputType"] = "inline"
        config_used["sequences"] = """>IGKV2-ACR*02
GACATTGTGATGACCCAGACTCCACTCTCCCTGCCCGTCACCCCTGGAGAGCCAGCCTCC
ATCTCCTGCAGGTCTAGTCAGAGCCTCTTGGATAGTGACGGGTACACCTGTTTGGACTGG
TACCTGCAGAAGCCAGGCCAGTCTCCACAGCTCCTGATCTATGAGGTTTCCAACCGGGTC
TCTGGAGTCCCTGACAGGTTCAGTGGCAGTGGGTCAGNCACTGATTTCACACTGAAAATC
AGCCGGGTGGAAGCTGAGGATGTTGGGGTGTATTACTGTATGCAAAGTATAGAGTTTCCT
CC
"""
        self.assertEqual(
            self.post.call_args.kwargs,
            {"data": config_used})
        self.assertEqual(
            list(result.keys()),
            ["Parameters.txt", "vquest_airr.tsv"])
        with open(self.path / "expected/Parameters.txt") as f_in:
            parameters = f_in.read()
        with open(self.path / "expected/vquest_airr.tsv") as f_in:
            vquest_airr = f_in.read()
        self.assertEqual(parameters, result["Parameters.txt"])
        self.assertEqual(vquest_airr, result["vquest_airr.tsv"])

    def test_vquest_no_collapse(self):
        """test_vquest but with vquest(..., collapse=False)."""
        # Also try with collapse=False, for raw output
        result = vquest(self.config, collapse=False)
        self.assertEqual(self.post.call_count, 1)
        self.assertEqual(len(result), 1)
        self.assertEqual(
            list(result[0].keys()),
            ["Parameters.txt", "vquest_airr.tsv"])

    def test_vquest_main(self):
        """Test that the command-line interface gives the expected response."""
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            main([str(self.path / "config.yml")])
            self.assertTrue(Path("vquest_airr.tsv").exists())
            self.assertTrue(Path("Parameters.txt").exists())

    def test_vquest_main_no_collapse(self):
        """Test command-line interface with --no-collapse."""
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            main(["--no-collapse", str(self.path / "config.yml")])
            self.assertTrue(Path("001/vquest_airr.tsv").exists())
            self.assertTrue(Path("001/Parameters.txt").exists())

    def test_vquest_main_alignment(self):
        """Try using the --align feature.

        In this case the regular output files should not be created and instead
        FASTA text should be written to stdout.
        """
        expected = """>IGKV2-ACR*02
gacattgtgatgacccagactccactctccctgcccgtcacccctggagagccagcctccatctcctgcaggtctagtcagagcctcttggatagt...gacgggtacacctgtttggactggtacctgcagaagccaggccagtctccacagctcctgatctatgaggtt.....................tccaaccgggtctctggagtccct...gacaggttcagtggcagtggg......tcagncactgatttcacactgaaaatcagccgggtggaagctgaggatgttggggtgtattactgtatgcaaagtatagagtttcctcc
"""
        out = StringIO()
        err = StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            with tempfile.TemporaryDirectory() as tempdir:
                os.chdir(tempdir)
                main([str(self.path / "config.yml"), "--align"])
                self.assertFalse(Path("vquest_airr.tsv").exists())
                self.assertFalse(Path("Parameters.txt").exists())
        self.assertEqual(out.getvalue(), expected)
        self.assertEqual(err.getvalue(), "")


class TestVquestEmpty(TestVquestSimple):
    """What if no options are given?

    In vquest() this raises a ValueError complaining about missing defaults,
    while in main() it shows the help text and exits.
    """

    def check_missing_defaults(self, func):
        """Check that func() raises the expected exception."""
        with self.assertRaises(ValueError) as err_cm:
            func()
        self.assertEqual(
                err_cm.exception.args[0],
                "species, receptorOrLocusType, and fileSequences "
                "and/or sequences are required options")

    def check_missing_defaults_main(self, func):
        """Check that func() exits the program with the expected error."""
        out = StringIO()
        err = StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            with self.assertRaises(SystemExit) as err_cm:
                func()
        self.assertEqual(err_cm.exception.args[0], 1)
        self.assertTrue(out.getvalue().startswith("usage:"))
        self.assertEqual(err.getvalue(), "")

    def test_vquest(self):
        self.check_missing_defaults(lambda: vquest(self.config))

    def test_vquest_no_collapse(self):
        self.check_missing_defaults(lambda: vquest(self.config, collapse=False))

    def test_vquest_main(self):
        self.check_missing_defaults(lambda: main([str(self.path / "config.yml")]))

    def test_vquest_main_no_collapse(self):
        self.check_missing_defaults_main(lambda: main(["--no-collapse"]))

    def test_vquest_main_no_args(self):
        """Test how the command-line interface handles no arguments.

        It should exit with a nonzero exit code and write the help text to
        stdout.
        """
        self.check_missing_defaults_main(lambda: main([]))

    def test_vquest_main_alignment(self):
        self.check_missing_defaults_main(lambda: main(["--align"]))


class TestVquestCustom(TestVquestSimple):
    """Try changing one of the configuration options.

    Note that most of the configuration options in the Excel section actually
    don't seem to change the results when AIRR output is selected.  The "Search
    for insertions and deletions in V-REGION" option does change the output
    though.

    (Nearly nothing has to change in the code here because the associated files
    for this class have the inputs and the expected outputs.)
    """

    def test_vquest_main_custom_arg(self):
        """Try an extra argument given as though on the command line."""
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            main(["--IMGTrefdirSet", "1", str(self.path / "config.yml")])
            self.assertTrue(Path("vquest_airr.tsv").exists())
            self.assertTrue(Path("Parameters.txt").exists())


class TestVquestInvalid(TestVquestBase):
    """Test vquest for an invalid request.

    Here the server should return an HTML document with an error message, which
    we should pick up and raise as a VquestError.
    """

    def test_vquest(self):
        """Test that an html file with an error message is parsed correctly."""
        with self.assertRaises(VquestError) as err_cm:
            vquest(self.config)
        self.assertEqual(
            err_cm.exception.server_messages,
            ["The receptor type or locus is not available for this species"])
        self.assertEqual(self.post.call_count, 1)
        self.assertEqual(
            self.post.call_args.args,
            ('http://www.imgt.org/IMGT_vquest/analysis', ))

    def test_vquest_main(self):
        """Test that an html file with an error message is parsed correctly for cmd-line usage."""
        with self.assertRaises(VquestError) as err_cm:
            with tempfile.TemporaryDirectory() as tempdir:
                os.chdir(tempdir)
                main([str(self.path / "config.yml")])
        self.assertEqual(
            err_cm.exception.server_messages,
            ["The receptor type or locus is not available for this species"])
