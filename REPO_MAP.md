# Trans-Prism-Builder 架构地图 (REPO_MAP)

> 本文档基于对仓库源码的逐文件阅读生成，帮助 AI 快速理解内容构建流水线。
> 仓库是唯一真实来源；若文档与代码冲突，以代码为准。
> workspace 根目录另有 **开发辅助子系统** [`rag-system/`](../rag-system/mcp_bridge_bge.py:1)（RAG 知识库 MCP Bridge，供本地 AI Agent 检索生态文档），属 workspace 级组件、不属于本 Builder 仓库；其配置双写点（Zoo/Roo 两处 mcp.json）与 mcp 锁 1.x 约束见 ADR-011 与 SYSTEM_MAP 对应章节。

---

## 项目职责

Trans-Prism-Builder 是 Trans Prism 生态中的 **云端内容构建与分发引擎**。它本身不含 App 代码，而是作为一条"内容工厂"流水线存在，职责是：

1. **监听** 多个上游开源 Wiki / 文档 / 前端项目的版本变化。
2. **拉取** 上游 Markdown 与静态资源（绕过凭据，用 tarball 方式无损获取）。
3. **清洗** Hugo / VitePress / Vite 等异构框架的私有语法，统一重排为 MkDocs 兼容格式。
4. **编译** 为 Material 主题的纯静态 HTML 站点。
5. **打包** 为标准 ZIP，以日期为版本号发布到 GitHub Releases。
6. **镜像** 到 Cloudflare R2 对象存储，生成版本协商 JSON。
7. **闭环** 把上游 Commit Hash 回写为本地下次比对基准。

最终消费者是 Flutter 客户端 `Trans_Prism`，它通过 R2 直链拉取这些 ZIP 实现离线 Wiki 与 HRT Tracker 的热更新。Builder 解决了"多源异构内容 → 统一离线包"这一核心矛盾。

> **与 App 侧更新入口的边界**：Builder 只负责把 ZIP 推到 R2 并生成 `{proj}_latest.json`，不感知 App 内的触发方式。App 侧「我的 → 高级与系统 → 检查更新」手动入口（`Trans_Prism/lib/main.dart` 的 `_handleCheckUpdate`）与首页静默检测、Wiki 列表页批量检查共用同一批 R2 版本协商服务（`UpdateService` / `WikiUpdateManager`），对本仓库产物无任何特殊耦合。

---

## 数据流

```
上游仓库 (Hugo/VitePress/React 多源异构)
   │
   ├─ project-trans/MtF-wiki     (Hugo, content/)
   ├─ project-trans/FtM-wiki     (Hugo, content/)
   ├─ project-trans/RLE-wiki     (VitePress, docs/)
   ├─ KitsuMio/MioMtFWiki        (VitePress, docs/)
   └─ SmirnovaOyama/Oyama-s-HRT-Tracker (Vite/React, 整包前端)
   │
   ▼  [抓取]  git ls-remote 比对 Hash → curl tarball / git clone --depth 1
   │
   ▼  [清洗]  Python 工具链: clean → compress → nuke → fix_nav → fix_index → fix_yaml → move_static → fix_syntax
   │
   ▼  [标准化]  全部收敛为 content/ + .pages + 标准 Markdown (Admonition 语法)
   │
   ▼  [HTML生成]  mkdocs build (Material 主题) → site/
   │              Tracker 例外: 前端项目直接 npm run build → dist/
   │
   ▼  [封包]  zip -r {name}-site-{date}.zip  (附带上游 Hash 到 Release body)
   │
   ▼  [GitHub推送]  GitHub Releases (tag = {prefix}-{date})
   │
   ▼  [镜像分发]  sync_builder_to_r2.yml: Release → R2 上传 + 生成 {proj}_latest.json
   │              R2 布局: /builder/releases/{tag}/  +  /builder/latest/
   │
   ▼  [最终消费者]  Trans_Prism App
                   WikiUpdateManager → 拉 {wikiType}_latest.json 协商版本
                   → Dio 直链下载 ZIP → WikiOfflineService 阅后即焚解压
                   → FtmWikiManager / MtfWikiManager WebView 加载本地 HTML
```

---

## 文件职责地图

