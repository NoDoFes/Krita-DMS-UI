# 更新记录

## v0.1.2 - 2026-11-12

- 修复切换到非 Dank Shell 主题时崩溃
- 修复图层改名编辑器和原图层名错位 / 重影
- 热重载只处理用户目录的 matugen 配色，内置主题交给 Krita

安装：解压后把 `krita_dms_ui/` 和 `krita_dms_ui.desktop` 放到 Krita 的 `pykrita/` 目录，重启 Krita。

## v0.1.1 - 2026-11-12

- README / manual 增加两张界面示例图
- 示例图放进插件 `assets/examples/`，Manual 离线也能显示

## v0.1.0 - 2026-11-12

第一个整理过的版本。

- 全局 Material You 圆角、状态层、自绘勾选控件
- 跟随 Krita / matugen / DMS 调色板，支持深色 / 浅色
- 监听 `.colors` 热重载，换壁纸后不用重启
- 菜单、子菜单、右键菜单、ComboBox、tooltip 淡入淡出
- 菜单栏左对齐、SpinBox 箭头 SVG、欢迎页整理
- 补充来源说明和 GPL-3.0 许可证，插件管理器内置 manual.html

安装：解压后把 `krita_dms_ui/` 和 `krita_dms_ui.desktop` 放到 Krita 的 `pykrita/` 目录，重启 Krita。

已知问题见 README。
