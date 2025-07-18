import os
import argparse
from typing import List, Set, Dict, Any

# 尝试导入 colorama
try:
    import colorama
    from colorama import Fore, Style
    colorama.init(autoreset=True)
    COLOR_DIR = Fore.CYAN
    COLOR_FILE_MATCH = Fore.GREEN
    KEYWORD_COLORS = [Fore.YELLOW, Fore.RED, Fore.BLUE, Fore.CYAN,Fore.MAGENTA]
    STYLE_RESET = Style.RESET_ALL
except ImportError:
    class EmptyColor:
        def __getattr__(self, name): return ""
    Fore = EmptyColor()
    Style = EmptyColor()
    COLOR_DIR, COLOR_FILE_MATCH, STYLE_RESET = "", "", ""
    KEYWORD_COLORS = ["", "", "", "", ""]
    print("[提示] 未找到 'colorama' 库,输出将不带颜色.建议运行: pip install colorama")

# --- 新增:只在这些扩展名的文件中搜索 ---
# 您可以根据需要添加更多文本或代码文件的扩展名
TEXT_EXTENSIONS = {
    # 纯文本 & 文档
    '.txt', '.md', '.rst', '.log', '.csv', '.tsv', '.tex', '.json', '.xml', 
    '.yaml', '.yml', '.toml', '.ini', '.cfg',
    # 编程语言
    '.c', '.h', '.cpp', '.hpp', '.cs', '.java', '.py', '.pyw', '.rb', '.go', 
    '.rs', '.swift', '.kt', '.kts', '.scala', '.pl', '.pm', '.sh', '.bash', 
    '.zsh', '.ps1', '.lua',
    # Web 开发
    '.html', '.htm', '.css', '.scss', '.sass', '.less', '.js', '.mjs', '.cjs', 
    '.ts', '.tsx', '.jsx', '.vue', '.svelte', '.php', '.phtml', '.sql'
}

# 默认排除的目录名称列表
DEFAULT_EXCLUDE_NAMES = {
    '.git', '.idea', '.vscode', 'node_modules', '__pycache__', 'build', 'dist', 'target'
}

