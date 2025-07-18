# 文件内容快速搜索工具 `search.py`

这是一个功能强大的命令行小工具,用于在指定目录中递归地搜索包含一个或多个关键字的文件,并以清晰的文件树结构高亮显示搜索结果.

## ✨ 主要功能

- **🌳 树状图显示**:以直观的文件树形式展示目录结构和搜索结果.
- **🔍 多关键词搜索**:可以同时搜索多个关键词,文件只要包含其中**任意一个**就会被标记.
- **✅ 高亮与标记**:
  - 使用 emoji 标记匹配到的文件.`✅️`
  - 在文件名后用彩色高亮具体命中了哪个/哪些关键词,结果一目了然.
- **⚙️ 高度可定制**:
  - `--path`: 支持指定任意目录作为搜索起点.
  - `-i` / `--case-insensitive`: 可选的忽略大小写搜索模式.
  - `--exclude-dir`: 允许用户添加额外的需要排除的目录.
- **🚀 智能高效**:
  - 自动排除 , , 等常见缓存/版本控制目录,加快搜索速度.` .git``node_modules``__pycache__ `
  - 自动跳过二进制文件(如图片、程序),避免乱码和错误.
- **💻 跨平台兼容**:借助 库,彩色输出效果在 Windows, macOS 和 Linux 上均表现良好.`colorama`

## 🔧 环境要求

- Python 3.6+
- `colorama` 库

### 📚 使用示例

**1. 基本搜索** 在当前目录下,搜索包含 “todo！” 或 “fn” 的文件.

```bash
python search.py "todo!" "fn"
```

**2. 在指定目录中搜索** 在 目录下搜索包含 的文件.` ~/Documents/my_project` `"error"`

```bash
python search.py error --path ~/Documents/my_project
```

**3. 忽略大小写搜索** 搜索 `"warning`,不区分大小写

```bash
python search.py warning --case-insensitive
```

或者使用短命令:

```bash
python search.py warning -i
```

**4. 排除特定目录** 在搜索时,除了默认排除的目录外,再额外排除 和 目录.` logs` `dist `

```bash
python search.py "DeprecationWarning" --exclude-dir logs --exclude-dir dist
```

**5. 组合使用** 在`/var/www` `vendor `目录下,不区分大小写地搜索 “debug” 或 “test”,并且排除`vendor`目录.

```bash
python search.py debug test --path /var/www -i --exclude-dir vendor
```
