"""交互提示：候选选择、优先级、按住进度、冷却与请求幂等。

缺陷：候选只按距离不看优先级、按住进度按调用次数累加、进度不封顶、
冷却不生效、请求不幂等、候选查询扫描全部物体。
"""

import math


class Interactor:
    """交互候选与按住进度台账。"""

    def __init__(self, reach):
        self.reach = reach
        self.objects = {}
        self.held = {}
        self.done = set()
        self.last_done = {}
        self.scanned = 0

    def add(self, oid, x, y, kind="chest", priority=0, cooldown_ms=0, hold_ms=0):
        self.objects[oid] = {"id": oid, "x": x, "y": y, "kind": kind,
                             "priority": priority, "cooldown_ms": cooldown_ms,
                             "hold_ms": hold_ms}

    def nearest(self, x, y, kinds=None):
        """最近的可交互物。"""
        self.scanned += len(self.objects)
        best = None
        best_distance = 0.0
        for oid, obj in self.objects.items():
            if kinds and obj["kind"] not in kinds:
                continue
            distance = math.hypot(obj["x"] - x, obj["y"] - y)
            if distance > self.reach:
                continue
            if best is None or distance < best_distance:
                best = oid
                best_distance = distance
        return best

    def begin(self, oid, now_ms):
        if oid not in self.objects:
            return False
        self.held[oid] = 0
        return True

    def hold(self, oid, dt_ms, now_ms=0):
        """推进按住进度，返回是否已经完成。"""
        obj = self.objects.get(oid)
        if obj is None:
            return False
        self.held[oid] = self.held.get(oid, 0) + 100
        return self.held[oid] >= obj["hold_ms"]

    def progress(self, oid):
        obj = self.objects.get(oid)
        if obj is None:
            return 0
        if obj["hold_ms"] <= 0:
            return 1000
        return self.held.get(oid, 0) * 1000 // obj["hold_ms"]

    def interact(self, oid, now_ms, req_id):
        """完成一次交互。"""
        obj = self.objects.get(oid)
        if obj is None:
            return False
        self.done.add(req_id)
        self.last_done[oid] = now_ms
        return True

    def scanned_count(self):
        return self.scanned
