"""
Tests for vquest.

These replace requests.post with a Mock object so nothing actually gets sent
out over the network.  Instead we just test that HTTP POST rqeuests *would* be
sent as expected and that the response from the web server would be parsed
correctly.
"""

import sys
import os
import tempfile
import unittest
from unittest.mock import Mock
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from io import StringIO
from vquest.request import vquest
from vquest.util import VquestError
from vquest.__main__ import main

class TestVquestBase(unittest.TestCase):
    """Base class for supporting code.  No actual tests here."""

    def setUp(self):
        self.set_up_mock_post()
        self.__startdir = os.getcwd()

    def tearDown(self):
        self.tear_down_mock_post()
        os.chdir(self.__startdir)

    @property
    def path(self):
        """Path for supporting files for each class."""
        # adapted from https://github.com/ShawHahnLab/umbra/blob/dev/test_umbra/test_common.py
        path = self.__class__.__module__.split(".") + [self.__class__.__name__]
        path.insert(1, "data")
        path = Path("/".join(path))
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
        config = {
            "species": "rhesus-monkey",
            "receptorOrLocusType": "IG",
            "resultType": "excel",
            "xv_outputtype": 3,
            "sequences": """>IGKV2-ACR*02
GACATTGTGATGACCCAGACTCCACTCTCCCTGCCCGTCACCCCTGGAGAGCCAGCCTCCATCTCCTGCAGGTCTAGTCA
GAGCCTCTTGGATAGTGACGGGTACACCTGTTTGGACTGGTACCTGCAGAAGCCAGGCCAGTCTCCACAGCTCCTGATCT
ATGAGGTTTCCAACCGGGTCTCTGGAGTCCCTGACAGGTTCAGTGGCAGTGGGTCAGNCACTGATTTCACACTGAAAATC
AGCCGGGTGGAAGCTGAGGATGTTGGGGTGTATTACTGTATGCAAAGTATAGAGTTTCCTCC"""}
        result = vquest(config)
        # requests.post should have been called once, with this input.
        self.assertEqual(self.post.call_count, 1)
        self.assertEqual(
            self.post.call_args.args,
            ('http://www.imgt.org/IMGT_vquest/analysis', ))
        config_used = config.copy()
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
        parameters = [("Date", "Tue Dec 01 22:08:11 CET 2020"),
        ("IMGT/V-QUEST program version", "3.5.21"),
        ("IMGT/V-QUEST reference directory release", "202049-2"),
        ("Species", "Macaca mulatta"),
        ("Receptor type or locus", "IG"),
        ("IMGT/V-QUEST reference directory set", "F+ORF+ in-frame P"),
        ("Search for insertions and deletions", "no"),
        ("Nb of nucleotides to add (or exclude) in 3' "
            "of the V-REGION for the evaluation of the alignment score", "0"),
        ("Nb of nucleotides to exclude in 5' "
            "of the V-REGION for the evaluation of the nb of mutations", "0"),
        ("Analysis of scFv", "no"),
        ("Number of submitted sequences", "1")]
        self.assertEqual(
            "\n".join(["%s\t%s\t" % param for param in parameters]) + "\n\n",
            result["Parameters.txt"])
        seq = result["vquest_airr.tsv"].splitlines()[1].split("\t")[1]
        self.assertEqual(
            ("GACATTGTGATGACCCAGACTCCACTCTCCCTGCCCGTCACCCCTGGAGAGCCAGCCTCC"
            "ATCTCCTGCAGGTCTAGTCAGAGCCTCTTGGATAGTGACGGGTACACCTGTTTGGACTGG"
            "TACCTGCAGAAGCCAGGCCAGTCTCCACAGCTCCTGATCTATGAGGTTTCCAACCGGGTC"
            "TCTGGAGTCCCTGACAGGTTCAGTGGCAGTGGGTCAGNCACTGATTTCACACTGAAAATC"
            "AGCCGGGTGGAAGCTGAGGATGTTGGGGTGTATTACTGTATGCAAAGTATAGAGTTTCCT"
            "CC").lower(),
            seq)
        seq_analysis_cat = result["vquest_airr.tsv"].splitlines()[1].split("\t")[118]
        deletions = result["vquest_airr.tsv"].splitlines()[1].split("\t")[123]
        self.assertEqual(seq_analysis_cat, "1 (noindelsearch)")
        self.assertEqual(deletions, "")

    def test_vquest_main(self):
        """Test that the command-line interface gives the expected response."""
        config_path = str((self.path / "config.yml").resolve())
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            main([config_path])
            self.assertTrue(Path("vquest_airr.tsv").exists())
            self.assertTrue(Path("Parameters.txt").exists())

    def test_vquest_main_alignment(self):
        """Try using the --align feature.

        In this case the regular output files should not be created and instead
        FASTA text should be written to stdout.
        """
        expected = """>IGKV2-ACR*02
gacattgtgatgacccagactccactctccctgcccgtcacccctggagagccagcctccatctcctgcaggtctagtcagagcctcttggatagt...gacgggtacacctgtttggactggtacctgcagaagccaggccagtctccacagctcctgatctatgaggtt.....................tccaaccgggtctctggagtccct...gacaggttcagtggcagtggg......tcagncactgatttcacactgaaaatcagccgggtggaagctgaggatgttggggtgtattactgtatgcaaagtatagagtttcctcc
"""
        config_path = str((self.path / "config.yml").resolve())
        out = StringIO()
        err = StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            with tempfile.TemporaryDirectory() as tempdir:
                os.chdir(tempdir)
                main([config_path, "--align"])
                self.assertFalse(Path("vquest_airr.tsv").exists())
                self.assertFalse(Path("Parameters.txt").exists())
        self.assertEqual(out.getvalue(), expected)
        self.assertEqual(err.getvalue(), "")