def find_keywords_in_file(file_path: str, keywords: List[str], case_insensitive: bool, mode: str) -> Set[str]:
    """检查单个文件中是否包含关键字."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except (IOError, OSError):
        return set()

    content_to_search = content.lower() if case_insensitive else content
    
    found_keywords = set()
    if mode == 'ANY':
        for keyword in keywords:
            keyword_to_search = keyword.lower() if case_insensitive else keyword
            if keyword_to_search in content_to_search:
                found_keywords.add(keyword)
        return found_keywords
    
    elif mode == 'ALL':
        all_found = True
        for keyword in keywords:
            keyword_to_search = keyword.lower() if case_insensitive else keyword
            if keyword_to_search not in content_to_search:
                all_found = False
                break
        return set(keywords) if all_found else set()

    return set()

def collect_matches(root_dir: str, keywords: List[str], case_insensitive: bool, exclude_names: Set[str], exclude_paths: Set[str], mode: str) -> List[Dict]:
    """第一阶段:遍历文件系统,只收集匹配项,不打印."""
    matches = []
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in exclude_names]
        dirs_to_keep = []
        for d in dirnames:
            if os.path.abspath(os.path.join(dirpath, d)) not in exclude_paths:
                dirs_to_keep.append(d)
        dirnames[:] = dirs_to_keep

        for filename in filenames:
            # --- 修改:只检查具有文本扩展名的文件 ---
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in TEXT_EXTENSIONS:
                file_path = os.path.join(dirpath, filename)
                found_keywords = find_keywords_in_file(file_path, keywords, case_insensitive, mode)
                if found_keywords:
                    matches.append({'path': file_path, 'keywords': found_keywords})
    return matches

def build_file_tree(matches: List[Dict], root_dir: str) -> Dict:
    """根据匹配列表构建一个嵌套字典来表示文件树."""
    tree = {}
    for match in matches:
        relative_path = os.path.relpath(match['path'], root_dir)
        parts = relative_path.split(os.sep)
        current_level = tree
        for part in parts[:-1]:
            current_level = current_level.setdefault(part, {})
        current_level[parts[-1]] = {'_is_file_': True, 'keywords': match['keywords']}
    return tree

def print_condensed_tree(node: Dict, prefix: str = ""):
    """第二阶段:递归地打印由匹配项构成的简洁文件树."""
    items = sorted(node.keys())
    for i, item in enumerate(items):
        connector = "└── " if i == len(items) - 1 else "├── "
        is_file = node[item].get('_is_file_', False)
        
        if is_file:
            colored_keywords = []
            sorted_keywords = sorted(list(node[item]['keywords']))
            for j, keyword in enumerate(sorted_keywords):
                color = KEYWORD_COLORS[j % len(KEYWORD_COLORS)]
                colored_keywords.append(f"{color}{keyword}{STYLE_RESET}")
            keywords_str = ", ".join(colored_keywords)
            print(f"{prefix}{connector}✅️ {COLOR_FILE_MATCH}{item}{STYLE_RESET} ({keywords_str})")
        else:
            print(f"{prefix}{connector}{COLOR_DIR}{item}{STYLE_RESET}")
            new_prefix = prefix + ("    " if i == len(items) - 1 else "│   ")
            print_condensed_tree(node[item], new_prefix)

def main():
    parser = argparse.ArgumentParser(
        description="在文件夹中递归搜索包含特定字符串的文本文件,并以树状结构显示结果.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    # --- 修改:将关键字参数分为默认的OR搜索和可选的AND搜索 ---
    parser.add_argument('keywords', nargs='*', default=[], 
                        help='(默认) 查找含有任意一个关键字的文件 (OR 搜索).')
    parser.add_argument('-c', '--co-occurrence', nargs='+', 
                        help='查找同时含有所有这些关键字的文件 (AND 搜索).')

    parser.add_argument('-p', '--path', default='.', help='要搜索的目录路径 (默认为当前目录).')
    parser.add_argument('-i', '--case-insensitive', action='store_true', help='进行不区分大小写的搜索.')
    parser.add_argument('-e', '--exclude', action='append', default=[],
                        help='要排除的目录 (可多次使用).\n- 按名称: --exclude doc\n- 按路径: --exclude target/classes')
    parser.add_argument('--full-tree', action='store_true', help='显示完整目录树,而不仅仅是包含匹配项的分支.')
    
    args = parser.parse_args()
    
    # 检查是否提供了关键字
    if not args.keywords and not args.co_occurrence:
        parser.error("错误: 必须提供关键字进行搜索.请使用 'python search.py 关键字...' 或 'python search.py -c 关键字...'.")

    # 确定搜索模式和关键字
    if args.co_occurrence:
        search_mode = 'ALL'
        keywords_to_search = args.co_occurrence
    else:
        search_mode = 'ANY'
        keywords_to_search = args.keywords

    search_path = os.path.abspath(args.path)
    if not os.path.isdir(search_path):
        print(f"错误: 路径 '{search_path}' 不是一个有效的目录.")
        return
        
    exclude_names = set(DEFAULT_EXCLUDE_NAMES)
    exclude_paths = set()
    for pattern in args.exclude:
        normalized_pattern = os.path.normpath(pattern)
        if os.sep in normalized_pattern:
            exclude_paths.add(os.path.abspath(os.path.join(search_path, normalized_pattern)))
        else:
            exclude_names.add(normalized_pattern)

    # 由于 --full-tree 模式已被废弃(逻辑未更新),我们只使用简洁模式
    # 如果需要完整模式,需要将文件扩展名过滤逻辑也添加到 search_and_print_full_tree 函数中
    if args.full_tree:
         print("警告: --full-tree 模式当前未完全支持所有新功能,可能显示不准确.建议使用默认的简洁输出.")

    matches = collect_matches(search_path, keywords_to_search, args.case_insensitive, exclude_names, exclude_paths, search_mode)
    if not matches:
        print("在指定的文本文件中未找到任何匹配项.")
        return
        
    print(f"{COLOR_DIR}📁 {os.path.basename(search_path)}{STYLE_RESET}")
    file_tree = build_file_tree(matches, search_path)
    print_condensed_tree(file_tree)

if __name__ == "__main__":
    main()