Builder 按上游项目分为 6 个子目录（`mtf/`、`ftm/`、`Mio/`、`rle/`、`tracker/`、`transmtf_tracker/`），每个目录内是一组针对该上游量身定制的脚本。`tracker/` 与 `transmtf_tracker/` 仅存指纹日志（走 npm 构建，无需 Python）。`ftm/` 与 `mtf/` 的脚本集几乎相同，`rle/` 与 `Mio/` 因上游用 VitePress 而有专属脚本。

### 通用脚本职责（以 mtf/ 为基准，各项目存在同名变体）

#### [`clean_repo.py`](Trans-Prism-Builder/mtf/clean_repo.py) — 工作区净化器
- **输入**：当前项目根目录（含刚解压的上游残留 + 自身脚本）
- **处理**：定义白名单（`content`、`static`、`mkdocs.yml`、`LICENSE`），保留所有 `.py` 与 `.md`，删除其余一切无用的上游构建产物、前端依赖、历史残留。
- **输出**：一块纯净的"画布"，只留核心 Markdown 源码与流水线脚本。
- **变体**：[`rle/clean_rle_repo.py`](Trans-Prism-Builder/rle/clean_rle_repo.py) 额外做一步"移花接木"——把上游 VitePress 的 `docs/` 重命名为 `content/`，以对接旧流水线。

#### [`compress_wiki.py`](Trans-Prism-Builder/mtf/compress_wiki.py) — 位图瘦身器（一次降维）
- **输入**：`content/` 与 `static/` 下的 `.png/.jpg/.jpeg` 位图
- **处理**：关闭 PIL 防解压炸弹限制（`Image.MAX_IMAGE_PIXELS = None`），宽超 1600px 用 LANCZOS 等比缩小，RGBA/P 模式转 RGB，统一转存为 quality=75 的 WebP，删除原图；最后遍历 `.md` 把 `.png/.jpg/.jpeg` 后缀引用替换为 `.webp`。
- **输出**：整站图片体积大幅下降的 Markdown 与配套 WebP 资源。

#### [`compress_webp.py`](Trans-Prism-Builder/mtf/compress_webp.py) — WebP 二次降维器
- **输入**：上一步产出的 `.webp` 文件
- **处理**：对任一边超过 2000px 的巨型 WebP 按最长边等比缩放，LANCZOS 重采样，quality=75 覆盖原文件。
- **输出**：彻底"老实"的手机端友好尺寸图片，控制离线包体积。

#### [`nuke_pdfs.py`](Trans-Prism-Builder/mtf/nuke_pdfs.py) — PDF 链接外置器
- **输入**：`content/` 下引用 `.pdf` 的 Markdown 文件
- **处理**：用正则匹配标准 Markdown 链接 `[text](path/file.pdf)` 与 HTML `<a href="...file.pdf">`，把本地路径重定向到远程基址（`https://mtf.wiki/static/documents/{filename}`），把几十 MB 的 PDF 推回云端。
- **输出**：不含大体积 PDF 的离线包，PDF 改为在线访问。

#### [`fix_nav.py`](Trans-Prism-Builder/mtf/fix_nav.py) — 侧边栏导航重构器
- **输入**：`content/` 目录树
- **处理**：清空所有旧 `.pages`；顶级语言目录套国旗 emoji 标签（如 `zh-cn → 🇨🇳 简体中文`）；子目录依次尝试从入口文件（`index.md/_index.md/readme.md`）抓取 YAML `title:` 或 Markdown 一级标题 `# ` 作为侧边栏节点名；内置"防复读机"拦截网，避免把全局站点名误当作章节名。
- **输出**：为每个含合法标题的目录生成 `.pages`（`title: '中文名'`），供 mkdocs-awesome-pages-plugin 渲染侧边栏。
- **注意**：`rle/fix_nav.py` 与 `mtf/fix_nav.py` 仅"防复读机"关键字不同（ftm.wiki vs mtf.wiki）。

#### [`fix_index.py`](Trans-Prism-Builder/mtf/fix_index.py) — 入口文件正名器
- **输入**：全项目文件树（避开 `site/.git/assets`）
- **处理**：把上游的 `_index.md` 与 `readme.md` 统一重命名为 MkDocs 要求的 `index.md`，使其成为目录默认入口页。
- **输出**：符合 MkDocs 目录约定的入口命名。

#### [`fix_yaml.py`](Trans-Prism-Builder/mtf/fix_yaml.py) — YAML 布尔排雷器
- **输入**：`content/` 下含 Front-Matter 的 Markdown
- **处理**：正则删除独占一行的 `hide: true/false`（不区分大小写）——该字段会让 MkDocs 直接隐藏整页甚至猝死构建。
- **输出**：去除致命布尔炸弹的安全 Markdown。

