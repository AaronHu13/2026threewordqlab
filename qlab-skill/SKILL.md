---
name: qlab
description: |
  用脚本驱动 macOS 上的 QLab 5 做演出音效工程：批量把一个文件夹的音频建成 cue list、加 fade out、设 loop / continue mode、改音量、保存工程、打包迁移给别人。当用户说"帮我连 QLab""把这些音效做成一个 QLab 工程""给每个 cue 加淡出""QLab 怎么保存 / 怎么发给别人 / 换机没声音""用 OSC 控制 QLab""QLab cue 是红的"，或任何涉及 .qlab5 工程文件、cue、fade、OSC 53000 的任务时，用本 skill。沉淀自 2026-08 用 QLab 5.6.3 做「Act 6 最后的太阳」26 个 cue 的实战，里面每一条都是踩过坑换来的，能省掉几十次失败尝试。
---

# QLab 5 脚本化（qlab）

QLab 有两套控制面：**AppleScript**（改属性稳）和 **OSC**（查状态、跑通道），两套都有洞。核心心法：**建 cue 用 UI 脚本点菜单，改属性用 AppleScript，查状态用 OSC，保存用 AppleScript 的 `save ... in POSIX file`。** 别指望任何一套单独搞定。

先确认版本：`defaults read /Applications/QLab.app/Contents/Info.plist CFBundleShortVersionString`。下面所有结论在 **5.6.3** 上实测通过。

## 起手式

1. `open -a QLab; sleep 6`，再 `osascript -e 'tell application "QLab" to get name of every document'` 确认有 workspace 打开；没有就让用户先打开或新建。
2. 拿 workspace id：`tell application "QLab" to tell front workspace to get unique id`。
3. **需要 OSC 才连 OSC**（查 broken cue、读属性、远程控制）。纯建工程用 AppleScript 就够，不用碰 OSC 那堆坑。
4. 动用户的现有工程前，先 `cp -R` 一份到 `/tmp` 试，别在正本上试错。

## 建 cue：`make new cue` 是坏的

`make` 命令在 `/Applications/QLab.app/Contents/Resources/QLab.sdef` 里被注释掉了，`make new cue with properties {...}` 一定报错。**唯一可行的建 cue 方式是 UI 脚本点 Cues 菜单**：

```applescript
tell application "System Events" to tell process "QLab" to ¬
  click menu item "Audio" of menu 1 of menu bar item "Cues" of menu bar 1
```

新 cue 落在**当前选中项之后**并自动变成选中项，所以批量建的套路是：`select(上一个 uid)` → 点菜单 → 读 `uniqueID of item 1 of (selected as list)`。菜单项名就是 cue 类型名：`Audio`、`Fade`、`Group`、`Wait`…

**免费模式下能用的 cue 类型**（QLab 5.6.3 无授权实测）：Audio、Fade、Group、Start、Stop、Wait、Memo 正常；**Pause、Script、Network、Devamp 建出来就 broken**，Status 窗口写的是 "License required. Install a license of any kind"。需要『暂停再续播』时的免费替代方案（已实测可用）：

- 暂停用工作区快捷键 **`[` = Pause All**、**`]` = Resume All**、**`P` = 暂停/续播选中 cue**（默认键位存在 .qlab5 的 keyCommands 里，可用 plistlib 解出来）。
- 续播用 **Start cue 打在暂停中的目标上，会从暂停点继续**（实测暂停在 3.03s，Start 后 2s 走到 5.05s），所以 cue list 里可以保留一条 Start cue 当"续播"的 GO。
- "A 停、B 同时起"用 Stop cue + `continue mode` = `auto_continue` 紧跟 B。

**UI 脚本别点带子菜单的菜单项**：`click menu item "Workspace Settings" of menu 1 of menu bar item "File"` 这种带子菜单的项，AX 会把子菜单撑开并进入 NSMenuTrackingSession，QLab 主线程卡在菜单循环里，AppleEvent 全部 -1712 超时，System Events 看不到任何窗口，Escape（System Events 和 CGEvent 两种都试过）都救不回来，只能 `kill -9` 重开。先 `sample QLab 1 | grep NSMenuTrackingSession` 确诊。工作区设置改用 plistlib 读 .qlab5 或直接 AppleScript 属性。

建完就能正常设属性了，可用的有：`file target`（POSIX file）、`q number`、`q name`、`duration`、`cue target`、`stop target when done`、`infinite loop`、`continue mode`（`do_not_continue` / `auto_continue` / `auto_follow`）、以及命令 `setLevel <cue> row 0 column 0 db <n>`（**db 到 −60 就是静音，−120 会被 floor**）。

**`q number` 撞号会被静默改掉**：如果工程里已有同号 cue（哪怕在别的 cue list、哪怕是待删的占位 cue），`set q number` 不报错，但 QLab 会给一个别的号（实测给了 10/13/14…）。所以要先删占位再设号，或者设完立刻读回来对一遍。

