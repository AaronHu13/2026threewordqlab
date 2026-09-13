# QLab 工程的保存、交付与换机

实测于 QLab 5.6.3，2026-08-25。

## 核心事实：「工程」是一个文件夹，不是一个文件

`.qlab5` 只存**路径引用**，不含音频本身（26 个 cue 的工程文件只有 428 KB）。所以只发 `.qlab5` 过去，对方所有 cue 会全部变红报错。

但好消息是 **QLab 会做相对路径恢复**：只要素材和 `.qlab5` 在同一个文件夹里，整个文件夹搬到任何位置都能自动找回。实测把文件夹整体拷到 `/tmp` 下打开，26 个 cue 全部正常、0 broken，而且每个 cue 的路径被自动改写成了新位置。

**规矩：一场戏一个文件夹，`.qlab5` 和所有音频都塞在里面。**

## 交付给别人的标准流程

1. **File → Workspace Files → Copy media files into project folder**
   把散在别处（桌面、下载文件夹）的素材收进工程文件夹。素材本来就都在文件夹里的话这步是空操作，但只要中途从别处拖过新素材，这步是**必须**的，否则对方那边那几个 cue 就是红的。
2. 整个文件夹**压缩成 zip** 发过去。
3. 对方解压到任意位置，双击 `.qlab5` 打开。

`<工程名> backups` 文件夹是 QLab 自动生成的，不用发，可以删。

## 换机 checklist

| 坑 | 说明 |
|---|---|
| **音频输出设备** | 换机「没声音」的头号原因，且与路径无关。对方声卡不一样，要去 Workspace Settings → Audio 重新指定 patch |
| **QLab 版本** | 工程**不向下兼容**。5.6.3 存的工程，对方版本更老直接打不开 —— 让他先更新 |
| **全角冒号等文件名** | 文件名里的「：」（全角）在 Mac 之间没问题，但中途经过 Windows 或某些网盘可能被改名，改名后 QLab 就找不到了。**所以发 zip，不发散文件** |
| **OSC 密码** | workspace 里那个 4 位 OSC passcode 会跟着工程走。对方要用 iPad / 平板远程控制的话得告诉他 |
| **授权** | Audio cue 和 Fade cue 都在**免费版范围内**，实测未激活的免费版能正常播放。用到 Video / Light / Network cue 才需要授权 |

## 排查对方那边 cue 是红的

红 cue = `file target` 指向的文件不存在。用 AppleScript 逐个读回来对：

```applescript
tell application "QLab" to tell front workspace
  repeat with c in (cues of first cue list)
    -- 读 file target / broken 状态
  end repeat
end tell
```

九成是因为忘了做上面第 1 步（Copy media files into project folder），素材还留在原机的桌面上。


## 多人协作 / git 备份

`.qlab5` 是 Apple binary plist（NSKeyedArchiver），**git 无法三方合并**：两个人同时改了同一个总工程再 push，冲突只能整个文件二选一，输的那方改动全丢。对策：

1. 仓库放 `.gitattributes`：`*.qlab5 binary`，让 git 从不尝试文本合并，冲突时明确报"二选一"。
2. **每幕一个独立 .qlab5**（用 `scripts/split_workspace.py` 从总工程拆出来），放在各幕自己的 `Act N_ 剧名/` 文件夹里，谁负责哪幕就只改哪个文件，互不冲突。
3. 总工程只由一个人（或演出前一次）合并：同时打开总工程和单幕工程，在单幕工程的 cue list 里全选 cue（⌘A）→ ⌘C，到总工程对应 list 里 ⌘V。QLab 5 没有"导入 cue list"功能，复制粘贴是唯一的合并方式；粘贴过来的 cue 保留编号、名字、file target、fade 目标（目标 cue 在同一批粘贴里时会一起重定向）。
4. 编排配置（如 `qlab_act8_sequence.json`）也入库，最坏情况可以用 `build_act_into_list.py` 一键重建，不用手工。

合并的更省事的办法：不复制 cue，而是让每幕文件夹里的 `qlab_actN_sequence.json` 保持最新（`scripts/dump_sequence.py` 导出），汇总时在总工程里跑 `build_act_into_list.py` 重建那一幕。详见 `references/sequence_json.md`。
