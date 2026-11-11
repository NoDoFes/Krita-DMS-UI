# DMS Modern UI for Krita

一个轻量的 PyKrita 界面插件：用纯 QSS + 少量 Python 补丁，给 Krita 换上圆角、低对比度的现代界面，并跟随系统 / Krita 主题调色板自动取色。

> 不修改 Krita 源码，不依赖外部 QSS 加载器，不需要额外安装任何包。

## ✨ 特性

- **动态跟随主题**：从 Krita 的 `QPalette` 提取背景色、基色、高亮色，自动区分明暗主题，适配 DankMaterialShell / matugen 等动态取色链路。
- **全局现代化样式**：菜单栏、工具栏、弹出菜单、标签页、图层面板、按钮、输入框、下拉框、滚动条、复选框等统一圆角风格。
- **M3 状态层**：hover 8%、focus 10%、禁用 38%，选中项使用 `primary-container` 柔和着色，避免整块主色实心块；颜色全部由 QPalette 派生。
- **表头 / 提示气泡**：补齐 `QHeaderView`、`QTableView`、`QToolTip` 等默认控件的暗色适配。
- **去除菜单黑边**：通过全局事件过滤器给 `QMenu` 打补丁，消除 Qt 经典黑边，保留圆角。
- **菜单弹出动画**：菜单栏下拉按 Material You 3 的节奏做淡入过渡（可开关），不再生硬弹出。
- **欢迎页统一风格**：重绘新建 / 打开按钮、最近文件列表和社区资源链接，去掉下划线与快捷键提示。
- **DMS UI 控制台**：在菜单栏最右侧新增 `DMS UI` 菜单，可以：
  - 显示 / 隐藏任意顶部菜单项（文件、编辑、视图……）
  - 隐藏菜单栏的快捷键提示
  - 手动重载当前主题色
- **启动优化**：全局 QSS 在启动时一次性注入，欢迎页、菜单文本等耗时操作延迟 1 秒后台执行，避免启动卡顿。
- **设置持久化**：菜单显隐等设置通过 Krita `readSetting / writeSetting` 保存，重启后仍然生效。

## 📦 安装

### 1. 找到 pykrita 目录

| 平台 | 路径 |
| :--- | :--- |
| Linux | `~/.local/share/krita/pykrita/` |
| Windows | `%APPDATA%\krita\pykrita\` |
| macOS | `~/Library/Application Support/Krita/pykrita/` |

目录不存在就手动创建。

### 2. 放入插件文件

需要把两样东西放进 `pykrita/`：

```text
pykrita/
├── krita_dms_ui/              # 插件包目录（名字不能改）
│   ├── __init__.py
│   ├── styles.py
│   ├── hacks.py
│   ├── menu_animation.py
│   ├── qt_compat.py
│   └── settings_ui.py
└── krita_dms_ui.desktop       # 插件声明文件
```

> ⚠️ 文件夹名必须是 `krita_dms_ui`，要和 `.desktop` 里的 `X-KDE-Library` 保持一致，否则 Krita 无法加载。

### 3. 从源码安装（Linux 开发推荐）

```bash
git clone https://github.com/NoDoFes/Krita-DMS-UI.git
cd Krita-DMS-UI

