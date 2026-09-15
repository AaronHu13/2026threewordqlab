# json ↔ QLab 互转手册（给协作者）

一句话：**每幕的真相是 `Act N_ 剧名/qlab_actN_sequence.json`，`.qlab5` 只是它的产物。** 改 cue 顺序、加淡出、改音量，先改 json，再"编译"进 QLab；在 QLab 里手工改了，就"反编译"回 json。两个方向各一条命令，第三条命令校验两边一致。

```
json  ──build_act_into_list.py──▶  QLab 里的 cue list  ──dump_sequence.py──▶  json
                    ▲                                                        │
                    └────────────── verify_sequence.py（diff 两边）◀─────────┘
```

脚本都在 `skills/qlab/scripts/`，下面的命令都假定在仓库根目录（`喜剧节/Audio/`）执行，用 `S=skills/qlab/scripts` 简写。

## 0. 环境（只需一次）

- macOS + QLab 5（免费版够用，实测 5.6.3），Python 3（系统自带即可，不需要第三方库）。
- 脚本靠 AppleScript 建 cue，第一次跑会弹**辅助功能 / 自动化**授权：系统设置 → 隐私与安全性 → 辅助功能，把「终端」（或你跑命令的 App）勾上；另外允许它控制「QLab」和「System Events」。没授权的症状是 `osascript is not allowed assistive access` 或 `-1743`。
- 跑脚本时 **QLab 必须打开且只开一个工程**（脚本操作的是 front workspace）。多开了就 `osascript -e 'tell application "QLab" to close every document saving no'` 再重开目标文件。
- 建 cue 期间不要碰鼠标键盘：脚本在点 QLab 的菜单，抢焦点会建到别的地方。

## 1. json → QLab（编译）

把 json 描述的整幕建进**当前打开工程**里那个同名 cue list：

```bash
open -a QLab "喜剧节2026.qlab5"        # 或某幕的独立工程 "Act 6_ 最后的太阳/Act 6_ 最后的太阳.qlab5"
python3 $S/build_act_into_list.py "Act 6_ 最后的太阳/qlab_act6_sequence.json"
osascript -e 'tell application "QLab" to save document 1 in POSIX file "'"$PWD"'/喜剧节2026.qlab5"'
```

行为：
- 找到 json `list` 字段那个名字的 cue list（名字要一字不差，包括全角冒号和书名号），**把里面原有的 cue 全部替换**为 json 的内容。幂等，可以反复跑。
- 音频文件在 json 的 `folder` 里按编号找：`Cue<N> xxx.mp3` / `<N> xxx.mp3` / `<N>xxx.mp3` 都行，N 唯一。`folder` 写 `"."` 表示 json 自己所在文件夹 —— **永远别写 `/Users/xxx/...` 绝对路径**，别人的机器上没有。
- 每建一条都会读回校验（编号、音量），有问题直接报错停下，不会静默错位。
- 建完的是**未保存状态**，一定要跑第三行保存（或 ⌘S）。别用 UI 脚本点保存对话框。
- 输出末尾 `cues now: N` 应等于 json 的步数。

**什么时候用**：
1. 新拿到一幕的音频 + 文字 cue 表 → 按 `sequence_json.md` 翻译成 json → build。
2. 别人改了 json 并推到 git → 你 pull 下来 → 打开总工程 → build 那一幕 → 保存。这就是"汇总到总工程"，不需要手工跨工程复制 cue。
3. 你改了 json 里的顺序/淡出/音量 → build → 保存 → 提交 json 和 .qlab5。

## 2. QLab → json（反编译）

在 QLab 里手工调过（拖顺序、改淡出秒数、拉推子、改名字、写 notes）之后，把 cue list 导出覆盖 json：

```bash
python3 $S/dump_sequence.py "Act 6:《最后的太阳》" "6_" "Act 6_ 最后的太阳" "Act 6_ 最后的太阳/qlab_act6_sequence.json"
#                            ^ list 名                 ^ 编号前缀  ^ 音频文件夹        ^ 输出（省略则打印到屏幕）
```