#### [`move_static.py`](Trans-Prism-Builder/mtf/move_static.py) — 静态资源归并器
- **输入**：根目录 `static/` 与 `content/`
- **处理**：把根 `static/` 移入 `content/static/`，使图片资源随 Markdown 一起被 MkDocs 收录；含冲突预清理逻辑。
- **输出**：统一的 `content/static/` 静态资源布局。

#### [`fix_hugo_syntax.py`](Trans-Prism-Builder/mtf/fix_hugo_syntax.py) — Hugo 短码翻译器（mtf/ftm/Mio）
- **输入**：`content/` 下含 Hugo 短码的 Markdown
- **处理**：四类翻译——
  1. `{{< notice warning "标题" >}}` → MkDocs `!!! warning "标题"`（内容缩进 4 空格）；
  2. 图片路径标准化为 `/static/...` 绝对路径（覆盖 Markdown 图片、`{{< hiddenphoto >}}`、`<img>` 标签）；
  3. `{{< wiki Novartis en >}}` → 维基百科标准链接；
  4. `{{< ref "risk" >}}` → `[risk](risk.html)`。
- **输出**：Hugo 短码全部转译为 MkDocs 兼容语法的 Markdown。

#### [`fix_vite_syntax.py`](Trans-Prism-Builder/rle/fix_vite_syntax.py) — VitePress 语法翻译器（rle 专属）
- **输入**：`content/` 下含 VitePress 语法的 Markdown
- **处理**：物理删除 `<script setup>` 块与 `<HomeContent>` 自定义标签；把 VitePress 的 `::: tip 标题 / 内容 / :::` 容器转为 MkDocs `!!! tip "标题"` + 4 空格缩进体。
- **输出**：VitePress 专属语法清洗为 MkDocs 兼容形式。

#### [`nuke_icons.py`](Trans-Prism-Builder/rle/nuke_icons.py) — VitePress 图标配置剥离器（rle 专属）
- **输入**：`content/` 下含 `icon:` 字段的 Markdown
- **处理**：删除 YAML 头里的 `icon: xxx` 行，避免 MkDocs 找不到对应 SVG 而报错。
- **输出**：去除图标引用炸弹的安全 Markdown。

### 非脚本状态文件

| 文件 | 职责 |
|------|------|
| [`mkdocs.yml`](Trans-Prism-Builder/mtf/mkdocs.yml) 等 | MkDocs 构建配置（站点名、docs_dir、Material 主题、markdown_extensions、awesome-pages 插件）|
| `last_sync_hash.txt` | 记录上次成功构建时上游 HEAD 的 Commit Hash，作为下次"Cron 跳过判定"的比对基准 |
| [`LICENSE.txt`](Trans-Prism-Builder/LICENSE.txt) | Apache 2.0 原创代码授权 |

---

## Workflow地图

所有 Workflow 位于 [`.github/workflows/`](Trans-Prism-Builder/.github/workflows/)。构建类 Workflow 共享同一骨架：Checkout → Check Hash（短路）→ Clone → Setup Python/Node → 装依赖 → 跑 Python 工具链 → mkdocs build → Zip → Release → Commit Sync Log。

### 1. [`build-mtf.yml`](Trans-Prism-Builder/.github/workflows/build-mtf.yml) — MtF Wiki 构建
- **触发**：`cron: '0 18 * * *'`（UTC 18:00 = 北京 02:00）每日定时；`workflow_dispatch` 手动
- **上游**：`https://github.com/project-trans/MtF-wiki.git`（Hugo，`content/`）
- **执行**：curl 拉 tarball 解出 `content/` 与 `static/`；Python 工具链顺序：clean → compress_wiki → compress_webp → nuke_pdfs → fix_nav → fix_index → fix_yaml → move_static → fix_hugo_syntax；`mkdocs build`
- **产出**：ZIP `mtf-wiki-site-{date}.zip`，tag `mtf-{date}`，Release body 含上游 Hash

