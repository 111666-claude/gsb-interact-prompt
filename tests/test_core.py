import unittest

from interact.core import Interactor


class BasicTest(unittest.TestCase):
    def test_empty_world_has_no_candidate(self):
        self.assertIsNone(Interactor(20).nearest(0, 0))

    def test_out_of_reach_is_not_a_candidate(self):
        world = Interactor(reach=5)
        world.add("a", 100, 0)
        self.assertIsNone(world.nearest(0, 0))

    def test_in_reach_is_a_candidate(self):
        world = Interactor(reach=20)
        world.add("a", 3, 0)
        self.assertEqual(world.nearest(0, 0), "a")

    def test_begin_unknown_object_fails(self):
        self.assertFalse(Interactor(20).begin("ghost", 0))

    def test_progress_of_unknown_object_is_zero(self):
        self.assertEqual(Interactor(20).progress("ghost"), 0)

    def test_scanned_starts_at_zero(self):
        self.assertEqual(Interactor(20).scanned_count(), 0)


if __name__ == "__main__":
    unittest.main()
