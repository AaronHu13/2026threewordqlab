---
name: mic-cues
description: |
  读话剧/音乐剧剧本（Google Doc 或贴进来的文本），复核里面内嵌的无线 mic 开关 cue（哪句话之后开/关几号 mic），
  用状态机逐条推演"此刻哪些 mic 是开的"，按说话人校验每句台词的 mic 有没有开，找出漏开、写错号、"keep"歧义、重复等问题，
  再把每条 cue 之后的全局状态行写回 Google Doc（脚本 dump → plan → check → apply，只动 mic 行，回读校验，可 --refresh 重写）。
  当用户说"帮我检查 mic cue""mic 开关有没有问题""加一个全局 mic 状态""同步 mic 状态到剧组剧本""剧本改了状态行要更新"，
  或给出剧本 + 演员 mic 编号表时，用本 skill。沉淀自 2026-09-13 喜剧节 Act 4《Cabaret新编AI》和 Act 8《一幕成名2》的实战。
---

# 剧本 mic cue 复核与状态行（mic-cues）

一句话：**每条 mic cue 之后的"全局状态"才是真相，增量写法（开 8、关 10）必须推演成完整状态才能校验；写回文档只碰 mic 行，写前 diff、写后回读。**

## 背景：行业怎么做，我们为什么不同

专业音乐剧不喊 mic cue：音响师（A1）在调音台上逐句推拉（line-by-line / DCA mixing），调音台每个 scene 存的是**完整状态**（没被分配的 channel 自动 mute），所以不会有"上一条忘关"这类累积错误。我们是 Aaron 口头喊 cue、audio 执行，cue 以增量形式写在剧本里，所以要人工把增量推演成完整状态并写在旁边。这套思路的详细来源见 `references/industry.md`。

## 起手式（不管是贴进来的文本还是 Google Doc）

1. **先拿 mic plot**：演员 → 角色 → mic 号。Google Doc 里通常是开头一张表或几行 `阿龙 - 8`。同一演员多角色（士兵/卫兵、快递员/外卖员）都要记成别名。
2. **分段读剧本**，一次 200 段左右，别一口气读完再凭印象判断——长剧本容易幻觉。`dump` 会把整段剧本存成 `DIR/script.txt`，用 `awk 'NR>=80&&NR<=300'` 之类分段看。
3. **列一张状态表**：每条 mic cue 一行：位置 / 操作 / 之后开着的 mic / 这段谁有词 / ✅❌。这是校验的核心，用户也明确要求过。

## 常见错误类型（两份剧本里真出现过的）

| 类型 | 例子 | 怎么发现 |
|---|---|---|
| 漏开 | 角色出场有整段 talking，但 cue 是从开场复制来的 `on 8,9,11`，该开的 10 没开 | 状态表里该段说话人的 mic 在"关"那一侧 |
| 写错号 | `mic on 8，mic off 10`，但接下来说话的是 9；8 本来就开着 | "开一个已经开着的 mic"几乎总是写错了号 |
| keep 歧义 | `keep mic on 8,9`，但 8 上一条刚关了 | keep 的对象必须在当前状态里是开的，否则要写成 on |
| 两人号码写反 | 外卖员 13 / 搬运工乙 14 在 4 条 cue 里互换，其中一条自己带"？" | 和 mic plot 表逐条对；同一角色前后 cue 号不一致 |
| 只有一句词的配角 | 卫兵："你别动！" 全剧就这一句，mic 从没开过 | 说话人校验（脚本 `check`）会抓出来 |
| 冗余 / 重复 | 连续两条一样的 cue；`阿杜 mic on 9` 但 9 早开着 | 无害，但建议删，避免操作员困惑 |
| 收尾没 all off | 拉幕后所有 mic 仍开 | 状态表最后一行不为空 → 提示 |

给用户的修改意见按 Aaron 的习惯写成「原文位置 → 改成什么」，可以直接贴回剧本；状态表另附作校验用（见记忆 `mic-cues-inline-in-script`）。

## 状态行格式

