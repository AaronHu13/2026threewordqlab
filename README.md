# 喜剧节 2026 · QLab 音效工程备份

戏剧节下半场（Act 5–8）的 QLab 5 全局工程及全部音频素材备份。

## 结构

```
喜剧节2026.qlab5              # QLab 5 总工程（每个 Act 一个 cue list，演出时用这个）
.gitattributes                # *.qlab5 标为 binary，git 不会尝试合并工程文件
Act 1_ 回来了/                # 每幕一个文件夹：本幕音频 + 独立工程 Act N_ 剧名.qlab5 + 编排 qlab_actN_sequence.json
Act 2_ 这个童话不对劲/        #   cue 编号 N_0 = 报幕，N_1… = 本幕音效，N_1F = 淡出停，N_1D = 压低不停
Act 3_ 今天小神有点忙/
Act 4_ 卡巴莱特新编/
Act 5_ 大堡健/
Act 6_ 最后的太阳/
Act 7_ 晚安承天寺/            # 2026-09-15 按导演 cts.qlab5 复刻 5 条音频 + 淡出；未引用的 wav 在子文件夹
Act 8_ 一幕成名2幕中无人/
报幕/                         # 8 个剧目的报幕音效：原录音、公用 BGM、合成成品（见其 README）
前厅组/                       # 前厅组（检票 + 引导入场）工作说明，见其 README
skills/                       # 做这套工程用到的 Claude Code skills（qlab / keynote / intro-mix）
```

## 各幕状态（2026-09-16）

手动淡出停（`N_xF`）统一为 **2s**（2026-09-16 从 3s 改短）；例外：Act 7 按导演工程保持 5s，**Act 6 剧组 2026-09-16 自己改成 1s**；Act 8 的 1s 无缝衔接和压低不停的 D 类 fade 不受影响。

| 幕 | cue 数 | 说明 |
|---|---|---|
| Act 1 回来了 | 10 | 报幕 + 6 条音效，顺序播；3 careless whisper（2s）/ 5 常回家看看（10s）/ 6 我记得（10s）各配一条手动淡出（5 / 6 的 10s 是 2026-09-16 剧组要求） |
| Act 2 这个童话不对劲 | 28 | 报幕 + 12 条音效 + 11 条旁白。2026-09-17 剧组新增 23 结尾垫乐（21s，编号沿用剧组顺序号，接在旁白11 后）+ 一条 3s 手动淡出（剧组说的 cue 24）。**没有拿到 cue 表**，音效按文件编号顺序、旁白按剧情插在 10 小矮人家 / 11 吃苹果前后，1 魔幻森林 / 4 皇后 intro / 6 狼人杀 各配一条手动淡出。顺序需要剧组确认，改 json 重建即可 |
| Act 3 今天小神有点忙 | 20 | 报幕 + 17 条，cue 13/14 音量 +3.5 dB；07 sidapusa / 08 dazhuanpan 各配一条手动淡出 |
| Act 4 卡巴莱特新编 | 22 | 报幕 + 12 条；1 In car（3s）/ 9 long新闻（6s）/ 12 kickline（8s）各配一条手动淡出（1 / 12 的时长是 2026-09-17 码戏剧组要求，12 的 8s 可能还会调）。**9 新闻 09-17 码戏四选一**：4_9 long（66s，现用）/ 4_91 mid（47s）/ 4_92 short + 长掌声（35s）/ 4_93 short（31s）四条各带 6s 手动淡出（09-17 码戏现场从 2s 改成 6s），91–93 的音频在 `9 候选（09-17 码戏四选一）/`；定稿后只留一条、删掉另外三条并把 cue 数改回 16 |
| Act 5 大堡健 | 20 | 报幕 + 17 条音效 + 2 条淡出 |
| Act 6 最后的太阳 | 35 | 2026-09-15 按新音频包 + `requirements.txt` 重建：报幕 + 21 条音效，含 9+10 一键同停、12+13 一键同起、cue 8 / cue 18 播放中压低的 D 类 fade。Cue 13 换 mp3、Cue 15 剪掉 1-2-3 倒数、Cue 16 换 35.8s 新版。**2026-09-16 剧组微信回传的独立工程已回收**：手动淡出全改 1s（9F 1s 但 10F 仍 2s，照原样保留）、8D 从压到 65% 改为压到 30%（-13.6 dB）、cue 11 / 14 换 `… New.mp3` 新录音（旧版在 `原始素材/`）、cue 17 +3 dB。**2026-09-17 cue 3 神剑登场换剧组 plus 版**（7.6s → 9.0s，响度不变，同名覆盖，旧版在 `原始素材/`） |
| Act 7 晚安承天寺 | 11 | 按导演 2026-09-15 的 cts.qlab5 复刻：报幕 + 5 条音频（intro / 二胡 / 信 / 邮箱 / wake up，后四条 -5 dB）+ 二胡、信 5s 淡出、邮箱立刻停、wake up 5s 推高到 +12 dB；另加一条 wake up 手动淡出。导演未引用且内容不重复的 8 条 wav 放在 `未编排音频（导演工程未引用）/`（可能是尚未编排的后续段落），原工程在 `协作者草稿/cts.qlab5`（它要求音频在 `audio/` 子文件夹，直接开会红） |
| Act 8 一幕成名2幕中无人 | 66 | 报幕 + 65 条（2026-09-13 重建；09-15 Aaron 手工调整：去掉两条 Memo 暂停占位，揭秘 / 枪声 / 英雄 +12 dB、夺抢 −3.3 dB、心声 +5.4 dB；09-16 剧组重做 3 / 6 / 26 / 28 / 29 / 41 六条音频的音量，原地覆盖同名文件） |

