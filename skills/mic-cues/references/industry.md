# 行业里 mic 开关是怎么处理和记录的（2026-09 调研摘要）

- **Line-by-line / DCA mixing** 是音乐剧标准做法：音响师（A1）只在 8–12 个 DCA 推子上工作，谁说话推谁，说完拉下；
  每个 desk scene 规定这几个推子对应哪些 mic，没分配的 channel 自动 mute。换 scene 常由 QLab 的 GO 键经 MIDI 一并触发。
  一首歌通常 3 个以上 desk scene。舞台监督的 prompt book 里没有 mic cue。
- **Mix script**：A1 自己标的剧本。mic 标红，QLab/台面 cue 标绿；两种流派——每场开头列本场用到的 DCA，或每句台词前写 DCA 号。
  演员上场 `+N`、下场 `-N`；每个角色本场第一句用荧光笔标出（提醒推子该上了）。iPad 用 Scriptation / GoodNotes，也有专用 app "Sound Script"。
- **总览表**：Excel 横列每个 scene 每个 DCA 对应谁，用来发现分配冲突——就是我们的状态表，只是他们按"每条的完整状态"记。
- **Mic plot** 是另一份文件：谁戴哪个发射包、何时换包（swap），A2（deck sound）执行。theatrecrafts.com 有样板。
- 工具：TheatreMix（按 cue 分配 DCA、未分配自动 mute、相邻 cue 差异着色、OSC 联动 QLab，支持 Yamaha / A&H / Behringer / Midas）；
  DiGiCo Theatre 软件（aliases / players）、Yamaha Rivage Theatre Mode（每演员一组 EQ/动态）；MicPlot 软件算最少 mic 数和换包。
- 来源：Adam Gibson《Quick Guide to Musical Theatre DCA & Line by Line Mixing》(2024)；SoundGirls "Mixing for Musicals"、"How to Make Tech Easier: Be Prepared"；
  Finlay Ross "How to Mix a Musical"；theatrecrafts.com Sound Design Paperwork；theatremix.com；Shannon Slaton《Mixing a Musical》ch.3。

对我们的启发：口头喊 cue 的场合，把每条 cue 写成**编号 + 完整状态 + 触发台词**，加 standby 行；这一条改动能消灭重复开、keep 歧义、漏开三类错误。