每条 mic cue **正下方新起一行**，黑色正体（灰色斜体 Aaron 说看着难受）：

```
【mic 关 8 - 11】
【当前开：5九条 6伊万 7导演 12助理 ｜ 关：8 9 10 11 13 14】
```

"开"一侧带角色名（喊 cue 的人一眼知道谁能说话），"关"一侧只列号。全开写 `关：无`，全关写 `开：无`。

## Google Doc 流程（scripts/gdoc_mic_cues.py）

前提：文档主人已按 `references/google_setup.md` 开好 Docs API、建好服务账号、把文档 Share 给服务账号邮箱（Editor）。密钥默认读 `~/.slock/tokens/google_docs_sa.json`，可用环境变量 `GDOC_SA_KEY` 覆盖。系统 python 被 PEP 668 锁，一律 `uv run --with google-api-python-client --with google-auth python3 scripts/gdoc_mic_cues.py …`（zsh 里别把整条命令放进变量再执行，会当成一个路径）。

```bash
S=~/.claude/skills/mic-cues/scripts/gdoc_mic_cues.py
alias gmc='uv run --quiet --with google-api-python-client --with google-auth python3 '$S
gmc dump  <doc_id> --work work/act8            # 只读；打印 mic plot 表和全部 mic 行，存 paras.json / script.txt
# 写 cfg.json：doc_id、mics、aliases、ignore、fixes（照 examples/）
gmc plan  --work work/act8 --config cfg.json   # 自动解析每条 mic 行 → cues；逐条人工审，尤其带 ⚠ 的
gmc check --work work/act8 --config cfg.json   # 状态表 + 说话人校验 + 与文档已有状态行比对
gmc apply --work work/act8 --config cfg.json --dry-run
gmc apply --work work/act8 --config cfg.json             # 首次写入
gmc apply --work work/act8 --config cfg.json --refresh   # 剧本改过 / 状态行过期时：删旧状态行后整体重写
```

脚本的安全边界（不要绕过）：
- `apply` 先重新抓文档，和 `dump` 时逐段比对，**有任何变化就拒绝写**，让你重新 dump/plan/check。
- 文档里已有状态行时不重复写，必须显式 `--refresh`。
- `fixes` 里每条原文必须在全文唯一，否则不写。
- 写完回读：每条 mic 行下面必须紧跟状态行；去掉状态行后其余段落必须和原文（加 fixes）逐字相同。最后一行 `other paragraphs identical … True` 才算成功。
- 行号 Lnn 四个子命令一致，按"去掉状态行后"的段落序号计。

改剧组共用正本前，先在用户自己的副本上跑通，再对正本 dump → check（确认 mic 行和副本一致）→ apply。所有写入 Google Doc 版本历史都能整体回退，出问题告诉用户回退到哪个时间点。

## 自动解析支持的写法（auto_parse）

`（mic CEO，阿龙，妈妈 8，9，11 on）` `【mic 导演 7 关】` `【mic 5-12开】` `【mic 关 8 - 11】` `【搜捕队mic开-8】` `[mic 开-外卖员-13]`
`（mic on 8,9,10，其他人off）`→set `（mic on 8、10， 其他人off 9.11-14）`→set `（all mic off）` `【mic - open all 5-14】` `（keep mic on 8,9，mic off 10-14）`（keep 视作 on）。
数字归属看离哪个 on/off 关键词最近；中英混排里 `\b` 不管用（"人off"），脚本用 lookaround。**解析结果只是草稿，plan 输出必须逐条人工审**，改 cfg.json 里的 on/off/set 即可。

## 说话人校验的局限

只识别 `名字：` / `名字（动作）：` / `（后台）名字：` 这类开头；歌词行、`合：`、`众人：`、画外音跳过（放 `ignore`）。"未识别的说话人"里通常是标题、场次、杂项，真有词的角色才需要加进 `aliases`。它能抓"mic 关着却有词"，抓不到"mic 开着但人在后台蹭出杂音"——那类要靠读剧本判断（例如戴马头套、后台换装时建议临时关）。
