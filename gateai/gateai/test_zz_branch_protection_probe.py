"""Deliberately failing test: verifies that branch protection blocks merging. Never merge."""
from django.test import SimpleTestCase


class BranchProtectionProbe(SimpleTestCase):
    def test_this_must_block_the_merge(self):
        self.fail('deliberate failure to verify required checks block merging')