### 2. [`build-ftm.yml`](Trans-Prism-Builder/.github/workflows/build-ftm.yml) — FtM Wiki 构建
- **触发**：`cron: '10 18 * * *'`（北京 02:10）错峰；`workflow_dispatch`
- **上游**：`https://github.com/project-trans/FtM-wiki.git`（Hugo，`content/`）
- **执行**：与 mtf 几乎相同，工具链顺序略调（move_static 提前到 compress 之前）
- **产出**：ZIP `ftm-wiki-site-{date}.zip`，tag `ftm-{date}`

### 3. [`build-rle.yml`](Trans-Prism-Builder/.github/workflows/build-rle.yml) — RLE Wiki 构建
- **触发**：`cron: '20 18 * * *'`（北京 02:20）错峰；`workflow_dispatch`
- **上游**：`https://github.com/project-trans/RLE-wiki.git`（VitePress，源码在 `docs/`，克隆时已 `mv docs ./content`）
- **执行**：专属工具链：clean_rle_repo → compress_wiki → compress_webp → fix_index → fix_nav → fix_yaml → nuke_pdfs → **fix_vite_syntax** → **nuke_icons**（无 fix_hugo_syntax、无 move_static）
- **产出**：ZIP `rle-wiki-site-{date}.zip`，tag `rle-{date}`

### 4. [`build-mio.yml`](Trans-Prism-Builder/.github/workflows/build-mio.yml) — MioMtF Wiki 构建
- **触发**：`push` 到 `main/master` 分支（非 Cron！因 Mio 上游更新频率低）；`workflow_dispatch`
- **上游**：`https://github.com/KitsuMio/MioMtFWiki.git`（VitePress，`docs/`）
- **执行**：working-directory 是仓库根（非 `./Mio`）；上游 `docs/` 留在根；工具链用 `python Mio/xxx.py` 形式调用；构建时把 `Mio/mkdocs.yml` 拷到根再 `mkdocs build`（因其 `docs_dir: docs` 相对根）。
- **产出**：ZIP `miomtfwiki-site-{date}.zip`，tag `build-{date}`（前缀用 miomtfwiki）
- **特殊点**：脚本用 Hugo 翻译器 `fix_hugo_syntax.py`（Mio 上游虽是 VitePress 文档但内含 Hugo 短码），无 move_static

### 5. [`build_tracker.yml`](Trans-Prism-Builder/.github/workflows/build_tracker.yml) — Oyama HRT Tracker 构建
- **触发**：`cron: '0 19 * * *'`（UTC 19:00 = 北京 03:00）；`workflow_dispatch`
- **上游**：`https://github.com/SmirnovaOyama/Oyama-s-HRT-Tracker.git`（Vite + React 前端项目，非 Wiki）
- **执行**：**Node.js 20 而非 Python**；`git clone --depth 1`；用内联 Python 给 `vite.config.ts` 注入 `base: './'`（相对路径，供 App 离线 WebView 加载）；`npm install && npm run build`；打包 `dist/`
- **产出**：ZIP `hrt_tracker_update-{date}.zip`，tag `tracker-{date}`，用 `gh release create`
- **特殊点**：不经过 MkDocs，是纯前端构建；指纹日志写到 `tracker/last_sync_hash.txt`

### 6. [`build_transmtf_tracker.yml`](Trans-Prism-Builder/.github/workflows/build_transmtf_tracker.yml) — TransMTF HRT Tracker 构建
- **触发**：`cron: '30 19 * * *'`（UTC 19:30 = 北京 03:30）接在 Oyama Tracker 之后错峰；`workflow_dispatch`
- **上游**：`https://github.com/TransmtfTeam/Transmtf-HRT-Tracker.git`（Vite + React + TypeScript，含 react-router-dom v7 多路由 SPA）
- **执行**：Node.js 20；`git clone --depth 1`；用内联 Python 注入 `base: './'`（相对路径）→ Python 剥离 import map + Tailwind CDN（强制 Vite bundle 全部依赖）→ `npm install && npm run build` → **Python 注入缺失 CSS 变量（`:root` 主题/glass/animation 类，上游 inline `<style>` 丢失兜底）** → Python 剥离 PWA Service Worker 注册 → 打包 `dist/`
- **产出**：ZIP `transmtf_tracker_update-{date}.zip`，tag `transmtf_tracker-{date}`，用 `gh release create`
- **特殊点**：不经过 MkDocs，是纯前端构建；剥离 import map + Tailwind CDN（消除运行时 CDN 依赖）→ Vite 从 node_modules bundle 全部依赖；额外剥离 `vite-plugin-pwa` 生成的 Service Worker（避免 WebView 内缓存冲突）；**PostCSS Tailwind 生成的 CSS 不含上游 inline `<style>` 块中的主题变量（`--bg-overlay`/`--bg-card`/`--text-primary` 等）与玻璃效果类（`glass-heavy`/`glass-noise`/`glass-card`），后注入步骤在 `dist/assets/*.css` 前插入 fallback 定义**；指纹日志写到 `transmtf_tracker/last_sync_hash.txt`

