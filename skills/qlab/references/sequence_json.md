# 音乐 cue 表 → `qlab_actN_sequence.json`

每一幕的音频文件夹里**必须**有一份 `qlab_actN_sequence.json`（N = 幕号）。它是这一幕 cue list 的唯一文字真相：
`scripts/build_act_into_list.py` 读它建 cue，`scripts/dump_sequence.py` 从 QLab 里把现成的 cue list 反向导出成它。
有了它，"某一幕的独立工程"和"戏剧节总工程"之间就不用靠手工复制 cue 来同步 —— 打开总工程，跑一遍 build 就是汇总。

范例：`喜剧节/Audio/Act 8_ 一幕成名2幕中无人/qlab_act8_sequence.json`（67 步）。

## 文件格式

```json
{
  "folder": ".",                                      // 音频所在文件夹；"." = json 自己所在目录（推荐，换机器也能跑），也可写绝对路径。文件名 "<N>-xxx.mp3" 或 "Cue<N> xxx.mp3"
  "list":   "Act 8:《一幕成名2幕中无人》",          // 总工程里的 cue list q name，必须一字不差
  "prefix": "8_",                                     // q number 前缀：8_1、8_1F、8_37R…
  "fade_seconds": 3,                                  // 手动停的默认淡出秒数
  "sequence": [ ...一步一行，按 GO 顺序... ]
}
```

`sequence` 每一步是 `["类型", N, {可选参数}]`，N 永远是**音频编号**（Fade/Start/Stop 的 N 是它作用的那条音频）：

| 类型 | 生成的 cue | q number | 可选参数 |
|---|---|---|---|
| `audio` | Audio cue，文件 = folder 里编号 N 的那个 | `<prefix>N` | `name`（默认文件名）、`notes`、`cont`、`level`（主推子 dB，默认 0）、`file`（相对 folder 的路径，给子文件夹里的音频用，此时 N 自己指定即可，如旁白用 101、102…） |
| `fade` | Fade cue，目标 `<prefix>N`，默认淡到 −120 dB 并 stop target when done | `<prefix>N` + `suffix`（默认 `F`） | `secs`（默认 fade_seconds）、`cont`、`suffix`、`name`、`notes`、`level`（目标 dB，默认 −120）、`stop`（默认 true；`false` = 只压低不停） |
| `start` | Start cue，目标 `<prefix>N`（暂停后续播） | `<prefix>N` + `suffix`（默认 `R`） | `cont`、`suffix`、`name`、`notes` |
| `stop` | Stop cue | `<prefix>N` + `suffix`（默认 `S`） | 同上 |
| `memo` | Memo cue，GO 无动作，纯占位 | `<prefix>N` + `suffix`（默认 `M`） | `suffix`、`name`、`notes` |
| `pause` | Pause cue —— **免费版是 broken 的，不要用** | `<prefix>N` + `P` | 同 start |

`cont` 取值：`do_not_continue`（默认）/ `auto_continue` / `auto_follow`。
同一条音频可以有多条 fade，用 `suffix` 区分（`F`、`F2`…），否则撞号。

## 翻译规则：剧组给的文字描述 → 步骤

剧组的音乐序列通常是一行一条：「N 曲名 —— 播放至完毕 / 手动停 / 与 N+1 无缝衔接 / 暂停后继续 / 与 X 重叠 / fade out」。逐行翻译，**保证 GO 次数和剧本描述一一对应**，音控看着剧本数 GO 就不会错位：

