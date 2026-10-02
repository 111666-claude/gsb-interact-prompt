"""命令行入口：跑交互提示样例。"""

import argparse

from .core import Interactor


def build_parser():
    parser = argparse.ArgumentParser(prog="interact-prompt", description="交互提示")
    parser.add_argument("--sample", default="priority",
                        help="priority / hold / overcap / cooldown / dup / scan")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.sample == "priority":
        world = Interactor(reach=20)
        world.add("a", 5, 0, priority=0)
        world.add("b", 9, 0, priority=5)
        print("pick=%s" % world.nearest(0, 0))
    elif args.sample == "hold":
        world = Interactor(reach=20)
        world.add("a", 1, 0, hold_ms=1000)
        world.begin("a", 0)
        for index in range(5):
            world.hold("a", 150, index * 150)
        print("progress=%d" % world.progress("a"))
    elif args.sample == "overcap":
        world = Interactor(reach=20)
        world.add("a", 1, 0, hold_ms=1000)
        world.begin("a", 0)
        for index in range(20):
            world.hold("a", 150, index * 150)
        print("progress=%d" % world.progress("a"))
    elif args.sample == "cooldown":
        world = Interactor(reach=20)
        world.add("a", 1, 0, cooldown_ms=5000)
        world.interact("a", 0, "r1")
        ok = world.interact("a", 1, "r2")
        print("second=%s" % str(ok).lower())
    elif args.sample == "dup":
        world = Interactor(reach=20)
        world.add("a", 1, 0)
        world.interact("a", 0, "same")
        ok = world.interact("a", 100, "same")
        print("second=%s" % str(ok).lower())
    elif args.sample == "scan":
        world = Interactor(reach=20)
        for index in range(3000):
            world.add("o-%d" % index, index, 0)
        for _ in range(3000):
            world.nearest(0, 0)
        print("scanned=%d" % world.scanned_count())
    else:
        raise SystemExit("需要 --sample priority|hold|overcap|cooldown|dup|scan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