### 7. [`sync_builder_to_r2.yml`](Trans-Prism-Builder/.github/workflows/sync_builder_to_r2.yml) — R2 分发器
- **触发**：`workflow_run`——当上述 6 个构建 Workflow **任一 completed** 时自动级联；`workflow_dispatch` 手动测试
- **执行**：遍历 6 个项目前缀（`tracker transmtf_tracker mtf ftm rle miomtfwiki`），用 `gh api` + `jq` 找出该前缀的最新 tag，下载其 Release 资产；上传到 R2 `builder/releases/{tag}/`（版本归档）；清理 R2 `builder/latest/` 下该前缀旧 `.zip`；生成 `{proj}_latest.json`（含 `latest_file`/`tag`/`update_time`）；同步到 `builder/latest/`。
- **产出**：R2 上的版本归档目录 + 最新版 ZIP + 版本协商 JSON（客户端热更新契约）

---

## 内容Schema

### MkDocs 站点统一结构（MtF/FtM/RLE/Mio）

所有 Wiki 类项目最终编译为同构的 Material 站点：

```
site/
  index.html              ← 首页
  {page}.html             ← use_directory_urls: false，扁平文件名
  assets/
    javascripts/          ← Material 主题 JS
    stylesheets/          ← Material 主题 CSS
  search/                 ← 搜索索引
  static/                 ← 图片/WebP（路径已被 fix_hugo_syntax 标准化为 /static/...）
  404.html
```

关键配置项（见 [`mtf/mkdocs.yml`](Trans-Prism-Builder/mtf/mkdocs.yml) / [`rle/mkdocs.yml`](Trans-Prism-Builder/rle/mkdocs.yml) / [`Mio/mkdocs.yml`](Trans-Prism-Builder/Mio/mkdocs.yml)）：

| 配置项 | 值 / 含义 |
|--------|-----------|
| `docs_dir` | `content`（mtf/ftm/rle）或 `docs`（Mio，因上游源码留在根） |
| `use_directory_urls` | `false` → 生成扁平 `{page}.html` 而非 `{page}/index.html`，适配 App 内 WebView 的相对路径加载 |
| `theme.name` | `material`（MkDocs Material 主题）|
| `theme.language` | `zh` |
| `theme.palette` | `primary: indigo` / `accent: indigo` |
| `markdown_extensions` | `admonition`、`pymdownx.details`、`pymdownx.superfences`、`toc.permalink`、`attr_list`、`md_in_html` |
| `plugins` | `search` + `awesome-pages`（读取各目录生成的 `.pages` 渲染侧边栏）|

### 模板机制

Builder **不使用自定义 HTML 模板**。它的"模板"实际上是：

1. **MkDocs Material 官方主题**：提供统一的视觉外壳（侧边栏、搜索、配色）。
2. **`.pages` 元文件**：由 [`fix_nav.py`](Trans-Prism-Builder/mtf/fix_nav.py) 动态生成的导航契约，控制侧边栏节点标题与排序，是 awesome-pages 插件的实际数据源。
3. **Markdown 翻译规则**：`fix_hugo_syntax.py` / `fix_vite_syntax.py` 中的正则就是隐式"模板"——把异构语法映射到 MkDocs Admonition（`!!! type "title"` + 4 空格缩进）这一统一目标格式。

### Tracker 特殊结构

HRT Tracker（Oyama / TransMTF）不走 MkDocs，而是 Vite 构建的 SPA：
```
hrt_tracker_update-{date}.zip  (内含 dist/)
  index.html
  assets/index-{hash}.js / .css
  manifest.webmanifest, sw.js, registerSW.js  (PWA)
```
或
```
transmtf_tracker_update-{date}.zip  (内含 dist/)
  index.html
  assets/index-{hash}.js / .css
  manifest.webmanifest, sw.js, registerSW.js  (PWA)
```
其"模板"是上游仓库自带的 React 组件与 Vite 配置，Builder 仅注入 `base: './'` 以支持离线相对加载。
TransMTF 额外执行一步 PWA Service Worker 剥离，避免 WebView 内缓存状态与 App 热更新机制冲突。

