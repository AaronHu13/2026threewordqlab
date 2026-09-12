# 喜剧节 2026 · QLab 音效工程备份

戏剧节下半场（Act 5–8）的 QLab 5 全局工程及全部音频素材备份。

## 结构

```
喜剧节2026.qlab5              # QLab 5 全局工程（每个 Act 一个 cue list）
Act 5_ 大堡健/                # Act 5 音频（cue 编号 5_N，17 个 cue）
Act 6_ 最后的太阳/            # Act 6 音频（cue 编号 6_N / 6_NF，14 个 cue）
Act 8_ 一幕成名2幕中无人/     # Act 8 音频（cue 编号 8_N，60 个 cue）
```

Act 7 音频尚未到位，待补。

## 使用方法

1. 整个仓库 clone 或下载 zip 到任意位置，**保持文件夹结构不变**。
2. 用 QLab 5 打开 `喜剧节2026.qlab5`，音频按相对路径自动关联。
3. 若出现红色 missing cue，在 QLab 里选中 cue → Inspector → Basics → 重新指向同名文件夹下的音频即可。

## 注意

- 剧团用的是 **免费版 QLab 5**：工程里只使用 Audio / Fade / Group / Start / Stop / Wait / Memo cue，不要加入需要付费授权的 cue 类型。
- `Act 6_ 最后的太阳/旧版单独工程（已弃用）/` 是早期的单 Act 工程，仅作留档，演出不用。
