# Trans-Prism-Builder 🏭

**云端内容构建与分发引擎** — 将 5 个异构上游 Wiki/文档仓库自动编译为离线 ZIP 包，供 [Trans Prism App](https://github.com/daanser/Trans-Prism) 消费。

[![GitHub](https://img.shields.io/badge/GitHub-Actions-2088FF?logo=githubactions)](https://github.com/features/actions)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE.txt)

---

## 🎯 它做什么？

本仓库本身不含 App 代码，是一条完全运行在 GitHub Actions 上的自动化流水线：

1. **每日定时** 监听 5 个上游开源仓库的版本变化
2. **自动拉取** 最新的 Markdown 源码与静态资源
3. **Python 工具链** 清洗异构框架语法（Hugo / VitePress / Vite），统一重排为 MkDocs 格式
4. **编译打包** 为 Material 主题的静态 HTML 站点 ZIP
5. **分发推送** 到 Cloudflare R2 边缘节点，供 App 热更新

---

## 📦 处理的项目

| 项目 | 上游仓库 | 框架 | 产物 |
|------|---------|------|------|
| **MtF Wiki** | [project-trans/MtF-wiki](https://github.com/project-trans/MtF-wiki) | Hugo | `mtf-wiki-site-{date}.zip` |
| **FtM Wiki** | [project-trans/FtM-wiki](https://github.com/project-trans/FtM-wiki) | Hugo | `ftm-wiki-site-{date}.zip` |
| **RLE Wiki** | [project-trans/RLE-wiki](https://github.com/project-trans/RLE-wiki) | VitePress | `rle-wiki-site-{date}.zip` |
| **MioMtF Wiki** | [KitsuMio/MioMtFWiki](https://github.com/KitsuMio/MioMtFWiki) | VitePress | `miomtfwiki-site-{date}.zip` |
| **HRT Tracker** | [SmirnovaOyama/Oyama-s-HRT-Tracker](https://github.com/SmirnovaOyama/Oyama-s-HRT-Tracker) | Vite+React | `hrt_tracker_update-{date}.zip` |

---

## 🔧 工具链概况

每个项目目录下有一套 Python 脚本组，按固定顺序执行：

```
clean_repo.py          → 工作区净化
compress_wiki.py       → PNG/JPG → WebP 瘦身
compress_webp.py       → 超大 WebP 二次降维
nuke_pdfs.py           → PDF 链接外置云端
fix_nav.py             → 生成侧边栏导航 .pages
fix_index.py           → _index.md → index.md
fix_yaml.py            → 删除 YAML 布尔炸弹
move_static.py         → 静态资源归并
fix_hugo_syntax.py     → Hugo 短码 → MkDocs Admonition（mtf/ftm/Mio）
fix_vite_syntax.py     → VitePress 容器 → MkDocs Admonition（rle 专属）
```

---

## ⏰ 构建触发

| Workflow | 触发 | 时间（北京时间） |
|----------|------|----------------|
| MtF / FtM / RLE / Tracker | Cron 每日 | 02:00~03:00 错峰 |
| Mio | Push（频率低） | 上游变化时 |
| R2 同步 | 上述任一完成后自动级联 | — |

每次构建会比对上游最新 Commit Hash 与本地 `last_sync_hash.txt`，**无变化则自动跳过**以节省 CI 资源。

---

## 📁 项目结构

```
.github/workflows/
├── build-mtf.yml             # MtF Wiki 构建
├── build-ftm.yml             # FtM Wiki 构建
├── build-rle.yml             # RLE Wiki 构建
├── build-mio.yml             # MioMtF Wiki 构建
├── build_tracker.yml         # HRT Tracker 构建
└── sync_builder_to_r2.yml    # R2 镜像分发

mtf/  ftm/  Mio/  rle/  tracker/     # 各项目目录
  ├── clean_repo.py                    # Python 工具脚本
  ├── compress_wiki.py
  ├── ...
  ├── mkdocs.yml                       # MkDocs 构建配置
  └── last_sync_hash.txt               # 上游 Commit 指纹（闭环）
```

---

## ⚖️ 开源许可

- **原创代码**：[Apache License 2.0](LICENSE.txt)
- **MtF/FtM/RLE Wiki 衍生**：[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
- **MioMtF Wiki 衍生**：[CC BY-ND 4.0](https://creativecommons.org/licenses/by-nd/4.0/)
- **HRT Tracker 衍生**：[MIT](https://opensource.org/licenses/MIT)

---

## 👨‍💻 开发者参考

| 想做什么 | 先去哪个文件 |
|----------|-------------|
| 增删上游项目 | 复制最接近的 build workflow + 在 `sync_builder_to_r2.yml` 加前缀 |
| 改清洗规则 | 对应项目的 `fix_hugo_syntax.py` / `fix_vite_syntax.py` |
| 改站点外观 | 各项目的 `mkdocs.yml`（主题配色） |
| 改侧边栏导航 | `fix_nav.py`（.pages 生成规则） |
| 改触发时间 | build workflow 的 `cron` 字段 |
| 了解完整契约 | [`REPO_MAP.md`](REPO_MAP.md)（AI Agent 导航）|

> ⚠️ **关键约束**：`use_directory_urls` 必须保持 `false`（App 离线加载依赖扁平 HTML）；ZIP/tag/前缀命名契约不可随意改（被客户端硬编码）。
