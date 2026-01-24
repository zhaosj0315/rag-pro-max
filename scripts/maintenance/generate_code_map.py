import os
import ast
import sys
import json

def analyze_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read())
        except Exception as e:
            return {"error": str(e)}

    classes = []
    top_level_funcs = []
    missing_docs = []
    
    file_docstring = ast.get_docstring(tree) or "无文件级文档"
    if file_docstring == "无文件级文档":
        missing_docs.append({"type": "file", "name": filepath, "context": ""})

    # Collect classes
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = []
            doc = ast.get_docstring(node)
            if not doc:
                missing_docs.append({"type": "class", "name": node.name, "file": filepath})
                doc = "无描述"
            
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    m_doc = ast.get_docstring(item)
                    if not m_doc and not item.name.startswith("_"):
                        missing_docs.append({"type": "method", "name": f"{node.name}.{item.name}", "file": filepath})
                    methods.append(item.name)

            classes.append({
                "name": node.name,
                "doc": doc,
                "methods": methods
            })
        elif isinstance(node, ast.FunctionDef):
            doc = ast.get_docstring(node)
            if not doc:
                missing_docs.append({"type": "function", "name": node.name, "file": filepath})
                doc = "无描述"
            
            top_level_funcs.append({
                "name": node.name,
                "doc": doc
            })

    return {
        "doc": file_docstring,
        "classes": classes,
        "functions": top_level_funcs,
        "missing_docs": missing_docs
    }

def generate_markdown(root_dir, output_file, missing_file):
    all_missing = []
    
    with open(output_file, "w", encoding="utf-8") as out:
        out.write(f"# 🗺️ RAG Pro Max 代码全典 (Code Index)\n\n")
        out.write(f"> 本文档由脚本自动生成，用于快速索引项目结构与功能。\n\n")
        out.write(f"## 目录结构\n\n")

        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
            
            for file in sorted(files):
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, os.getcwd())
                    
                    analysis = analyze_file(full_path)
                    
                    if "error" in analysis:
                        out.write(f"### ❌ {rel_path}\n*解析失败: {analysis['error']}*\n\n")
                        continue
                    
                    if "missing_docs" in analysis:
                        all_missing.extend(analysis["missing_docs"])

                    # File Header
                    out.write(f"### 📄 {rel_path}\n")
                    if analysis['doc'] and analysis['doc'] != "无文件级文档":
                        out.write(f"**📝 描述**: {analysis['doc'].strip().splitlines()[0]}\n\n")
                    
                    # Classes
                    if analysis['classes']:
                        out.write(f"- **🏗️ Classes**:\n")
                        for c in analysis['classes']:
                            doc_summary = c['doc'].strip().splitlines()[0]
                            out.write(f"  - `class {c['name']}`: {doc_summary}\n")

                    # Functions
                    if analysis['functions']:
                        out.write(f"- **⚡ Functions**:\n")
                        for func in analysis['functions']:
                            doc_summary = func['doc'].strip().splitlines()[0]
                            out.write(f"  - `def {func['name']}`: {doc_summary}\n")
                    
                    out.write("\n---\n\n")
    
    # Save missing docs for AI processing
    with open(missing_file, "w", encoding="utf-8") as f:
        json.dump(all_missing, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    target_dir = "src"
    output_md = "docs/CODE_INDEX.md"
    missing_json = "docs/MISSING_DOCS.json"
    
    if not os.path.exists("docs"):
        os.makedirs("docs")
        
    print(f"🔍 正在扫描 {target_dir} 并生成索引...")
    generate_markdown(target_dir, output_md, missing_json)
    print(f"✅ 索引已生成: {output_md}")
    print(f"✅ 缺失文档清单: {missing_json}")