**每幕第一个 cue 是报幕**（编号 `N_0`）：`报幕/2026 报幕audio/合成/报幕-<剧名>.mp3` 复制成该幕文件夹里的 `0 报幕-<剧名>.mp3`（这样每幕文件夹自成一体，打 zip 发出去不缺文件）。报幕重新合成后要把 8 份副本一起换掉再重建。

Pre-show / Intermission / Post-show 三个 list 里各有一条旧占位 cue，仍是红色 missing，属正常。

## 为什么每幕还有一个独立工程

`.qlab5` 是 Apple 二进制 plist，**git 无法合并**。两个人同时改了 `喜剧节2026.qlab5` 再 push，冲突时只能整个文件二选一，输的那方改动全丢。所以：

1. **各幕独立工程** `Act N_ 剧名/Act N_ 剧名.qlab5` 只含本幕那一个 cue list，是从总工程拆出来的（`skills/qlab/scripts/split_workspace.py`）。**谁负责哪幕，就只改哪幕的独立工程**，互不冲突。
2. **总工程由一个人合并**（演出前统一做一次）：同时打开总工程和某幕的独立工程，在独立工程的 cue list 里 ⌘A 全选 → ⌘C，到总工程对应 list 里 ⌘V。QLab 5 没有"导入 cue list"功能，跨工程复制粘贴是唯一的合并方式；粘贴会保留编号、名字、音频指向和 fade 目标。
3. 改了总工程里某幕的内容，记得**同步改该幕的独立工程**（或重跑一次拆分脚本），否则两边会不一致。
   更推荐的做法：改动以该幕的 `qlab_actN_sequence.json` 为准（json 是文本，能 diff、能合并），改完对着总工程跑一次 `skills/qlab/scripts/build_act_into_list.py`，再用 `split_workspace.py` 拆出独立工程。json 里 `"folder": "."` 指 json 自己所在的文件夹，所以在任何人的机器上都能直接跑。
4. `.gitattributes` 把 `*.qlab5` 标成 binary：git 不再尝试文本合并，冲突会明确报出来，而不是产生半损坏的文件。真撞了冲突就 `git checkout --theirs/--ours` 选一边，再用复制粘贴把另一边的改动补回来。

独立工程另存时 QLab 会给它新的 workspace ID，所以可以和总工程同时打开。

## 改 cue 的标准流程

1. `git pull`，改该幕的 `qlab_actN_sequence.json`（格式见 `skills/qlab/references/sequence_json.md`）。
2. 打开 `喜剧节2026.qlab5`，`python3 skills/qlab/scripts/build_act_into_list.py "<该幕文件夹>/qlab_actN_sequence.json"`，⌘S 保存。
3. `python3 skills/qlab/scripts/split_workspace.py "$PWD/喜剧节2026.qlab5" "$PWD" 'Act N'` 拆出该幕独立工程。
4. `python3 skills/qlab/scripts/verify_sequence.py --all .` 全 ✓ 后提交 json + 两个 .qlab5。

