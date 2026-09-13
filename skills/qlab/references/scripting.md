# QLab 5 脚本接口的能力边界（实测清单）

全部实测于 QLab **5.6.3** / macOS 26，2026-08-25。每一条都是花了若干次失败尝试换来的。sdef 路径：`/Applications/QLab.app/Contents/Resources/QLab.sdef` —— **它是唯一的真相来源**，官方文档不写这些。

## AppleScript：能做什么

建 cue 之后这些属性都能设：

| 属性 | 备注 |
|---|---|
| `file target` | 传 `POSIX file "/abs/path"` |
| `q number` / `q name` | 字符串。q number 可以是 `"11F"` 这种非数字 |
| `duration` | Fade cue 的淡出时长，秒（浮点） |
| `cue target` | Fade cue 指向哪个 cue，传 `cue id "<uid>" of first cue list` |
| `stop target when done` | Fade 结束后停掉目标 cue |
| `infinite loop` | 循环播放 |
| `continue mode` | `do_not_continue` / `auto_continue` / `auto_follow` |
| `integrated fade` | 只是**开关**，见下方「内置淡出」 |
| `lock fade to cue` | 开关 |
| `selected` | `set selected to {cue id "..." of first cue list}` |
| 命令 `setLevel <cue> row 0 column 0 db <n>` | **db 到 −60 即静音，−120 会被 floor 到 −60** |

查询用：`get count of cues of first cue list`、`get uniqueID of item 1 of (selected as list)`、`get unique id`（workspace）、`get {name, path, modified}`、`panic`、`delete every cue of first cue list`。

## AppleScript：不能做什么

**`make new cue` 是坏的。** `make` 命令在 sdef 里被注释掉了，`make new cue with properties {q type:"Audio"}` 一定报错。唯一的建 cue 方式是 UI 脚本点 **Cues** 菜单：

```applescript
tell application "System Events" to tell process "QLab" to ¬
  click menu item "Audio" of menu 1 of menu bar item "Cues" of menu bar 1
```

新 cue 落在**当前选中项之后**，并自动成为选中项。所以批量建的循环是：选中上一个 → 点菜单 → 读新 uid。

**保存不要 UI 脚本。** 那个保存 sheet 很不稳，按 Escape 会把整个对话框连带杀掉，Go-to-folder 子面板也会互相干扰。用命令：

```applescript
tell application "QLab" to save document 1 in POSIX file "/abs/path/x.qlab5"
```

## 内置淡出（Integrated fade）：长度改不了

Audio cue **确实有**内置淡出 —— cue 检查器 **Time & Loops** tab 里的 **Integrated fade** 勾选框。内部实现是一个完整的 `Fade` 对象，嵌在 audio cue 的归档键 `playlistOutFade`（和 `playlistInFade`）下，`duration` 默认 **3.0 秒**。

**但它的长度无法用任何方式脚本化设置。** 穷尽验证过：

- QLab 界面里**根本没有这个数值的输入框**。Time & Loops 只暴露 start time、end time、play count、rate 和一个 fade 曲线菜单。长度**只能**在波形图上拖手柄来改。
- AppleScript 只暴露开关 `integrated fade` 和 `lock fade to cue`，没有 duration。
- OSC：`/cue/N/doFade` 和 `/cue/N/lockFadeToCue` 可用；`fadeInDuration`、`fadeOutDuration`、`playlistOutFade`、`sliceMarkers` **全部返回 `error`**。
- 波形上那两个 fade 手柄**没有 accessibility 接口**，脚本点不到也拖不动（用 axdump.js 确认过）。
- 直接改存盘的 `.qlab5`（一个 NSKeyedArchiver plist）原理上可行，但对真实演出文件太脆 —— 默认值不写进归档，缺失的 `Fade` 对象得自己合成出来。

**结论：要精确、可脚本的淡出，就用独立的 Fade cue。** 它还有两个额外好处：由操作员按 GO 触发（而不是在文件末尾自动发生），以及 —— **loop 的 cue 只能用它**，因为 cue 永远到不了结尾，内置淡出永远不会触发。

## OSC

三个坑写在 SKILL.md 里，`scripts/qlab_osc.py` 已经填好。补充：

- **OSC 地址名 = sdef 里的 cocoa key，不是 AppleScript 属性名。** 例：AppleScript `integrated fade` → OSC `/cue/N/doFade`。查表：`grep '<cocoa key=' QLab.sdef`。
- 鉴权是 **per-TCP-connection** 的，每开一个新 socket 都要重发裸 `/connect <passcode>`。
- 可用来 probe 的：`/version`、`/workspaces`、`/alwaysReply`、`/new audio`、`/cue/N/<prop>`。
- 回包是 JSON 字符串塞在 OSC 的 string arg 里，`{"status": "...", "data": ...}`。**`status` 不是 `ok` 时要当错误抛出** —— 否则「权限没拿到」会伪装成「值是 None」，能骗掉很多回合。

## UI 脚本 / 调试

- **`screencapture` 在这些机器上是废的**（没有 Screen Recording 权限，出来是空的）。别浪费回合截图，改成 dump AX 树。
- **JXA（`osascript -l JavaScript`）走 AX 树比 AppleScript 可靠得多。** UI 脚本优先 JXA。
- QLab 的 cue 检查器在 `window[0].uiElements[0].uiElements[2]`。
- 工具：`scripts/axdump.js`（整窗递归 dump）、`scripts/tabdump.js`（点开某个检查器 tab 再 dump）、`scripts/oscaccess.js`（打开 Settings → Network → OSC Access 并 dump，用来读 passcode）。
- 想看 `.qlab5` 里到底存了什么：`cp x.qlab5 /tmp/p.plist && plutil -convert xml1 /tmp/p.plist -o /tmp/p.xml`，然后 grep 键名。也可以 `plistlib.load` 后遍历 `d['$objects']`。
- 找不到某个内部键名时：`strings -a /Applications/QLab.app/Contents/MacOS/QLab | grep -iE '<关键词>' | sort -u`。

## 工作纪律

- **每一步回读验证。** QLab 静默失败很多（尤其是 OSC 权限没拿到时）。建完 cue 数一遍，设完属性读回来对一遍。
- **别在正本工程上试错**，`cp -R` 到 `/tmp` 试。
- **收尾恢复原状**：`panic`、删掉试验 cue、`close document 1 without saving`、清理 `/tmp` 副本。
- 涉及改用户安全设置（比如把 OSC「No Passcode」那行打开）**先问**。