class TestVquestEmpty(TestVquestSimple):
    """What if no options are given?"""

    def test_vquest(self):
        """Test that an empty config fails as expected."""
        with self.assertRaises(ValueError):
            vquest({})

    def test_vquest_main(self):
        """Test how the command-line interface handles no arguments.

        It should exit with a nonzero exit code and write the help text to
        stdout.
        """
        out = StringIO()
        err = StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            with self.assertRaises(SystemExit):
                with tempfile.TemporaryDirectory() as tempdir:
                    os.chdir(tempdir)
                    main([])
        self.assertNotEqual(out.getvalue(), "")
        self.assertEqual(err.getvalue(), "")

    def test_vquest_main_alignment(self):
        """Try using the --align feature.

        This should error out just like without --align.
        """
        out = StringIO()
        err = StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            with self.assertRaises(SystemExit):
                with tempfile.TemporaryDirectory() as tempdir:
                    os.chdir(tempdir)
                    main(["--align"])
        self.assertNotEqual(out.getvalue(), "")
        self.assertEqual(err.getvalue(), "")


class TestVquestCustom(TestVquestSimple):
    """Try changing one of the configuration options.

    Note that most of the configuration options in the Excel section actually
    don't seem to change the results when AIRR output is selected.  The "Search
    for insertions and deletions in V-REGION" option does change the output
    though.
    """

    def test_vquest(self):
        """We should see a change in Parameters and the AIRR table."""
        config = {
            "species": "rhesus-monkey",
            "receptorOrLocusType": "IG",
            "resultType": "excel",
            "xv_outputtype": 3,
            "v_regionsearchindel": True,
            "sequences": """>IGKV2-ACR*02
GACATTGTGATGACCCAGACTCCACTCTCCCTGCCCGTCACCCCTGGAGAGCCAGCCTCCATCTCCTGCAGGTCTAGTCA
GAGCCTCTTGGATAGTGACGGGTACACCTGTTTGGACTGGTACCTGCAGAAGCCAGGCCAGTCTCCACAGCTCCTGATCT
ATGAGGTTTCCAACCGGGTCTCTGGAGTCCCTGACAGGTTCAGTGGCAGTGGGTCAGNCACTGATTTCACACTGAAAATC
AGCCGGGTGGAAGCTGAGGATGTTGGGGTGTATTACTGTATGCAAAGTATAGAGTTTCCTCC"""}
        result = vquest(config)
        parameters = [("Date", "Wed Dec 02 19:18:14 CET 2020"),
        ("IMGT/V-QUEST program version", "3.5.21"),
        ("IMGT/V-QUEST reference directory release", "202049-2"),
        ("Species", "Macaca mulatta"),
        ("Receptor type or locus", "IG"),
        ("IMGT/V-QUEST reference directory set", "F+ORF+ in-frame P"),
        ("Search for insertions and deletions", "yes"),
        ("Nb of nucleotides to add (or exclude) in 3' "
            "of the V-REGION for the evaluation of the alignment score", "0"),
        ("Nb of nucleotides to exclude in 5' "
            "of the V-REGION for the evaluation of the nb of mutations", "0"),
        ("Analysis of scFv", "no"),
        ("Number of submitted sequences", "1")]
        self.assertEqual(
            "\n".join(["%s\t%s\t" % param for param in parameters]) + "\n\n",
            result["Parameters.txt"])
        seq = result["vquest_airr.tsv"].splitlines()[1].split("\t")[1]
        self.assertEqual(
            ("GACATTGTGATGACCCAGACTCCACTCTCCCTGCCCGTCACCCCTGGAGAGCCAGCCTCC"
            "ATCTCCTGCAGGTCTAGTCAGAGCCTCTTGGATAGTGACGGGTACACCTGTTTGGACTGG"
            "TACCTGCAGAAGCCAGGCCAGTCTCCACAGCTCCTGATCTATGAGGTTTCCAACCGGGTC"
            "TCTGGAGTCCCTGACAGGTTCAGTGGCAGTGGGTCAGNCACTGATTTCACACTGAAAATC"
            "AGCCGGGTGGAAGCTGAGGATGTTGGGGTGTATTACTGTATGCAAAGTATAGAGTTTCCT"
            "CC").lower(),
            seq)
        seq_analysis_cat = result["vquest_airr.tsv"].splitlines()[1].split("\t")[118]
        deletions = result["vquest_airr.tsv"].splitlines()[1].split("\t")[123]
        self.assertEqual(seq_analysis_cat, "2 (indelcorr)")
        self.assertEqual(
            deletions,
            ("in CDR1-IMGT, from codon 33 of V-REGION: 3 nucleotides "
            "(from position 97 in the user submitted sequence), (do not cause frameshift)"))

    def test_vquest_main(self):
        """Try an extra argument given as though on the command line."""
        config_path = str((self.path / "config.yml").resolve())
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            main(["--imgtrefdirset", "1", config_path])
            self.assertTrue(Path("vquest_airr.tsv").exists())
            self.assertTrue(Path("Parameters.txt").exists())


