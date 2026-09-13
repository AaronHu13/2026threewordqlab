# 喜剧节 2026 · QLab 音效工程备份

戏剧节下半场（Act 5–8）的 QLab 5 全局工程及全部音频素材备份。

## 结构

```
喜剧节2026.qlab5              # QLab 5 总工程（每个 Act 一个 cue list，演出时用这个）
.gitattributes                # *.qlab5 标为 binary，git 不会尝试合并工程文件
Act 1_ 回来了/                # 每幕一个文件夹：本幕音频 + 本幕独立工程 Act N_ 剧名.qlab5
Act 2_ 这个童话不对劲/
Act 3_ 今天小神有点忙/
Act 4_ 卡巴莱特新编/
Act 5_ 大堡健/                # cue 编号 5_N，19 个 cue
Act 6_ 最后的太阳/            # cue 编号 6_N / 6_NF，28 个 cue
Act 7_ 晚安承天寺/            # 音频尚未到位，工程里是模板占位
Act 8_ 一幕成名2幕中无人/     # cue 编号 8_N，67 个 cue（2026-09-13 按新音频包重建）
                              #   qlab_act8_sequence.json 是本幕的编排配置，可一键重建
```

Act 1–4、7 的音频还没进仓库，对应 cue 目前是红色 missing，属正常。

## 为什么每幕还有一个独立工程

`.qlab5` 是 Apple 二进制 plist，**git 无法合并**。两个人同时改了 `喜剧节2026.qlab5` 再 push，冲突时只能整个文件二选一，输的那方改动全丢。所以：

1. **各幕独立工程** `Act N_ 剧名/Act N_ 剧名.qlab5` 只含本幕那一个 cue list，是从总工程拆出来的（`qlab-skill/scripts/split_workspace.py`）。**谁负责哪幕，就只改哪幕的独立工程**，互不冲突。
2. **总工程由一个人合并**（演出前统一做一次）：同时打开总工程和某幕的独立工程，在独立工程的 cue list 里 ⌘A 全选 → ⌘C，到总工程对应 list 里 ⌘V。QLab 5 没有"导入 cue list"功能，跨工程复制粘贴是唯一的合并方式；粘贴会保留编号、名字、音频指向和 fade 目标。
3. 改了总工程里某幕的内容，记得**同步改该幕的独立工程**（或重跑一次拆分脚本），否则两边会不一致。
4. `.gitattributes` 把 `*.qlab5` 标成 binary：git 不再尝试文本合并，冲突会明确报出来，而不是产生半损坏的文件。真撞了冲突就 `git checkout --theirs/--ours` 选一边，再用复制粘贴把另一边的改动补回来。

独立工程另存时 QLab 会给它新的 workspace ID，所以可以和总工程同时打开。

## 使用方法

1. 整个仓库 clone 或下载 zip 到任意位置，**保持文件夹结构不变**。
2. 演出用 QLab 5 打开 `喜剧节2026.qlab5`；只排某一幕就打开该幕文件夹里的 `Act N_ 剧名.qlab5`。音频按相对路径自动关联。
3. 若出现红色 missing cue，在 QLab 里选中 cue → Inspector → Basics → 重新指向同名文件夹下的音频即可。

## 注意

- 剧团用的是 **免费版 QLab 5**：工程里只使用 Audio / Fade / Group / Start / Stop / Wait / Memo cue，不要加入需要付费授权的 cue 类型（Pause / Script / Network / Devamp 建出来就是 broken）。
- 「暂停再续播」在免费版的做法：到点按键盘 `[`（Pause All）暂停，列表里的 Memo 行只是对齐流程占位，之后 GO 那条 Start cue（如 `8_1R`、`8_37R`）从暂停点续播。
- `Act 6_ 最后的太阳/旧版单独工程（已弃用）/` 是早期的单 Act 工程，仅作留档，演出不用。

## qlab-skill/

用脚本驱动 QLab 5 建工程的 Claude Code skill（AppleScript + OSC），本工程的 Act 5/6/8 cue 都是用它批量建出来的。

- `SKILL.md`：踩坑总结与操作心法（QLab 5.6.3 实测）
- `scripts/build_act_into_list.py <cfg.json>`：往指定 cue list 批量建 cue、加 fade、设编号
- `scripts/dump_workspace.applescript <ws索引>`：回读工程里所有 cue 校对
- `scripts/split_workspace.py <总工程> <输出目录> ['Act \d']`：把总工程拆成每幕一个独立 .qlab5（自动处理删 cue list 的确认框）
- `references/`：打包迁移、脚本细节

装到自己机器上：把 `qlab-skill/` 复制为 `~/.claude/skills/qlab/` 即可。

## keynote-skill/

用脚本给演出 Keynote 加音效 / 改动效的 Claude Code skill，沉淀自给「2026喜剧节背景.key」第 15 页加音效的实战（2026-09-12）。

- `SKILL.md`：踩坑总结（AppleScript 建音频会死锁、System Events 点击在 Keynote 里无效、新插音频默认要点一下才播、GIF 默认循环）
- `scripts/insert_audio.applescript <页号> <音频路径>`：走「插入 › 选取…」把音频插到指定页
- `scripts/click.js x y [x y ...]`：CGEvent 真鼠标点击，用来点检查器里的勾（如取消 Start audio on click）
- `scripts/media_info.applescript <页号>`：列出某页的音频 / 视频 / GIF 及其循环、音量
- `scripts/inspector_dump.applescript [tab]`：dump 检查器控件核对改动

装到自己机器上：把 `keynote-skill/` 复制为 `~/.claude/skills/keynote/` 即可。
