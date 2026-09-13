---
name: intro-mix
description: |
  把一条公用 BGM 和每个节目的报幕人声（录音前面带两三秒空白）合成为演出用的节目 intro / 报幕音效：自动检测人声开口点、切掉前后空白、把人声准点放到 BGM 第 N 秒、BGM 整体压低、限幅后输出 mp3，并逐条打印响度校对。当用户说"合成报幕""bgm 进人声""做节目 intro""把这些报幕录音和 bgm 合起来""第七秒进人声"，或给出一个 bgm 和一堆 .m4a 人声录音要做成一批音效时，用本 skill。沉淀自 2026-09-13 给喜剧节 8 个剧目做报幕的实战，参数是拆解 2025 年成品反推出来的。
---

# 报幕 / 节目 intro 合成（intro-mix）

一句话：**先量去年的成品，再决定参数；人声不是叠上去而是先找到开口点再对齐；做完逐条打印响度看齐不齐。**

## 起手式

1. 确认工具：`which ffmpeg ffprobe`（Homebrew 装的就行）。这台机器 **没有 numpy、没有 sox，pip 也被 PEP 668 锁了**，脚本全部用 ffmpeg 管道 + 纯 Python `array`，不要浪费回合装包。
2. 先 `ffprobe` 看 BGM 和人声的时长、采样率、声道。人声一般是手机录的 `.m4a`，48k 立体声或 24k 单声道都遇到过，脚本会统一到 48k 立体声。
3. **有去年/上次的成品就先拆它**：用 `scripts/mix_intro.py` 同目录的思路量它的 250 ms RMS 包络，跟裸 BGM 逐段相减得到"BGM 压了几 dB"，看人声在第几秒进、人声段 RMS 多少。2025 喜剧节的结论：同一条 BGM 整体压 **−7 dB**，人声 **7.00 s** 准时进，人声段 RMS 约 −11 dBFS，整轨 −20.5 LUFS、峰值 −1.2 dBTP，**没有 side-chain 闪避**。

## 跑

```bash
# 单条
python3 scripts/mix_intro.py "<bgm.mp3>" "<人声.m4a>" "<输出.mp3>"
# 整个文件夹（跳过 bgm 自己），输出到 <out 文件夹>/报幕-<原名>.mp3
python3 scripts/mix_intro.py "<bgm.mp3>" "<人声文件夹>" "<out 文件夹>"
# 可调：--at 7.0 人声进入秒数  --bgm-db -7  --voice-db -1  --thresh -30（算作开口的 RMS 阈值）
```

脚本做的事：
- **开口点检测**：10 ms 窗 RMS 首次超过 `--thresh`（默认 −30 dBFS）。录音底噪一般在 −55 到 −65 dBFS，人声一进就是 −10 dBFS 左右，跳变很干脆，−30 这个阈值很安全；口水声、呼吸声通常在 −40 到 −50，不会误触发。往前留 60 ms 起手 + 30 ms fade in，不然辅音起头会被切掉。
- **尾部**同法切掉，留 250 ms + 150 ms fade out。
- BGM `volume=<bgm-db>`，人声 `adelay` 到位后 `amix normalize=0`，最后 `alimiter` 限 −1 dBTP 兜底。
- 输出长度 = BGM 长度，320 kbps mp3，48 kHz。
- 每条打印：源文件里人声 从几秒到几秒、词长、整轨 LUFS、峰值。

## 校对（每次都做，不要只听一条）

1. 看打印出来的 **LUFS 列**：八条落在 −19.7 到 −21.5 之间就算齐；差 2.5 dB 以内人耳基本无感，差 4 dB 以上再考虑给人声加一步统一响度。
2. 抽一条画 **50 ms 包络看 7 s 附近**：6.95 s 还是 BGM 的 −35 左右、7.00 s 起跳到 −13/−9，就是准点。
3. 每条的开口点值应在 2–3 s 这种"合理的录音起手空白"范围。如果某条报 0.0x s 或 5 s 以上，多半是那条录音有爆音/长静默，去看它 10 ms 包络。
4. 拿去年成品同位置对比包络，BGM 段前后都在 1 dB 内、人声段 RMS 相近即可交付。

## 坑

- 手机录的人声很多本身已经**顶到 0 dBTP**（被手机自带压限器推满），这时人声不要再抬增益，靠压 BGM 来做出对比；`--voice-db -1` 只是给 limiter 留一点余量。
- `loudnorm=print_format=json` 输出在 stderr，而且后面还跟着别的行，解析要取 `rindex("{")` 到 `rindex("}")+1`，直接 `json.loads` 尾巴会报 Extra data。
- `adelay` 对立体声要写 `adelay=N:all=1`，只写一个数只延时左声道。
- `amix` 默认会把总音量除以输入数，一定加 `normalize=0`。
- `astats=reset=1:length=1` 出来的是每个音频帧一行不是每秒一行，量包络别用它，用脚本里那种 ffmpeg 解成 f32le 再自己分窗算 RMS 的办法，可控得多。

## 后续

合成出来的 mp3 通常要放进 QLab 每一幕 cue list 的**最前面**当报幕 cue（编号如 `5_0`），这一步用 `qlab` skill 做，在该幕的 `qlab_actN_sequence.json` 里加一步 `["audio", 0]` 即可（文件名要以 `0-` 开头才能被 `files()` 识别）。
