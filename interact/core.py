"""交互提示：候选选择、优先级、按住进度、冷却与请求幂等。

候选先过滤超出 reach 的物体，再按 priority 降序、距离升序、id 字典序
升序取第一个；按住进度按真实毫秒累加并封顶；交互受冷却与请求幂等约束。

候选查询使用以 reach 为格宽的均匀网格（只需检查 3x3 邻格）并缓存
同一参数的查询结果，避免随物体总数线性扫描。
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
        self._cell = reach if reach > 0 else 1
        self._grid = {}
        self._cells = {}
        self._cache = {}

    def add(self, oid, x, y, kind="chest", priority=0, cooldown_ms=0, hold_ms=0):
        if oid in self.objects:
            old = self._cells.pop(oid, None)
            if old is not None:
                bucket = self._grid.get(old)
                if bucket and oid in bucket:
                    bucket.remove(oid)
        self.objects[oid] = {"id": oid, "x": x, "y": y, "kind": kind,
                             "priority": priority, "cooldown_ms": cooldown_ms,
                             "hold_ms": hold_ms}
        cell = self._cell_of(x, y)
        self._cells[oid] = cell
        self._grid.setdefault(cell, set()).add(oid)
        self._cache.clear()

    def _cell_of(self, x, y):
        return (int(math.floor(x / self._cell)), int(math.floor(y / self._cell)))

    def nearest(self, x, y, kinds=None):
        """reach 内按优先级、距离、id 排序的第一个物体。"""
        kind_key = tuple(sorted(kinds)) if kinds else None
        cache_key = (x, y, kind_key)
        if cache_key in self._cache:
            return self._cache[cache_key]

        cx, cy = self._cell_of(x, y)
        best = None
        best_rank = None
        reach_sq = self.reach * self.reach
        grid = self._grid
        objects = self.objects
        scanned = self.scanned
        for gx in (cx - 1, cx, cx + 1):
            for gy in (cy - 1, cy, cy + 1):
                for oid in grid.get((gx, gy), ()):
                    obj = objects[oid]
                    if kinds and obj["kind"] not in kinds:
                        continue
                    scanned += 1
                    dx = obj["x"] - x
                    dy = obj["y"] - y
                    dist_sq = dx * dx + dy * dy
                    if dist_sq > reach_sq:
                        continue
                    rank = (-obj["priority"], dist_sq, oid)
                    if best_rank is None or rank < best_rank:
                        best_rank = rank
                        best = oid
        self.scanned = scanned
        self._cache[cache_key] = best
        return best

    def begin(self, oid, now_ms):
        if oid not in self.objects:
            return False
        self.held[oid] = 0
        return True

    def hold(self, oid, dt_ms, now_ms=0):
        """按真实毫秒推进按住进度，返回是否已经完成。"""
        obj = self.objects.get(oid)
        if obj is None:
            return False
        hold_ms = obj["hold_ms"]
        if hold_ms <= 0:
            return True
        elapsed = min(self.held.get(oid, 0) + dt_ms, hold_ms)
        self.held[oid] = elapsed
        return elapsed >= hold_ms

    def progress(self, oid):
        obj = self.objects.get(oid)
        if obj is None:
            return 0
        if obj["hold_ms"] <= 0:
            return 1000
        return min(self.held.get(oid, 0) * 1000 // obj["hold_ms"], 1000)

    def interact(self, oid, now_ms, req_id):
        """完成一次交互；重复 req_id 或冷却期内返回 False 且不改状态。"""
        obj = self.objects.get(oid)
        if obj is None:
            return False
        if req_id in self.done:
            return False
        last = self.last_done.get(oid)
        if last is not None and now_ms - last < obj["cooldown_ms"]:
            return False
        self.done.add(req_id)
        self.last_done[oid] = now_ms
        return True

    def scanned_count(self):
        return self.scanned