class TestVquestInvalid(TestVquestBase):
    """Test vquest for an invalid request.

    Here the server should return an HTML document with an error message, which
    we should pick up and raise as a VquestError.
    """

    def test_vquest(self):
        """Test that an html file with an error message is parsed correctly."""
        config = {
            "species": "rhesus-monkey",
            "receptorOrLocusType": "antibody", # not valid!
            "resultType": "excel",
            "xv_outputtype": 3,
            "sequences": """>IGKV2-ACR*02
GACATTGTGATGACCCAGACTCCACTCTCCCTGCCCGTCACCCCTGGAGAGCCAGCCTCCATCTCCTGCAGGTCTAGTCA
GAGCCTCTTGGATAGTGACGGGTACACCTGTTTGGACTGGTACCTGCAGAAGCCAGGCCAGTCTCCACAGCTCCTGATCT
ATGAGGTTTCCAACCGGGTCTCTGGAGTCCCTGACAGGTTCAGTGGCAGTGGGTCAGNCACTGATTTCACACTGAAAATC
AGCCGGGTGGAAGCTGAGGATGTTGGGGTGTATTACTGTATGCAAAGTATAGAGTTTCCTCC"""}
        with self.assertRaises(VquestError) as context:
            vquest(config)
        self.assertEqual(
            context.exception.server_messages,
            ["The receptor type or locus is not available for this species"])
        self.assertEqual(self.post.call_count, 1)
        self.assertEqual(
            self.post.call_args.args,
            ('http://www.imgt.org/IMGT_vquest/analysis', ))
