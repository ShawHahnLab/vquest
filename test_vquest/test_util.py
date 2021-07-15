"""
Test util functions.
"""

import unittest
from vquest import util

class TestChunker(unittest.TestCase):
    """Basic test of iterator chunker."""

    def test_chunker(self):
        """Test that chunker breaks iterator items into fixed-size chunks."""
        chunks = []
        for chunk in util.chunker(range(8), 5):
            chunks.append(chunk)
        self.assertEqual([[0, 1, 2, 3, 4], [5, 6, 7]], chunks)

class TestChunkerPerfectFit(unittest.TestCase):
    """Test chunker for a perfect fit, with number of items equal to chunk size."""

    def test_chunker(self):
        """Test that chunker gives only one chunk for the perfect-fit case."""
        chunks = []
        for chunk in util.chunker(range(5), 5):
            chunks.append(chunk)
        self.assertEqual([[0, 1, 2, 3, 4]], chunks)

class TestUnzip(unittest.TestCase):
    """Basic test of the unzip helper."""

    def test_unzip(self):
        """Test that binary ZIP data with an empty file can be extracted."""
        self.assertEqual(
            util.unzip(bytes.fromhex(
                "504b03040a0000000000ab6c"
                "ef5200000000000000000000"
                "000008001c00746573742e64"
                "617455540900035272f06052"
                "72f06075780b000104e90300"
                "0004e9030000504b01021e03"
                "0a0000000000ab6cef520000"
                "000000000000000000000800"
                "18000000000000000000b481"
                "00000000746573742e646174"
                "55540500035272f06075780b"
                "000104e903000004e9030000"
                "504b05060000000001000100"
                "4e000000420000000000")),
            {"test.dat": b""})

class TestAirrToFasta(unittest.TestCase):
    """Basic test of the airr_to_fastas helper."""

    def test_airr_to_fasta(self):
        """Test that FASTA is generated from AIRR TSV."""
        expected = ">1\nACTG\n>2\nCGTA\n"
        observed = util.airr_to_fasta(
            "sequence_id\tsequence\tsequence_alignment\n"
            "1\tACTG\tACTG\n"
            "2\t\tCGTA\n")
        self.assertEqual(observed, expected)
