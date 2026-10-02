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


class CandidateTest(unittest.TestCase):
    def test_higher_priority_beats_closer_distance(self):
        world = Interactor(reach=20)
        world.add("a", 5, 0, priority=0)
        world.add("b", 9, 0, priority=5)
        self.assertEqual(world.nearest(0, 0), "b")

    def test_same_priority_picks_nearest(self):
        world = Interactor(reach=20)
        world.add("far", 9, 0, priority=1)
        world.add("near", 4, 0, priority=1)
        self.assertEqual(world.nearest(0, 0), "near")

    def test_distance_tie_breaks_by_id(self):
        world = Interactor(reach=20)
        world.add("b", 5, 0)
        world.add("a", -5, 0)
        self.assertEqual(world.nearest(0, 0), "a")

    def test_distance_equal_to_reach_is_in_range(self):
        world = Interactor(reach=20)
        world.add("edge", 20, 0)
        self.assertEqual(world.nearest(0, 0), "edge")

    def test_kind_filter_still_applies(self):
        world = Interactor(reach=20)
        world.add("chest", 5, 0, kind="chest", priority=9)
        world.add("barrel", 6, 0, kind="barrel", priority=0)
        self.assertEqual(world.nearest(0, 0, kinds={"barrel"}), "barrel")


class HoldTest(unittest.TestCase):
    def test_zero_hold_ms_completes_immediately(self):
        world = Interactor(reach=20)
        world.add("a", 1, 0, hold_ms=0)
        world.begin("a", 0)
        self.assertTrue(world.hold("a", 0, 0))
        self.assertEqual(world.progress("a"), 1000)

    def test_progress_accumulates_real_milliseconds(self):
        world = Interactor(reach=20)
        world.add("a", 1, 0, hold_ms=1000)
        world.begin("a", 0)
        for index in range(5):
            self.assertFalse(world.hold("a", 150, index * 150))
        self.assertEqual(world.progress("a"), 750)

    def test_progress_never_exceeds_1000(self):
        world = Interactor(reach=20)
        world.add("a", 1, 0, hold_ms=1000)
        world.begin("a", 0)
        for index in range(20):
            world.hold("a", 150, index * 150)
        self.assertEqual(world.progress("a"), 1000)

    def test_hold_reports_completion_at_hold_ms(self):
        world = Interactor(reach=20)
        world.add("a", 1, 0, hold_ms=300)
        world.begin("a", 0)
        self.assertFalse(world.hold("a", 100, 0))
        self.assertFalse(world.hold("a", 100, 100))
        self.assertTrue(world.hold("a", 100, 200))


class CooldownTest(unittest.TestCase):
    def test_interact_during_cooldown_fails(self):
        world = Interactor(reach=20)
        world.add("a", 1, 0, cooldown_ms=5000)
        self.assertTrue(world.interact("a", 0, "r1"))
        self.assertFalse(world.interact("a", 4999, "r2"))

    def test_interact_after_cooldown_succeeds(self):
        world = Interactor(reach=20)
        world.add("a", 1, 0, cooldown_ms=5000)
        self.assertTrue(world.interact("a", 0, "r1"))
        self.assertTrue(world.interact("a", 5000, "r2"))

    def test_failed_interact_does_not_change_state(self):
        world = Interactor(reach=20)
        world.add("a", 1, 0, cooldown_ms=5000)
        self.assertTrue(world.interact("a", 0, "r1"))
        self.assertFalse(world.interact("a", 100, "r2"))
        self.assertTrue(world.interact("a", 5000, "r2"))


class IdempotencyTest(unittest.TestCase):
    def test_same_req_id_only_applies_once(self):
        world = Interactor(reach=20)
        world.add("a", 1, 0)
        self.assertTrue(world.interact("a", 0, "same"))
        self.assertFalse(world.interact("a", 100, "same"))

    def test_different_req_id_applies(self):
        world = Interactor(reach=20)
        world.add("a", 1, 0)
        self.assertTrue(world.interact("a", 0, "r1"))
        self.assertTrue(world.interact("a", 100, "r2"))


class ScanCostTest(unittest.TestCase):
    def test_nearest_stays_correct_over_many_objects(self):
        world = Interactor(reach=20)
        for index in range(3000):
            world.add("o-%d" % index, index, 0)
        self.assertEqual(world.nearest(0, 0), "o-0")

    def test_scanned_does_not_grow_with_object_count(self):
        world = Interactor(reach=20)
        for index in range(3000):
            world.add("o-%d" % index, index, 0)
        for _ in range(100):
            world.nearest(0, 0)
        self.assertLessEqual(world.scanned_count(), 200)


if __name__ == "__main__":
    unittest.main()
