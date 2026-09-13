# 报幕音效

- `2026 报幕audio/bgm 7s进人声.mp3`：今年公用 BGM（27.3 s，第 7 秒有个给人声让位的空档）。
- `2026 报幕audio/<剧名>.m4a`：8 个剧目的报幕人声原录音，前面各带 2–3 s 空白。
- `2026 报幕audio/合成/报幕-<剧名>.mp3`：**成品**，演出用这个。做法：人声自动找开口点切掉空白，准点放在 BGM 第 7.00 s，BGM 整体压 7 dB，限幅 −1 dBTP。参数是拆 2025 年成品反推出来的，和去年听感一致。
- `2025 节目intro/`：去年的原录音（`N.m4a`）和成品（`introN-updated.mp3`），留作参照。

重做 / 换人声重跑：

```bash
python3 ../skills/intro-mix/scripts/mix_intro.py "2026 报幕audio/bgm 7s进人声.mp3" "2026 报幕audio" "2026 报幕audio/合成"
```
