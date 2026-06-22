# Trans-Prism-Builder

Trans-Prism-Builder 是一个强大的、基于 GitHub Actions 驱动的自动化文档构建和打包分发引擎。它的主要目的是将分散在各个上游仓库中的 Wiki 与文档内容，经过系列复杂的自动化清理、转换与重新排版后，使用 **MkDocs (Material Theme)** 进行统一的静态网站构建，并自动打包为压缩包以 GitHub Releases 的形式进行每天的分发更新。

## 🎯 它做了什么？

整个构建流水线主要实现以下核心操作：

1. **版本差异追踪**：自动获取上游目标文档仓库的最新 Commit Hash，与本地 `last_sync_hash.txt` 记录对比。若无更新则直接跳过，节省 CI 资源。
2. **源码获取与重组**：使用无凭据劫持的方式获取并解压上游 `HEAD` 的归档文件，无缝提取所需目录下的源 Markdown 文件及静态资源。
3. **自动化 Python 工具链处理**：这是整个流程的核心，针对不同体系来源的 Markdown 文本进行“预处理”，从而兼容 MkDocs 严格的目录要求。
4. **编译与封包**：运用 MkDocs 驱动完成现代化的静态网站编译，然后将结果统一规范命名打包为 `.zip`，附带包含上游 Hash 的发布描述，推送到 GitHub Releases 页面，供外部源自动更新拉取。
5. **记录状态**：将最新构建的 Hash 伪装成 bot 操作推送到本仓库中作为下一次构建时的比对标杆，完成生命周期闭环。

## 🛠️ 处理的具体项目

该 Builder 目前支持对多个独立的维基或项目文档进行定时自动构建（通过独立分拆的 Workflow 实现错峰执行和处理）。包括但不限于：

- **FtM**
- **MtF**
- **Mio**
- **RlE**

每个项目的子目录下都有针对其特定源结构和规范量身定做的脚本组和 `mkdocs.yml` 配置。

## 🔧 Python 处理工具链

为了修正不同静态生成的框架（如 Hugo、VitePress 等）中互相不兼容的短代码与结构化语法，我们在对应项目的目录内编写了丰富的 Python 转换脚手架：

- `clean_repo.py` / `clean_rle_repo.py`：清理并重置工作空间，保证每次提取纯净状态。
- `compress_webp.py` / `compress_wiki.py`：对文章配图和其他位图资源进行无损 / 有损降维压缩，控制整站体积。
- `nuke_pdfs.py` / `nuke_icons.py`：智能剔除或者剥离无关的大体积非 Markdown 元素。
- `fix_hugo_syntax.py` / `fix_vite_syntax.py`：将其它框架私有的语法特征（比如高亮语块、特殊 Note 块或内嵌组件）通过正则转换回标准或 MkDocs Admonition 兼容形式。
- `fix_nav.py` / `fix_index.py` / `fix_yaml.py`：根据文章头部的 Front-Matter 动态修补或生成适用于 MkDocs-Awesome-Pages 的导航树。
- `move_static.py`：一键平移和融合外部静态资源。

## ⏰ 构建触发策略

所有项目均以 **GitHub Actions Cron 计划任务** 进行调度（通常是每日在凌晨不同的时段运行，从而进行错峰编排），同时也支持 `workflow_dispatch` 按钮一键手动介入和强行全量构建。

## ⚖️ 开源许可

*   **所有原创代码**：以 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 协议进行许可。
*   **MtF-Wiki, FtM-Wiki, Rle-Wiki 衍生内容**：严格继承上游的 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) 协议。
*   **Mio-Mtf-Wiki 衍生内容**：严格继承上游的 [CC BY-ND 4.0](https://creativecommons.org/licenses/by-nd/4.0/) 协议。