### Release / 版本命名契约

| 项目 | ZIP 名 | Tag | R2 前缀 | 客户端 wikiType |
|------|--------|-----|---------|-----------------|
| MtF | `mtf-wiki-site-{date}.zip` | `mtf-{date}` | mtf | mtf |
| FtM | `ftm-wiki-site-{date}.zip` | `ftm-{date}` | ftm | ftm |
| RLE | `rle-wiki-site-{date}.zip` | `rle-{date}` | rle | rle |
| Mio | `miomtfwiki-site-{date}.zip` | `build-{date}` | miomtfwiki | miomtfwiki |
| Oyama Tracker | `hrt_tracker_update-{date}.zip` | `tracker-{date}` | tracker | tracker |
| TransMTF Tracker | `transmtf_tracker_update-{date}.zip` | `transmtf_tracker-{date}` | transmtf_tracker | transmtf_tracker |

R2 上每个项目维护一份 `{prefix}_latest.json`：
```json
{ "latest_file": "mtf-wiki-site-2026-06-24.zip", "tag": "mtf-2026-06-24", "update_time": "2026-06-24T02:57:29Z" }
```

---

## 与主项目关系

### Builder 生成什么

- **Wiki 离线包**：mtf / ftm / rle / miomtfwiki 四个 MkDocs 静态站点 ZIP
- **HRT Tracker 离线包**：tracker（Oyama）的 Vite build 产物 ZIP
- **TransMTF HRT Tracker 离线包**：transmtf_tracker 的 Vite build 产物 ZIP
- **版本协商 JSON**：R2 上各项目的 `{prefix}_latest.json`

### 主项目消费什么

Flutter 客户端 `Trans_Prism` 通过两个服务消费 Builder 产物：

1. **[`WikiUpdateManager`](Trans_Prism/lib/services/wiki_update_manager.dart:31)** — R2 热更新引擎
   - 向 `{baseUpdateUrl}/builder/latest/{wikiType}_latest.json` 协商版本
   - 从 tag 用正则 `\d{4}-\d{2}-\d{2}` 萃取日期，与本地版本（`.version` 文件）比对
   - Dio 流式直链下载 ZIP 到 `offline_wiki/`，重命名为标准名 `{wikiType}-wiki-site.zip`
   - 支持后台静默热更新（`checkAndPerformHotUpdate`）与前台带进度下载

2. **[`WikiOfflineService`](Trans_Prism/lib/services/wiki_offline_service.dart:23)** — 阅后即焚解压器
   - 把 ZIP 现场解压到 `live_{wikiType}_site/`，精准探测站点根（优先找含 `index.html` 的子目录，兜底找含 `assets/` 的层级——这正是 MkDocs 站点结构）
   - 关闭即焚：退出时清理临时解压目录，只保留 ZIP
   - 管理版本日志 `.{wikiType}-wiki-site.version`

3. **[`FtmWikiManager`](Trans_Prism/lib/wiki/ftm_wiki/ftm_wiki_manager.dart:5)** 等 Wiki Manager — 前端加载器
   - 优先返回热更新沙盒路径 `live_{wikiType}_site/{wikiType}-wiki-site`，无则回退 ZIP 解压
   - 交给 WebView 加载本地 HTML

4. **[`WikiSyncService`](Trans_Prism/lib/services/wiki_sync_service.dart:37)** — 在线/离线策略仲裁
   - 后台戳 GitHub API 对比上游 Commit SHA（与 Builder 的 Hash 比对思路同源）
   - 决定 WebView 优先用本地缓存还是在线站点

### 数据如何流动（端到端闭环）

```
Builder Releases ──sync──→ R2 (builder/latest/) ──latest.json 协商──→ App WikiUpdateManager
                                                                       │
                          App WikiOfflineService ←── Dio 下载 ZIP ─────┘
                                  │ 阅后即焚解压
                                  ▼
                          live_{type}_site/  ──WebView file://──→ 用户
```

Builder 的 `last_sync_hash.txt`（上游指纹）与 App 的 `.{type}-wiki-site.version`（构建日期）是两条独立的版本状态线，前者驱动 Builder 是否重新构建，后者驱动 App 是否重新下载。

---

## Agent开发建议

