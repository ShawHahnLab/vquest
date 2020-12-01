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
import vquest

class TestVquest(unittest.TestCase):
    """Basic test of vquest."""

    def setUp(self):
        self.case = "basic"
        self.set_up_mock_post()

    def tearDown(self):
        self.tear_down_mock_post()

    def set_up_mock_post(self):
        """Use fake POST request during testing."""
        reqs = sys.modules["requests"]
        reqs.post_real = reqs.post
        response = (
            Path(__file__).parent /
            "data" /
            "tests" /
            (self.case + ".zip"))
        if response.exists():
            with open(response, "rb") as f_in:
                data = f_in.read()
        else:
            data = None
        reqs.post = Mock(return_value=Mock(content=data))
        # for easy access, though it's sys-wide
        self.post = reqs.post

    @staticmethod
    def tear_down_mock_post():
        """Put back original post function after testing."""
        reqs = sys.modules["requests"]
        reqs.post = reqs.post_real

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
        result = vquest.vquest(config)
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

    def test_vquest_main(self):
        """Test that the command-line interface gives the expected response."""
        config_path = str(Path(__file__).parent /
            "data" /
            "tests" /
            (self.case + "_config.yml"))
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            vquest.vquest_main([config_path])
            self.assertTrue(Path("vquest_airr.tsv").exists())
            self.assertTrue(Path("Parameters.txt").exists())


class TestVquestEmpty(TestVquest):
    """What if no options are given?"""

    def setUp(self):
        self.case = "empty"
        self.set_up_mock_post()

    def test_vquest(self):
        """Test that an empty config fails as expected."""
        self.skipTest("not yet implemented")
        vquest.vquest({})

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
                    vquest.vquest_main([])
        self.assertNotEqual(out.getvalue(), "")
        self.assertEqual(err.getvalue(), "")