| 文字描述 | 步骤 | 说明 |
|---|---|---|
| 播放至完毕 / 播完 | `["audio", N]` | 一条，自然结束 |
| 手动停 / 导演喊停 | `["audio", N]`, `["fade", N, {"name": "手动停 N（3s 淡出）"}]` | 一次 GO 淡出并停 |
| fade out 结束 | 同「手动停」，`secs` 按要求 | 免费版 Audio cue 内置淡出长度脚本设不了，只能用 Fade cue |
| 与 N+1 无缝衔接 / N+1 起这个就停 | `["audio", N]`, `["fade", N, {"secs": 1, "cont": "auto_continue", "name": "停 N → 接 N+1（一次 GO）"}]`, `["audio", N+1]` | Fade 带 auto_continue，一次 GO 同时起下一条 |
| 暂停 → 继续（免费版） | `["audio", N, {"name": "N-xx ▶ 到点按 [ 暂停"}]`, `["memo", N, {"suffix": "P", "name": "⏸ N 暂停 = 按 [ 键"}]`, `["start", N, {"name": "N 续播"}]` | 暂停靠键盘 `[`（Pause All），Memo 只是对齐 GO 次数，Start 打在暂停中的 cue 上从暂停点续播 |
| 与 X、Y 重叠 | `["audio", N, {"notes": "与 X、Y 重叠"}]`, `["audio", X]`, `["audio", Y]`, 需要停 N 时再 `["fade", N]` | 什么都不做就是重叠，写进 notes 提醒 |
| 循环 | `["audio", N, ...]` + 建完手动 `set infinite loop`，或用 `loops` 字段 | 循环的 cue 只能靠 Fade cue 停 |
| 描述互相矛盾（既说无缝衔接又说手动停） | 按无缝衔接做，再补一条 `["fade", N, {"suffix": "F2", "name": "手动停 N（备用，通常无动作）"}]` | 保住 GO 次数一致，并在交付时向用户点出这处歧义 |
| 播放中把音量压低 X%（音乐不停） | `["fade", N, {"suffix": "D", "level": 20*log10(1-X/100), "stop": false, "secs": 2}]` | 30% → `-3.1`，35% → `-3.7`，40% → `-4.4`。`stop: false` 让 Fade 只改音量不停 cue；后面照常再放一条 `["fade", N]` 手动停。要「B 起时 A 自动压低」就给 B 的 audio 加 `cont: auto_continue`，紧跟这条 duck fade（Act 6 的 6_19 → 6_18D） |
| 音量调到 X%（百分比） | `["audio", N, {"level": 20*log10(X/100)}]` | `level` 是主推子 dB，百分比是线性振幅：150% → `20*log10(1.5) ≈ 3.5`，50% → `20*log10(0.5) ≈ -6.0`。`dump_sequence.py` 会把手动在 QLab 里调过的 level 原样导出回 json，所以改完记得导出一次，别让下次重建把它冲掉 |

其他约定：
- **每幕第一步是报幕** `["audio", 0, {"name": "0 报幕-<剧名>（…播完）"}]`：把 `报幕/…/合成/报幕-<剧名>.mp3` 复制成该幕文件夹里的 `0 报幕-<剧名>.mp3`，编号 0 → `<prefix>0`。
- `name` 用中文写清**这一 GO 干什么**（"停 26 → 接 27 揭秘（一次 GO）"），音控在 QLab 里看到的就是它。
- `notes` 写操作提醒（按哪个键、为什么这条 GO 无动作）。
- 文件名里的编号必须唯一；有两份同号音频先让用户二选一，`files()` 会直接报错。

## 工作流：什么时候生成、怎么用

1. **拿到文字 cue 表 → 先写 json，再建 cue。** 写好放到该幕的音频文件夹，再 `python3 scripts/build_act_into_list.py <json>`。
2. **cue 是在 QLab 里手工建的或手工改过 →** 打开那个工程，`python3 scripts/dump_sequence.py "<list 名>" "<prefix>" "<音频文件夹>" "<音频文件夹>/qlab_actN_sequence.json"` 把最终状态导出覆盖。改完 cue 就导出，json 和 .qlab5 永远一致。
3. **每一幕做完，交付前检查：**该幕文件夹里有 json、json 步数 = cue list 里的 cue 数、`dump_sequence.py` 输出和文件一致（可以 dump 到 `/tmp` 再 diff）。
4. **汇总到戏剧节总工程：**打开总工程，确认 list 名、prefix 和 json 里的一致，跑 build。build 会清掉该 list 里原有 cue 的编号、新建、校验、删旧的，所以是幂等的，可以反复跑。
5. json 是文本，能进 git、能 diff、能合并；`.qlab5` 不能。所以**多人协作时冲突解决的单位是 json，不是 .qlab5**：谁的 json 对就以谁的为准重建。
