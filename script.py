import os
from collections import defaultdict

def prompt():
    '''
    
    markdown修正提示词:
    我会给出我的markdown笔记 你需要做以下的任务
    1. 对我的内容进行适当的补充和添加,保证内容的完整性和不改变原有的意思,需要适当添加内容,但是不要过于详细,帮我补充一部分就好
    2.帮我排版内容 运用适当的段落块和标题 让内容看上去更加的合理和清晰
    3. 把里面的专有名词和文本出现的代码使用合适的格式包包裹 诸如 对code进行讲解的时候出现了某个变量或者函数 你需要把 他用``这样进行包裹
    4. 给出一个markdown格式的code block 而不是给我渲染后的内容 这样我方便复制  
    like如下
    ```markdown
    //这是你修正后的笔记内容
    ```

    '''

def replace_chinese_punctuation(file_path, total_char_counts):
    """
    替换文件中的中文字符为英文字符，并统计字符修改数量。
    返回修改数量和处理状态消息。
    """
    replacements = {
        '（': '(',
        '）': ')',
        '；': ';',
        '：': ':',
        '。': '.',
        '，': ',',
        '？': '?'
    }

    file_modified_count = 0
    status_message = ""
    
    try:
        # Attempt to read file with UTF-8 encoding
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        new_content = original_content
        
        # Iterate through replacement rules and count
        for chinese_char, english_char in replacements.items():
            count_before = new_content.count(chinese_char)
            if count_before > 0:
                new_content = new_content.replace(chinese_char, english_char)
                modified_chars_in_this_rule = count_before 
                
                # Update total statistics
                total_char_counts[chinese_char] += modified_chars_in_this_rule
                file_modified_count += modified_chars_in_this_rule

        if file_modified_count > 0:
            # Write only if content has changed
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            status_message = f"Sucessfully replace {file_modified_count} chars"
        else:
            status_message = "无字符需替换" # This status will typically not be shown in the tree view now

    except UnicodeDecodeError:
        status_message = "skip (not UTF-8 decode or binary file)"
        #status_message = "跳过（非UTF-8编码或二进制文件）"
    except Exception as e:
        status_message = f"failure（ERROR：{e}）"
    
    return file_modified_count, status_message

def generate_tree_structure(root_dir, modified_files_info):
    """
    根据修改文件信息生成一个标准的树形结构字典。
    字典的键是目录，值是包含子目录和文件的列表。
    """
    tree = {}

    for file_path, info in modified_files_info.items():
        # Get path relative to the root directory
        relative_path = os.path.relpath(file_path, root_dir)
        
        # Split path into components
        parts = relative_path.split(os.sep)
        
        current_level = tree
        for i, part in enumerate(parts):
            if i == len(parts) - 1: # Last part is the file
                # Store file info directly at the leaf node
                current_level[part] = info 
            else: # Directory
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
    return tree

def print_tree(tree, indent="", is_last=True, file_prefix='📄', dir_prefix='📁'):
    """
    递归打印树形结构。
    """
    keys = sorted(tree.keys())
    for i, key in enumerate(keys):
        is_current_last = (i == len(keys) - 1)
        # Determine branch symbol
        branch_symbol = "└── " if is_current_last else "├── "
        
        value = tree[key]
        if isinstance(value, dict): # It's a directory
            print(f"{indent}{branch_symbol}{dir_prefix} {key}/")
            next_indent = indent + ("    " if is_current_last else "│   ")
            print_tree(value, next_indent, False, file_prefix, dir_prefix) # Recursive call for sub-directory
        else: # It's a file with its info (modified_count, status_message)
            modified_count, status_message = value
            if modified_count > 0:
                print(f"{indent}{branch_symbol}📝 {key}：{status_message} （tot {modified_count} chars）")
            else: # This branch covers files marked as "skipped (binary/non-UTF8)"
                print(f"{indent}{branch_symbol}📄 {key}：{status_message}")


def main():
    """
    Traverses the current directory, processes text files, and outputs a detailed tree view.
    """
    script_name = os.path.basename(__file__)
    current_root_dir = os.getcwd() # Get the actual current working directory

    # Common text file extensions. Add or modify as needed.
    text_extensions = {
        '.txt', '.md', '.cpp', '.h', '.c', '.py', '.java', '.js', 
        '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.sh', '.go', 
        '.rb', '.php', '.swift', '.kt', '.vue', '.ts', '.jsx', '.tsx',
        '.rs' ,'toml',
    }

    # Directories to skip (e.g., build outputs, version control metadata)
    skip_dirs = {
        'build', 'target', 'dist', '.git', '.vscode', '__pycache__', 'node_modules', 
        '.idea', '.vs', '.DS_Store', 'coverage' 
    }

    # Stores info for files that were modified or identified as non-UTF8/binary.
    # key: full file path, value: (modified_count, status_message)
    relevant_files_info = {}
    
    # Aggregates total replacements for each type of Chinese character.
    total_char_replacement_summary = defaultdict(int)

    print("⭕️⭕️⭕️ start ⭕️⭕️⭕️")
    print(" " * 20)
    
    # Traverse current directory and all subdirectories.
    for root, dirs, files in os.walk('.'):
        # Filter out skipped directories and hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in skip_dirs] 
        
        for file_name in files:
            # Exclude the script itself.
            if file_name == script_name:
                continue

            file_path = os.path.join(root, file_name)
            
            # Get file extension and convert to lowercase.
            _, ext = os.path.splitext(file_name)
            ext = ext.lower()

            # Process only common text file extensions.
            if ext in text_extensions:
                modified_count, status = replace_chinese_punctuation(file_path, total_char_replacement_summary)
                # Only store results for files that were actually modified (count > 0)
                # or those identified as binary/non-UTF8 (which we still want to flag).
                if modified_count > 0 or "跳过（非UTF-8编码或二进制文件）" in status:
                    relevant_files_info[file_path] = (modified_count, status)
            # Files not in text_extensions are ignored and not stored.

    #print("-" * 20)
    print("✅️✅️✅️ details ✅️✅️✅️")
    
    if not relevant_files_info:
        print("Not Found Files Replaceble")
    else:
        # Generate the tree structure from the relevant file paths
        tree_structure = generate_tree_structure(current_root_dir, relevant_files_info)
        print_tree(tree_structure)

    print(" " * 20 )
    print("--- Tot Counts ---")
    
    # Output total replacement count for each character type.
    if total_char_replacement_summary:
        # Use a list of the Chinese characters to ensure consistent output order.
        ordered_chars = ['（', '）', '；', '：', '。', '，', '？']
        # Map for outputting corresponding English character
        output_replacements = {
            '（': '(',
            '）': ')',
            '；': ';',
            '：': ':',
            '。': '.',
            '，': ',',
            '？': '?'
        }
        for char in ordered_chars:
            if char in total_char_replacement_summary:
                count = total_char_replacement_summary[char]
                print(f"'{char}' -> '{output_replacements[char]}' tot {count} chars")
    else:
        print("No CN chars to be replaced")

    print(" " * 20)
    print("⭕️⭕️⭕️ finish ⭕️⭕️⭕️")

if __name__ == "__main__":
    main()