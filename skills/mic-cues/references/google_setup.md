# 给文档主人：让脚本能读写你的 Google Doc（约 5 分钟，一次性）

原理：不需要给任何人你的 Google 账号密码。你在自己的 Google Cloud 里建一个"机器人账号"（服务账号），
把剧本文档像分享给同事一样分享给它，脚本用它的密钥文件登录，只能碰你分享给它的文档。

## 1. 建项目
打开 https://console.cloud.google.com/projectcreate ，用你自己的 Google 账号登录，项目名随意（例如 `doc-editor`），Create。
建好后页面顶部选中这个新项目。

## 2. 开 Google Docs API
打开 https://console.cloud.google.com/apis/library/docs.googleapis.com ，确认左上角是刚建的项目，点 **Enable**。
（脚本报 `Google Docs API has not been used in project … or it is disabled` 就是这步没做；报错里带的链接直接点 Enable 即可，等一两分钟生效。
如果链接打开显示 "You need additional access / resourcemanager.projects.get"，说明浏览器登录的不是建项目的那个 Google 账号，右上角头像切换。）

## 3. 建服务账号并下载密钥
1. 打开 https://console.cloud.google.com/iam-admin/serviceaccounts ，Create service account，名字如 `docs-editor`，一路 Done，**不用**授予任何角色。
2. 点进这个服务账号 → Keys 标签 → Add key → Create new key → JSON → 下载。
3. 把下载的 json 放到 `~/.slock/tokens/google_docs_sa.json`（或任意路径，然后 `export GDOC_SA_KEY=/那个/路径`），`chmod 600`。
4. 记下 json 里的 `client_email`，形如 `docs-editor@doc-editor-xxxxxx.iam.gserviceaccount.com`。

不要把这个 json 贴进聊天、提交进 git、发进群。贴过就去 Keys 里删掉重建一把。

## 4. 把文档分享给服务账号
在 Google Doc 右上角 **Share** → 填上面的 `client_email` → 权限 **Editor** → 取消"Notify"→ Send。
每一份要处理的文档都要单独分享。只读检查也可以给 Viewer，但写状态行需要 Editor。

## 5. 验证
```bash
uv run --with google-api-python-client --with google-auth python3 scripts/gdoc_mic_cues.py dump <文档id> --work /tmp/w
```
文档 id 是链接里 `/d/` 和 `/edit` 之间那串。能打印出标题和 mic 行就通了。

常见报错：
- `403 … has not been used in project / is disabled` → 第 2 步没做。
- `403 The caller does not have permission`（读得到、写不进）→ 第 4 步只给了 Viewer 或没分享；读得到是因为链接对所有人可见。
- `404` → 文档 id 抄错，或文档没对外分享也没分享给服务账号。

## 6. 完事以后
项目和服务账号可以一直留着复用。要收回权限：在文档 Share 里移除那个邮箱，或去 Keys 删掉密钥。