`scripts/build_workspace.py` 是一个能直接改的模板：扫文件夹里的 `Cue<N>：xxx.mp3` → 每个建 Audio cue → 紧跟一个 1 秒 Fade out cue，支持 loop 和交叠序列。**改 `FOLDER` 和 `main()` 里的编排就能用。**

## Fade：cue 内置淡出的长度改不了

Audio cue **确实有**内置淡出（Time & Loops 检查器里的 **Integrated fade** 勾选框），但它的**长度只能在波形图上拖，脚本完全设不了** —— AppleScript 只暴露开关（`integrated fade`）和 `lock fade to cue`，OSC 的 `fadeInDuration` / `fadeOutDuration` / `playlistOutFade` 全返回 `error`，波形上那两个 fade 手柄没有 accessibility 接口，点不到也拖不动。详见 `references/scripting.md`。

**所以要精确、可脚本的淡出，就用独立的 Fade cue**（`duration` + `stop target when done` + `setLevel … db -120`）。而且 loop 的 cue 只能用 Fade cue —— 内置淡出永远不触发，因为 cue 永远到不了结尾。

## OSC：三个必踩的坑

要用 OSC 就直接 `scripts/qlab_osc.py`，它已经把坑填好了：

```python
from qlab_osc import QLab
q = QLab(workspace="<uuid>", passcode=1234)      # 建连接即完成鉴权
print(q.send("/cue/1/duration"))
```

坑本身（自己写客户端时必知）：

1. **必须走 TCP，不能 UDP。** 53000 端口两个都收，但 UDP 的回包永远不会到。TCP 上是 F53OSC 的 SLIP 分帧：`0xC0` 分界，转义 `0xDB 0xDC` / `0xDB 0xDD`。
2. **`/connect` 必须不带 workspace 前缀发。** 发 `/workspace/<id>/connect <passcode>` 会返回 `"ok:"` 但**没有任何权限**，之后每条命令都静默 `status: denied`；发裸的 `/connect <passcode>` 才返回 `"ok:view|edit|control"`。鉴权是 per-TCP-connection 的，每开一个 socket 都要重新连。
3. **passcode 是必需的，而且要现读不要硬编码。** Workspace Settings → Network → OSC Access 里有两行：「No Passcode」那行 View/Edit/Control 全是关的，4 位密码那行全是开的。**从那个面板读当前工程的密码**（`scripts/oscaccess.js` 能 dump 出来），不同工程不一样。**不要擅自把「No Passcode」那行打开** —— 那是改用户的安全设置，先问。

翻译 AppleScript 属性名 → OSC 地址名的诀窍：OSC 用的是 sdef 里的 **cocoa key**，不是 AppleScript 属性名（`integrated fade` → `/cue/N/doFade`）。`grep '<cocoa key=' /Applications/QLab.app/Contents/Resources/QLab.sdef` 查表。

## 保存

**别 UI 脚本点保存对话框** —— 那个 sheet 很不稳，Escape 会把整个对话框连带杀掉。直接：

```applescript
tell application "QLab" to save document 1 in POSIX file "/path/to/x.qlab5"
```

## 交付与迁移

一句话规矩：**一场戏一个文件夹，`.qlab5` 和所有音频都塞在里面，整个文件夹打 zip 发过去。** `.qlab5` 里存的是路径引用（几百 KB），但 QLab 会做相对路径恢复，同文件夹内的素材搬到任何位置都能自动找回（实测 26 cue 拷到 `/tmp` 打开，0 broken）。换机没声音的头号原因不是路径而是**音频输出设备**。完整的交付清单、换机 checklist、版本兼容和授权范围见 `references/packaging.md` —— 用户问到迁移就读它。

## 看不见界面时怎么调试

这台机器**没有屏幕录制权限，`screencapture` 是废的**，别浪费回合去截图。改成 dump accessibility 树：

- `scripts/axdump.js` —— 递归打印某个 app 窗口的 AX 树：`osascript -l JavaScript scripts/axdump.js QLab 6 1`
- `scripts/tabdump.js` —— 点开检查器的某个 tab 再 dump：`osascript -l JavaScript scripts/tabdump.js "Time & Loops"`

**JXA（`osascript -l JavaScript`）走 AX 树比 AppleScript 可靠得多**，UI 脚本优先用 JXA。QLab 的 cue 检查器在 `window[0].uiElements[0].uiElements[2]`。

## 工作习惯

- 每一步都回读验证：建完 cue 就 `get count of cues of first cue list`，设完属性就读回来对一遍。QLab 的静默失败很多。
- 遇到"某个属性到底能不能设"，**去翻 sdef 而不是猜**：`grep -n 'property name=' QLab.sdef`。sdef 是唯一的真相来源，QLab 官方文档不写这些。
- 排查完记得把工程恢复原状（`panic`、删掉试验 cue、`close document 1 without saving`），别留脏状态给用户。