在 QLab 里手工改了的话，反过来先 `dump_sequence.py` 导出 json 再走 3、4。细节和报错见 `skills/qlab/references/json_qlab_workflow.md`。

## 使用方法

1. 整个仓库 clone 或下载 zip 到任意位置，**保持文件夹结构不变**。
2. 演出用 QLab 5 打开 `喜剧节2026.qlab5`；只排某一幕就打开该幕文件夹里的 `Act N_ 剧名.qlab5`。音频按相对路径自动关联。
3. 若出现红色 missing cue，在 QLab 里选中 cue → Inspector → Basics → 重新指向同名文件夹下的音频即可。

## 注意

- 剧团用的是 **免费版 QLab 5**：工程里只使用 Audio / Fade / Group / Start / Stop / Wait / Memo cue，不要加入需要付费授权的 cue 类型（Pause / Script / Network / Devamp 建出来就是 broken）。
- 「暂停再续播」在免费版的做法：到点按键盘 `[`（Pause All）暂停，列表里的 Memo 行只是对齐流程占位，之后 GO 那条 Start cue（如 `8_1R`、`8_37R`）从暂停点续播。

## skills/

做这套工程用到的三个 Claude Code skill，每个子文件夹就是一个 skill。装到自己机器上：把 `skills/<名字>/` 复制为 `~/.claude/skills/<名字>/` 即可（Aaron 机器上的 `~/.claude/skills/` 与这里保持同步，改了任一边就 rsync 过去）。

### skills/qlab/

用脚本驱动 QLab 5 建工程（AppleScript + OSC），本工程的 Act 5/6/8 cue 都是用它批量建出来的。

- `SKILL.md`：踩坑总结与操作心法（QLab 5.6.3 实测）
- **`references/json_qlab_workflow.md`：json ↔ QLab 互转手册（环境授权、三条命令、独立工程与总工程的关系、常见报错）。协作者先读这个。**
- `scripts/build_act_into_list.py <qlab_actN_sequence.json>`：按 json 编排往指定 cue list 批量建 cue、加 fade、设编号（幂等，可反复跑）
- `scripts/dump_sequence.py "<list 名>" <prefix> <音频文件夹> [out.json]`：反向把 QLab 里的 cue list 导出成 json，json 是多人协作时的合并单位
- `scripts/verify_sequence.py --all <仓库根>`：校验前台工程里每幕 cue list 与 json 一致，提交前必跑（总工程、各幕独立工程各一次）
- `scripts/split_workspace.py <总工程> <输出目录> ['Act \d']`：把总工程拆成每幕一个独立 .qlab5
- `scripts/dump_workspace.applescript <ws索引>`：回读工程里所有 cue 校对
- `references/sequence_json.md`：文字版音乐 cue 表 → json 的翻译规则；`packaging.md`、`scripting.md`：打包迁移、脚本细节

### skills/keynote/

用脚本给演出 Keynote 加音效 / 改动效，沉淀自给「2026喜剧节背景.key」第 15 页加音效的实战（2026-09-12）。

- `SKILL.md`：踩坑总结（AppleScript 建音频会死锁、System Events 点击在 Keynote 里无效、新插音频默认要点一下才播、GIF 默认循环）
- `scripts/insert_audio.applescript <页号> <音频路径>`：走「插入 › 选取…」把音频插到指定页
- `scripts/click.js x y [x y ...]`：CGEvent 真鼠标点击，用来点检查器里的勾
- `scripts/media_info.applescript <页号>`、`scripts/inspector_dump.applescript [tab]`：核对页内媒体与检查器

### skills/intro-mix/

把公用 BGM 和各剧目的报幕人声合成节目 intro，`报幕/2026 报幕audio/合成/` 里的 8 条就是它做的（2026-09-13）。

- `SKILL.md`：做法（拆 2025 成品反推的参数：BGM 压 7 dB、人声 7.00 s 准点进、限 −1 dBTP）、校对步骤、ffmpeg 坑
- `scripts/mix_intro.py <bgm> <人声|文件夹> <out>`：自动检测人声开口点切掉前后空白、对齐、混合、逐条打印响度
