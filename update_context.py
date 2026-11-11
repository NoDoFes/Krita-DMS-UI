import os
import shutil
from pathlib import Path
from collections import defaultdict

# ================= 配置区 =================
ROOT_DIR = Path(__file__).parent.resolve()
BUNDLE_DIR = ROOT_DIR / "ai_context_bundle"
INDEX_FILE_NAME = "_00_CONTEXT_INDEX.md"

# 需要处理的开发文件后缀 (按需增减)
ALLOWED_EXTENSIONS = {'.py', '.qss', '.desktop', '.md', '.toml', '.json', '.txt', '.xml', '.ui', '.sh', '.svg'}

# 排除的目录 (不扫描)
EXCLUDE_DIRS = {'.git', '__pycache__', '.idea', '.vscode', 'ai_context_bundle', 'venv', '.env'}
# ==========================================

def main():
    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR)
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 收集所有符合条件的文件相对路径
    all_files = []
    print(f"🚀 开始扫描根目录: {ROOT_DIR}")

    for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        
        for filename in filenames:
            filepath = Path(dirpath) / filename
            if filepath.suffix.lower() not in ALLOWED_EXTENSIONS or filename.startswith('.'):
                continue
            if filename == 'update_context.py':
                continue
            all_files.append(filepath.relative_to(ROOT_DIR))

    # 2. 规划平铺文件名，解决重名冲突
    # 结构: {原始相对路径字符串: 平铺后的文件名}
    name_mapping = {}
    
    # 第一轮：先全部直接用基础文件名
    for rel_path in all_files:
        name_mapping[str(rel_path)] = rel_path.name

    # 第二轮：检查冲突，如果有冲突，把相对路径的 / 替换为 _ 
    # (例如: src/main.py -> src_main.py)
    used_names = set()
    final_mapping = {}
    
    for rel_path_str, flat_name in name_mapping.items():
        if flat_name in used_names:
            # 发生重名，使用完整路径扁平化
            # 比如: reference/config.json -> reference_config.json
            safe_name = rel_path_str.replace(os.sep, '_').replace('/', '_')
            final_mapping[rel_path_str] = safe_name
            used_names.add(safe_name)
        else:
            final_mapping[rel_path_str] = flat_name
            used_names.add(flat_name)

    # 3. 执行复制操作
    file_mappings = []
    for rel_path_str, flat_name in final_mapping.items():
        source_path = ROOT_DIR / rel_path_str
        target_path = BUNDLE_DIR / flat_name
        
        shutil.copy2(source_path, target_path)
        file_mappings.append((rel_path_str, flat_name))
        
        # 打印出来方便查看
        if rel_path_str != flat_name:
            print(f"  🔄 重名解决: {rel_path_str} -> {flat_name}")
        else:
            print(f"  📄 已收集: {rel_path_str}")

    # 4. 生成层级关系 MD 文件
    generate_index_md(file_mappings)
    print(f"\n✅ 打包完成！共收集 {len(file_mappings)} 个文件。")
    print(f"📂 查看目录: {BUNDLE_DIR}")

def generate_index_md(mappings):
    index_path = BUNDLE_DIR / INDEX_FILE_NAME
    
    # 按照原始路径排序，让树状结构更好看
    mappings.sort(key=lambda x: x[0])

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write("# 项目上下文索引 (Context Bundle Index)\n\n")
        f.write("> 此文件由 `update_context.py` 自动生成。\n")
        f.write("> 为了防止同名文件被覆盖，存在重名的文件在平铺时，其文件名会被替换为**完整相对路径（下划线连接）**。\n\n")
        
        f.write("## 📁 路径映射表\n\n")
        f.write("| 原始相对路径 | 平铺后的文件名 (Bundle内) |\n")
        f.write("| :--- | :--- |\n")
        
        for rel_path, flat_name in mappings:
            if rel_path != flat_name:
                f.write(f"| `{rel_path}` | **`{flat_name}`** |\n")
            else:
                f.write(f"| `{rel_path}` | `{flat_name}` |\n")
            
        f.write("\n## 🌳 原始目录树\n\n")
        f.write("```text\n")
        
        current_dir = None
        for rel_path, _ in mappings:
            # 处理路径
            rel_path_obj = Path(rel_path)
            dir_name = str(rel_path_obj.parent)
            if dir_name == '.': dir_name = ""
            
            if dir_name != current_dir:
                if dir_name:
                    depth = dir_name.count(os.sep) + dir_name.count('/')
                    indent = "  " * depth
                    f.write(f"{indent}📁 {Path(dir_name).name}/\n")
                current_dir = dir_name
            
            depth = str(rel_path_obj).count(os.sep) + str(rel_path_obj).count('/')
            indent = "  " * depth
            f.write(f"{indent}📄 {rel_path_obj.name}\n")
            
        f.write("```\n")

if __name__ == "__main__":
    main()