---
name: keynote
description: |
  用脚本驱动 macOS 上的 Keynote 给演出用的 PPT 加音效和动效：往指定页插入音频、设成翻到该页自动播放、让 GIF / 视频只播一次不循环、改音量、保存。当用户说"把这个音频加到 keynote 第 N 页""一翻到这页音效就出来""动画放完一次就定住别再动""Keynote 卡死了""Keynote 怎么用脚本改"，或任何涉及 .key 文件、幻灯片音频、自动播放、循环播放的任务时，用本 skill。沉淀自 2026-09-12 给「喜剧节 2026 背景」27 页 Keynote 第 15 页加音效的实战：AppleScript 能读不能建、一条命令让 Keynote 主线程死锁、System Events 的 click 在 Keynote 里是空的、新插的音频默认要点一下才播。
---

# Keynote 脚本化（keynote）

Keynote 的 AppleScript 字典**读得多、写得少、建媒体对象会死锁**。核心心法：**查状态、改循环、翻页、保存用 AppleScript；插入媒体用 UI 脚本点「插入 › 选取…」；改"自动播放"这种检查器里的勾只能用 CGEvent 点坐标 + 截图确认。** 用户往往在旁边同时用别的 app，所有 UI 操作都要短、原子、点之前先确认 Keynote 在前台。

下面所有结论在 **Keynote 14.x / macOS 26（Darwin 25.6）** 上实测通过。

## 起手式

1. 确认文件在：`ls -la <path.key>`；音频用 `afinfo <wav>` 看时长和声道。
2. 打开并翻到目标页（AppleScript，稳）：

```applescript
tell application "Keynote"
  set theDoc to open (POSIX file "/path/to/x.key")
  set current slide of theDoc to slide 15 of theDoc
  count of slides of theDoc
end tell
```

3. 先用 `scripts/media_info.applescript <页号>` 看这页已有什么：`iWork items` 的类会是 `image` / `movie` / `audio clip`。**GIF 是 `movie` 类**，不是 image。
4. 动用户文件前不用备份 —— Keynote 自动保存 + 版本历史，但一切改动都要最后 `save document 1` 落盘，并看 `modified of document 1` 变回 false。

## 死锁：`make new audio clip` 会把 Keynote 卡死

字典里 `audio clip` / `movie` 的 `file name` 标着 rw，但**只有 `image` 类支持 `make new image with properties {file: ...}`**。执行

```applescript
make new audio clip at end of iWork items of s with properties {file name: POSIX file "..."}
```

Keynote 主线程会卡在 `NSCreateCommand → setValue:forKey: → _dispatch_semaphore_wait_slow` 上，之后**所有 AppleEvent 都 -1712 超时，连 `activate` 都超时**，System Events 看不到任何窗口，永远不会自己恢复。

- 确诊：`sample Keynote 2 -mayDie | grep -A30 "Call graph"`，看到 `semaphore_wait_trap` 挂在 `NSCreateCommand` 下面就是它。
- 唯一出路：`kill -9 $(pgrep -x Keynote)`，重开文档。Keynote 有自动保存，损失极小，但要告诉用户。
- 结论：**不要用 AppleScript 建音频 / 视频对象**，用下面的 UI 流程。

## 插音频：走「插入 › 选取…」菜单

`scripts/insert_audio.applescript <页号> <音频绝对路径>` 封装了整套流程；手动做的话要点是：

1. `set current slide` 到目标页，`activate`，System Events 里 `set frontmost to true`。
2. 点 `menu item "Choose..." of menu 1 of menu bar item 5 of menu bar 1`（Insert 菜单是第 5 个 menu bar item；英文界面下叫 `Choose...`，三个点是普通句点）。
3. 打开的 Open panel 是**远程视图，AX 里 `sheet 1` 下没有任何 button**，别指望 `click button "Insert"`。用键盘：`⌘⇧G` → 输入**完整文件路径**（含文件名）→ `return`。实测两种结果都出现过：一次直接插入成功；一次只是选中了文件，此时再按 `return` 会**进入重命名模式**而不是插入。所以按完第一个 return 后**用 AppleScript 读 `count of audio clips of slide N`** 判断：涨了就成功；没涨且 sheet 还在，就按一次 `escape`（只退重命名，不关面板）再 CGEvent 点 Insert 按钮。
4. 成功后读回属性：`file name`、`clip volume`（0–100）、`repetition method`。**`position of ac as text` 会报 -1700**，要 `set p to position of ac` 再 `item 1 of p`。

**新插入音频的默认值**（一定要告诉用户，否则"翻到这页没声音"）：

