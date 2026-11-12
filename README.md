# DMS Modern UI for Krita

给 Krita 换一套跟着 DankMaterialShell / matugen 走的 Material You 风格界面：圆角、低对比度、动态配色、菜单动画。

> 这是一个新人用 AI 辅助（vibecoding）一点点改出来的业余项目，不是专业作品。
> 代码和设计都还在学，可能有 bug，也可能有奇怪的地方。发现问题欢迎提 issue，不用期待专业级的维护速度。

当前版本：**0.1.0**（第一个整理过的版本）

项目基于 [Krita-MorandiUI](https://github.com/LanRhyme/Krita-MorandiUI) 继续改；MorandiUI 又基于 2020 年的 Krita UI Redesign（Kapyia、Pedro Reis）。本项目按 GPL-3.0 分发。

## 功能

- 从 Krita 的 `QPalette` 取色，跟随 matugen / DankMaterialShell，深色浅色都适配
- 菜单栏、工具栏、菜单、标签页、面板、输入框、滚动条统一圆角
- M3 状态层，勾选控件用 `QProxyStyle` 自绘
- 菜单、子菜单、右键菜单、ComboBox、tooltip 淡入淡出，时长跟随 DMS
- 换壁纸后监听 `.colors` 热重载配色，不用重启 Krita
- 欢迎页整理，SpinBox 箭头换成 SVG 图标
- `DMS UI` 菜单：菜单显隐、隐藏快捷键提示、动画开关

## 安装

把 `krita_dms_ui/` 和 `krita_dms_ui.desktop` 放进 Krita 的 `pykrita` 目录：

| 平台 | 路径 |
| :--- | :--- |
| Linux | `~/.local/share/krita/pykrita/` |
| Windows | `%APPDATA%\krita\pykrita\` |
| macOS | `~/Library/Application Support/Krita/pykrita/` |

Linux 从源码安装可以直接软链接：

```bash
git clone https://github.com/NoDoFes/Krita-DMS-UI.git
cd Krita-DMS-UI
mkdir -p ~/.local/share/krita/pykrita
ln -sfn "$PWD/krita_dms_ui" ~/.local/share/krita/pykrita/krita_dms_ui
ln -sfn "$PWD/krita_dms_ui.desktop" ~/.local/share/krita/pykrita/krita_dms_ui.desktop
```

然后打开 **设置 → 配置 Krita → Python 插件管理器**，勾选 **DMS Modern UI**，重启 Krita。

## 使用

菜单栏最右侧的 **DMS UI** 里可以：

- 显示 / 隐藏顶部菜单
- 隐藏菜单栏快捷键提示
- 开关菜单 / 下拉列表动画

换壁纸后颜色会自动刷新，不需要手动重载。

## 已知问题

- 主要是在 Krita 6.x / Linux 上试的，Krita 5 没充分测试
- 不要和 Krita-MorandiUI、Style Sheet Loader 等 UI 插件同时开
- 有些 Krita 自己画的控件改不到，只能单独补
- 热重载后颜色和 QSS 会立刻变，但部分 KDE 图标可能要重启 Krita
- 菜单淡出是把菜单最后一帧盖在主窗口上做的，超出主窗口的部分会被裁掉
- 勾选控件是 `QProxyStyle` 自绘的，切 Krita 样式后可能出现问题，还没完全验证

## 开发

改完代码重启 Krita 就能看到效果。检查用：

```bash
uvx ruff check .
python3 -m py_compile krita_dms_ui/*.py
```

## 来源与许可

- 本项目：[Krita-DMS-UI](https://github.com/NoDoFes/Krita-DMS-UI)
- 基于：[Krita-MorandiUI](https://github.com/LanRhyme/Krita-MorandiUI)
- MorandiUI 基于 2020 年的 **Krita UI Redesign**
  - 原作者：Kapyia、Pedro Reis
  - Copyright (C) 2020
  - GNU General Public License v3

本项目也按 **GPL-3.0** 分发，见 [LICENSE](LICENSE)。谢谢前面的作者。