### 修改内容抓取（新增/更换上游源）

1. **先看** 对应项目的 build workflow（如 [`build-mtf.yml`](Trans-Prism-Builder/.github/workflows/build-mtf.yml:27)）的 `UPSTREAM_URL` 与 `Clone Upstream Wiki` 步骤——这里决定上游地址与解压后 `content`/`docs`/`static` 的映射。
2. **再看** [`clean_repo.py`](Trans-Prism-Builder/mtf/clean_repo.py:8)（或 [`clean_rle_repo.py`](Trans-Prism-Builder/rle/clean_rle_repo.py:8)）的白名单——若上游新增了需保留的目录，必须在此放行，否则会被当垃圾粉碎。
3. 上游若用新框架（非 Hugo/VitePress），需新建专属 `fix_{framework}_syntax.py`，参考 [`fix_hugo_syntax.py`](Trans-Prism-Builder/mtf/fix_hugo_syntax.py) 与 [`fix_vite_syntax.py`](Trans-Prism-Builder/rle/fix_vite_syntax.py) 的正则翻译范式，并在 workflow 的 `Run Python Toolchain` 步骤中按序插入。

### 修改 HTML 模板 / 站点外观

1. **改主题与配色**：编辑各项目的 [`mkdocs.yml`](Trans-Prism-Builder/mtf/mkdocs.yml:5)（`theme.palette`、`theme.features`）。所有 Wiki 项目共享相同 Material 配置模板，改一处可对照同步到其余三个。
2. **改侧边栏导航逻辑**：改 [`fix_nav.py`](Trans-Prism-Builder/mtf/fix_nav.py:9) 的 `lang_map`（顶级语言标签）与标题提取正则——这是 `.pages` 的生成规则，决定了用户看到的导航树。
3. **改页面入口命名规则**：改 [`fix_index.py`](Trans-Prism-Builder/mtf/fix_index.py:16) 的重命名目标（当前 `_index.md/readme.md → index.md`）。
4. **注意**：`use_directory_urls: false` 是 App WebView 相对路径加载的前提，轻易不要改为 true，否则 App 内链接会大面积 404。

### 修改 Workflow

1. **改触发时间/错峰**：直接改各 build workflow 的 `cron`，注意前缀为 UTC，且 6 个项目当前按 02:00/02:10/02:20/03:00/03:30 错峰，避免 R2 同步级联拥堵。
2. **改工具链顺序**：在 `Run Python Toolchain` 步骤调整 `python xxx.py` 调用顺序——记住"先 clean 再压缩、先 move_static 再 fix 语法"的依赖：`fix_hugo_syntax` 依赖 `content/static` 已就位，所以 `move_static` 须在其前。
3. **新增项目**：复制一个最接近的 workflow（Hugo 系抄 mtf，VitePress 系抄 rle），改 `UPSTREAM_URL`、`working-directory`、ZIP/tag 命名前缀；然后在 [`sync_builder_to_r2.yml`](Trans-Prism-Builder/.github/workflows/sync_builder_to_r2.yml:25) 的 `PROJECTS` 数组加入新前缀；最后在主项目 App 的 `WikiCatalog` 注册新 wikiType 与 R2 base URL。
4. **Tracker 类前端项目**：参考 [`build_tracker.yml`](Trans-Prism-Builder/.github/workflows/build_tracker.yml) 的 Node 流程与 `base: './'` 注入逻辑，不要套用 MkDocs 工具链。

### 关键约束（修改时务必遵守）

- **命名契约不可随意改**：ZIP/tag/前缀三者的对应关系（见"内容Schema"表）被主项目 [`WikiUpdateManager`](Trans_Prism/lib/services/wiki_update_manager.dart:99) 的 URL 拼接硬编码，改任一处需联动改客户端。
- **`use_directory_urls` 必须保持 false**：App 的 [`WikiOfflineService.extractZipToTemp`](Trans_Prism/lib/services/wiki_offline_service.dart:114) 依赖扁平 HTML 结构探测站点根。
- **上游 Hash 回写**：`Commit Sync Log` 步骤是闭环关键，且用 `git reset --soft FETCH_HEAD` 防冲突，删改该步骤会导致 Cron 永远全量构建或永远跳过。
- **`Image.MAX_IMAGE_PIXELS = None`**：上游含亿像素医疗图，禁用 PIL 防炸弹限制是有意为之，勿恢复默认值。