| 设置 | 默认 | 含义 |
|---|---|---|
| Start audio on click | **勾选** | 要点一下才播 → 想自动播必须取消 |
| Play audio across slides | 勾选 | 没放完翻页也继续播 |
| Repeat | None | 不循环 |
| Volume | 100 | |

`Start audio on click` **AppleScript 完全碰不到**，只能在 Format › Audio 检查器里点掉，见下一节。

## 改检查器里的勾：CGEvent 点坐标，不是 System Events

**`tell process "Keynote" to click at {x, y}` 在 Keynote 里是空操作** —— 返回正常但什么都没发生（Insert 按钮、对象列表行、检查器 tab 都试过）。必须用 CoreGraphics 发真鼠标事件，`scripts/click.js` 就是干这个的：

```bash
osascript -l JavaScript scripts/click.js 1264 500          # 点一个点
osascript -l JavaScript scripts/click.js 945 283 1003 575  # 连点两个点，每点间隔 1s
```

它会先 `activate` Keynote 并校验 `frontmost`，不在前台就返回 `not frontmost` 且不点 —— 用户切走 app 时点击会落到别的窗口上，这个保护省过好几次误点。

坐标怎么来：`screencapture -x /tmp/k.png && sips -Z 1600 /tmp/k.png --out /tmp/k_s.png` 看缩略图；屏幕点 = 缩略图像素 × (屏幕逻辑宽度 / 1600)。Retina 3024 px 宽的 MacBook 逻辑宽 1512，系数 0.945。**用户一旦拖动/分屏窗口，所有坐标全部失效，必须重新截图**。

选中音频对象的正确方式：**先点画布空白处取消选择，再点画布中央的喇叭图标**。别点对象列表里的行 —— 实测点行会和已选的图片形成多选，此时检查器 tab 变成 `Style / Image / Arrange`，且 Description 栏里同时列出多个对象名，这就是多选的信号。单选音频时 tab 是 `Audio / Arrange`。

改自动播放的完整动作：选中喇叭 → 工具栏 `Format` → `Audio` tab → 点掉 `Start audio on click` → 截图确认方框变空 → `save document 1`。

## 循环：GIF / 视频用 AppleScript 就能改

"动画放完一次又来一次"= 那个 GIF 的 `repetition method` 是 `loop`（**Keynote 导入 GIF 默认循环**）。这是字典里少数真正能写的属性，不用碰 UI：

```applescript
tell application "Keynote"
  set m to movie 1 of slide 15 of document 1
  set repetition method of m to none   -- none / loop / loop back and forth
  save document 1
end tell
```

`audio clip` 也有同名属性；`clip volume` / `movie volume` 同理可写。

## AX 读值：能用但不稳

- `entire contents of window 1` 在 Keynote 上**时好时坏**：同一状态下有时给 85 个元素，有时空。读到空就重试，别据此下结论。
- 能读到的：检查器 tab 是 `AXRadioButton`，`description` = "Format"/"Animate"/"Document"/"Audio"/"Style"…；`perform action "AXPress"` **不需要 Keynote 在前台**，是最安全的切 tab 方式。勾选框是 `AXCheckBox`，`value` 0/1。
- 读不到的：对象列表（Object List）的行没有文字；Open panel 里没有按钮。
- `scripts/inspector_dump.applescript` 一把 dump 出所有 popup / checkbox / radio / static text，用来核对改动是否生效。
- 截图：`screencapture -x` 抓全屏可以；但 **`CGWindowListCopyWindowInfo` 看不到 Keynote 窗口**（没给终端屏幕录制权限），`screencapture -l <winid>` 这条路不通。Keynote 在别的 Space 上时截图里没它，先 `activate`。

## 两个误导性的报错

- **`open` 超时 + 弹窗「"x.key" can't be opened right now. The file format is invalid.」**：先别慌，大概率是**路径不存在**（用户改了文件名或移走了），不是文件坏了。`ls` 一下目录确认，`sample Keynote 1 | grep -A3 runModal` 能确诊是 NSAlert 卡住了主线程。用 AX 按 `OK` 再按 Open 面板的 `Cancel`（`perform action "AXPress"`，不需要前台）即可恢复。
- **`activate` 都 -1712 超时**：那才是真死锁，见上文 `make new audio clip` 一节，只能 `kill -9`。

## 保存与收尾

```applescript
tell application "Keynote" to save document 1
```

之后核对：`modified of document 1` 为 false；`ls -la` 看 .key 变大（嵌入了音频，3.4 MB 的 wav 让文件从 32.5 MB 涨到 36.0 MB）。

交付时提醒用户：从目标页的前一页开始播放，翻过去确认音效准时、动效只走一遍；「Play audio across slides」是否保留是他们的选择 —— 舞台音效通常希望离开这页就停，但别替用户改。