mkdir -p ~/.local/share/krita/pykrita
ln -sfn "$PWD/krita_dms_ui" ~/.local/share/krita/pykrita/krita_dms_ui
ln -sfn "$PWD/krita_dms_ui.desktop" ~/.local/share/krita/pykrita/krita_dms_ui.desktop
```

用软链接的好处是改完代码直接重启 Krita 就生效，不用反复复制。

### 4. 启用插件

1. 启动 Krita
2. 打开 **设置 → 配置 Krita → Python 插件管理器**
   （英文界面：`Settings → Configure Krita → Python Plugin Manager`）
3. 勾选 **DMS Modern UI**
4. 重启 Krita

如果列表里没有出现插件，通常是目录层级或 `.desktop` 文件名不对，检查第 2 步。

## 🎛️ 使用

启动后，菜单栏最右侧会出现 **DMS UI** 菜单：

- **显示/隐藏顶部菜单**：勾选控制各个顶部菜单项是否显示。即使把所有菜单都隐藏了，`DMS UI` 本身仍然保留，方便恢复。
- **隐藏菜单栏快捷键提示**：把菜单文字里的 `(Ctrl+X)` 之类提示去掉，界面更干净。
- **菜单弹出动画**：控制顶栏下拉的淡入过渡，默认开启。
- **🔄 重载当前主题色**：切换系统主题后，不需要重启 Krita，点一下即可重新读取调色板。

## 🧩 项目结构

```text
Krita_dmsUI/
├── krita_dms_ui/
│   ├── __init__.py       # 插件入口：注册 Extension、注入全局 QSS、调度耗时任务
│   ├── styles.py         # QSS 模板 + 主题色提取（get_theme_colors / build_qss）
│   ├── hacks.py          # 欢迎页补丁 + 菜单黑边 / 内嵌文字修复 + M3 勾选控件自绘
│   ├── menu_animation.py # 菜单栏下拉的 Material You 3 淡入动画
│   ├── qt_compat.py      # PyQt5 / PyQt6 兼容层（Qt 类与枚举常量统一入口）
│   └── settings_ui.py    # DMS UI 菜单、设置键、菜单显隐与快捷键提示
├── krita_dms_ui.desktop   # Krita 插件声明
├── update_context.py      # 开发辅助：打包扁平化上下文供 AI 使用
└── README.md
```

### 主题色是怎么来的

`styles.py` 的 `get_theme_colors()` **只读取 QPalette**（matugen / 系统主题注入），不再写死主题色：

- `Window` → `surface`，`WindowText` → `on-surface`（对比度不足 4.5:1 时回退黑 / 白）
- `Highlight` → `primary`，其上文字按 WCAG 对比度自动取黑 / 白
- 选中态统一为 `primary-container` / `on-primary-container`，并同步写回 `QPalette` 的 `Highlight` / `HighlightedText`：Qt 与 KDE 的 delegate（例如配置对话框左侧的 `KPageListViewDelegate`）只从调色板取文字色，不读 QSS 的 `color`
- 插件会缓存 matugen 注入的原始主色，避免改写 `Highlight` 之后再次推导时颜色逐次变暗
- `surface-container`、`outline`、`outline-variant` 由 `on-surface` 与 `surface` 混合得到
- hover / focus / disabled 分别用 8% / 10% / 38% 的状态层推导，边框不再写死 rgba
- 同时导出 M3 语义 token（`PRIMARY_CONTAINER`、`ON_SURFACE_VARIANT` 等），组件样式逐步迁移
- 勾选控件由 `QProxyStyle` 自绘，颜色同样来自 token：`PRIMARY` / `ON_PRIMARY` 画选中态，`OUTLINE` 画未选中边框，禁用态用 12% 容器与 38% 前景

想换整体配色，交给 matugen 注入即可；想调组件样式，改 `styles.py` 的 `MODERN_QSS` 模板。

## 🛠️ 开发

```bash
# 语法检查
python3 -m py_compile krita_dms_ui/*.py

# 生成 AI 上下文包（输出到 ai_context_bundle/，已被 .gitignore 忽略）
python3 update_context.py
```

调试时打开 Krita 的 **Python 控制台**（`工具 → Python 控制台` 或 `Tools → Python Console`）可以看到插件报错。

## ⚠️ 注意事项与已知限制

- **已验证环境**：Krita 6.x（Qt6 / PyQt6，Linux）。代码保留了 PyQt5 兼容分支，但主要在 Krita 6 上开发验证，Krita 5.x 尚未充分测试。
- **不要和其他 UI 插件同时启用**：例如 krita-morandiUI、Style Sheet Loader 等。全局 QSS 会互相覆盖，容易出现样式错乱。
- **部分控件不受 QSS 控制**：Krita 有不少 C++ 自绘控件（画布周边、部分色彩选择器等），需要针对 `objectName` 单独打补丁。
- **切换主题后自动刷新**：matugen 在运行中重新注入 `QPalette` 时会自动重载 QSS、选中态和欢迎页；也可以手动点 **DMS UI → 🔄 重载当前主题色**。插件记录的调色板签名包含 `Highlight` / `HighlightedText`，因此 Krita 用同一个 `.colors` 重放主题（例如打开画布后）也能被识别并自动修复。
- **部分控件只认调色板**：KDE 的 `KPageListViewDelegate`（配置对话框左侧栏）等自绘 delegate 不读 QSS 的 `color`，所以选中态的 `Highlight` / `HighlightedText` 由插件同步写入 `QPalette`，与 QSS 的 `primary-container` 保持一致。`KPageDialog` 在显示时还会显式套用当前应用调色板，并单独校正侧栏 `KPageListView`，避免从画布窗口继承到 matugen 的深色选中文字。
- **勾选控件是 M3 自绘**：QSS 画不出勾号和圆点，所以 `hacks.py` 里用 `QProxyStyle`（`IndicatorStyle`）绘制——checkbox 是圆角方形，选中为 `primary` 填充 + `on-primary` 勾号，不确定态画横杠；radio 是圆环 + 圆点，选中用 `primary`；`QTreeView` / `QListView` 的勾选复用同一套画法，尺寸小一号。颜色取自 `styles.get_indicator_colors()`，跟随主题切换，不引入 SVG / PNG。注意：Krita 的「样式」菜单会调用 `QApplication.setStyle()` 换掉代理样式，插件会在刷新 / 新窗口时自动重新包裹。
- **SpinBox / ComboBox 箭头暂未绘制**：自定义 `up/down-button` 后 Qt 不再画默认箭头，后续用 `QProxyStyle` 或 SVG 补。
- **低开销优先**：QSS token 单次遍历替换，菜单文字色按调色板缓存，欢迎页只在颜色变化时重绘，避免重复 `polish`。
- **菜单动画为最小实现**：目前只有顶栏下拉的淡入（200ms），不含位移 / 缩放 / 退出动画。动画使用 `QGraphicsOpacityEffect`（客户端渲染），在 Wayland 下同样生效；不想用时可在 `DMS UI → 菜单弹出动画` 关闭。
- **Qt 版本兼容**：PyQt5 / PyQt6 的枚举差异统一由 `qt_compat.py` 处理，新增代码请从这里导入 Qt 类和常量，不要再写裸 `QEvent.Type` / `Qt.WindowType`。
- **Qt QSS 不支持 `!important`**：写自定义样式时请用选择器优先级和书写顺序来控制覆盖关系，不要依赖 `!important`。

## 🗑️ 卸载

删除 `pykrita/` 下的 `krita_dms_ui/` 文件夹和 `krita_dms_ui.desktop` 文件，重启 Krita 即可。

## 📄 License

本项目尚未声明开源许可证。如需分发或二次发布，建议先补充一个 `LICENSE` 文件。