行为：
- 逐条读前台工程里那个 list：Audio → `audio`，Fade → `fade`（含秒数、目标音量、是否停），Start/Stop → `start`/`stop`，Memo → `memo`。
- 只写非默认值（0 dB 不写、默认淡出秒数不写、名字等于文件名不写），所以 json 保持可读、diff 干净。
- json 落在音频文件夹内时 `folder` 自动写 `"."`。
- **编号必须符合 `<prefix><N><后缀>`**（`6_12`、`6_12F`、`6_12D`、`6_101`），手工建的 cue 没按这个编号会报 `does not match prefix`。手工加 cue 时照着规则编号。
- 免费版能建的 cue 类型才能往返：Audio / Fade / Group / Start / Stop / Wait / Memo。Group/Wait 目前脚本不支持，会 `warn: skipping`。

导出后 `git diff` 看一眼变了什么，确认是你想要的改动再提交。

## 3. 校验两边一致（提交前必做）

```bash
python3 $S/verify_sequence.py --all .                       # 前台工程 vs 所有幕的 json
python3 $S/verify_sequence.py "Act 6_ 最后的太阳/qlab_act6_sequence.json"   # 只查一幕
```

每幕一行 `✓` 或 `✗` + 差异。**总工程和每幕的独立工程都要各跑一次**（脚本只看前台工程，换一个工程再跑）。有 `✗` 就二选一：json 对 → build；QLab 对 → dump。

## 4. 独立工程 ↔ 总工程

总工程 `喜剧节2026.qlab5` 每幕一个 list；各幕独立工程只含本幕。**独立工程不是手工维护的，是从总工程拆出来的**：

```bash
osascript -e 'tell application "QLab" to close every document saving no'
python3 $S/split_workspace.py "$PWD/喜剧节2026.qlab5" "$PWD" 'Act 6'     # 只拆 Act 6；'Act \d' 拆全部 8 幕
```

所以标准流程是：改 json → build 进总工程 → 保存 → split 拆出该幕 → verify（两个工程各一次）→ 提交 json + 两个 .qlab5。

反过来，如果协作者只在自己那幕的独立工程里手工改：dump 出 json → 提交 json（.qlab5 可一起提交）→ 负责总工程的人 pull 后 build 进总工程 → split。

## 5. 常见报错

| 现象 | 原因 / 处理 |
|---|---|
| `Can't get cue list 1 of workspace 1 whose q name = …` | 前台工程里没有这个 list：多开了别的工程，或 list 名不一字不差 |
| `two files share cue number N` | 文件夹里两份同编号音频，删一份或改编号 |
| `no audio file numbered N` | json 引用的编号在文件夹里没有；子文件夹里的音频要用 `file` 字段 |
| `q number collision: wanted 6_3, QLab gave 10` | 别的 list 里已有同号 cue（通常是旧占位），先清掉那个编号 |
| `-1712` / `-1743` / `not allowed assistive access` | 刚打开工程头几秒 QLab 不理 AppleEvent，等 5 秒重跑；或辅助功能没授权 |
| cue 建到了别的位置 | 建 cue 期间点了鼠标/换了选中项，重跑一次 build（幂等） |
| 红色 missing cue | 音频不在 `folder`，或文件名改了；Inspector → Basics 重新指向，然后 dump 一次 |

## 6. json 长什么样

完整格式、每种步骤的参数、文字 cue 表怎么翻译成步骤，见 `sequence_json.md`。最小例子：

```json
{
  "folder": ".",
  "list": "Act 1:《回来了》",
  "prefix": "1_",
  "fade_seconds": 3,
  "sequence": [
    ["audio", 0, {"name": "0 报幕-回来了（播完）"}],
    ["audio", 1],
    ["audio", 2, {"name": "2 冲水", "notes": "演员进卫生间后 GO"}],
    ["fade", 2, {"name": "手动停 2（3s 淡出）"}],
    ["audio", 3, {"level": -3.0}]
  ]
}
```
