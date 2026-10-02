"""交互提示：候选选择、优先级、按住进度、冷却与请求幂等。

口径见 README：候选先过滤超出 reach 的物体，再按 priority 降序、距离升序、
id 字典序取第一个；按住进度按真实毫秒累加并封顶 hold_ms；交互完成后进入
cooldown_ms，冷却期内 interact 返回 False 且不改状态；同一个 req_id 只
生效一次。nearest 使用空间网格（格边长等于 reach，一次查询只碰 3x3 格），
格内按 priority 分组、组内按 x 排序做二分定位与由近及远扩展，scanned_count
只统计真正计算距离的物体，单次摊还 O(可达范围内物体数)，不随物体总数增长。
"""

import bisect
import math


class Interactor:
    """交互候选与按住进度台账。"""

    def __init__(self, reach):
        self.reach = reach
        self._cell_size = reach if reach > 0 else 1.0
        self.objects = {}
        self._cells = {}
        self.held = {}
        self.done = set()
        self.last_done = {}
        self.scanned = 0

    def add(self, oid, x, y, kind="chest", priority=0, cooldown_ms=0, hold_ms=0):
        self.objects[oid] = {"id": oid, "x": x, "y": y, "kind": kind,
                             "priority": priority, "cooldown_ms": cooldown_ms,
                             "hold_ms": hold_ms}
        cell = self._cells.setdefault(
            (math.floor(x / self._cell_size), math.floor(y / self._cell_size)),
            {"order": [], "levels": {}})
        level = cell["levels"].get(priority)
        if level is None:
            level = ([], [])
            cell["levels"][priority] = level
            bisect.insort(cell["order"], priority)
        xs, ids = level
        pos = bisect.bisect_left(xs, x)
        xs.insert(pos, x)
        ids.insert(pos, oid)

    def nearest(self, x, y, kinds=None):
        """可达范围内 priority 最高、距离最近、id 最小的物体。"""
        size = self._cell_size
        cx0 = math.floor((x - self.reach) / size)
        cx1 = math.floor((x + self.reach) / size)
        cy0 = math.floor((y - self.reach) / size)
        cy1 = math.floor((y + self.reach) / size)
        cells = []
        priorities = set()
        for cx in range(cx0, cx1 + 1):
            for cy in range(cy0, cy1 + 1):
                cell = self._cells.get((cx, cy))
                if cell is not None:
                    cells.append((cx, cy, cell))
                    priorities.update(cell["order"])
        for priority in sorted(priorities, reverse=True):
            candidates = []
            for cx, cy, cell in cells:
                if priority not in cell["levels"]:
                    continue
                min_dx = max(cx * size - x, 0.0, x - (cx + 1) * size)
                min_dy = max(cy * size - y, 0.0, y - (cy + 1) * size)
                candidates.append((math.hypot(min_dx, min_dy), cell))
            candidates.sort(key=lambda item: item[0])
            best_dist = None
            best_id = None
            for min_dist, cell in candidates:
                if best_dist is not None and min_dist > best_dist:
                    break
                xs, ids = cell["levels"][priority]
                lo = bisect.bisect_left(xs, x - self.reach)
                hi = bisect.bisect_right(xs, x + self.reach)
                left = bisect.bisect_left(xs, x) - 1
                right = left + 1
                while left >= lo or right < hi:
                    if left < lo:
                        index = right
                        right += 1
                    elif right >= hi:
                        index = left
                        left -= 1
                    elif x - xs[left] <= xs[right] - x:
                        index = left
                        left -= 1
                    else:
                        index = right
                        right += 1
                    if best_dist is not None and abs(xs[index] - x) > best_dist:
                        break
                    oid = ids[index]
                    obj = self.objects[oid]
                    if kinds and obj["kind"] not in kinds:
                        continue
                    self.scanned += 1
                    distance = math.hypot(xs[index] - x, obj["y"] - y)
                    if distance > self.reach:
                        continue
                    if (best_dist is None or distance < best_dist
                            or (distance == best_dist and oid < best_id)):
                        best_dist = distance
                        best_id = oid
            if best_id is not None:
                return best_id
        return None

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
        if obj["hold_ms"] <= 0:
            return True
        self.held[oid] = min(self.held.get(oid, 0) + dt_ms, obj["hold_ms"])
        return self.held[oid] >= obj["hold_ms"]

    def progress(self, oid):
        obj = self.objects.get(oid)
        if obj is None:
            return 0
        if obj["hold_ms"] <= 0:
            return 1000
        value = self.held.get(oid, 0) * 1000 // obj["hold_ms"]
        return max(0, min(1000, value))

    def interact(self, oid, now_ms, req_id):
        """完成一次交互；冷却期内或重复 req_id 返回 False 且不改状态。"""
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
