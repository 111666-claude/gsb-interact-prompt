# interact-prompt

交互提示：候选选择、优先级、按住进度、冷却与请求幂等，只用 Python 标准库。

```
python3 -m interact.cli --sample priority
python3 -m interact.cli --sample hold
python3 -m interact.cli --sample overcap
python3 -m interact.cli --sample cooldown
python3 -m interact.cli --sample dup
python3 -m interact.cli --sample scan
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **候选**：先过滤超出 `reach` 的物体；剩下的按 `priority` 降序、距离升序、
  id 字典序升序取第一个；距离正好等于 `reach` 算在范围内。
- **按住**：`hold_ms` 为 0 时立刻完成；否则进度按真实毫秒累加，封顶 `hold_ms`，
  `progress` 返回 0 到 1000 的整数。
- **冷却**：交互完成后进入 `cooldown_ms`，冷却期内 `interact` 返回 False 且不改状态。
- **幂等**：同一个 `req_id` 只生效一次，重复调用返回 False。
- **不变量**：`progress` 永远不超过 1000；同一串交互序列重复执行结果相同。
- **查询代价**：`nearest` 不许遍历全部物体，`scanned_count` 不随物体数线性增长。
- **规模**：10 万可交互物、每秒 10 万次查询，单次摊还 O(可达范围内物体数)。

## 输出契约（不改格式）

```
pick=..
progress=..
second=..
scanned=..
```

## 目录

```
interact/core.py   候选、进度、冷却与幂等
interact/cli.py    命令行入口
tests/             unittest 用例
```
