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
