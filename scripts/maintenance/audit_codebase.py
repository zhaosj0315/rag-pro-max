import os
import subprocess
import time

def run_command(cmd, description):
    print(f"🚀 {description}...")
    start = time.time()
    try:
        subprocess.run(cmd, shell=True, check=True)
        elapsed = time.time() - start
        print(f"✅ 完成 (耗时: {elapsed:.2f}s)\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ 失败: {e}\n")

def main():
    print("======== RAG Pro Max 代码全景审计 ========\n")
    
    # Ensure directories
    os.makedirs("docs", exist_ok=True)
    os.makedirs("scripts/maintenance", exist_ok=True)

    # 1. 静态索引 (Dimension 1)
    run_command("python3 scripts/maintenance/generate_code_map.py", "生成代码户籍档案 (Static Index)")

    # 2. 依赖图 (Dimension 2)
    # pydeps generates SVG by default or dot.
    # --noshow prevents opening the image. --max-bacon limits clutter.
    # Excluding standard libs for clarity.
    pydeps_cmd = "pydeps src --noshow --max-bacon 2 -o docs/DEPENDENCY_GRAPH.svg --exclude-exact src/tests"
    run_command(pydeps_cmd, "绘制血缘关系图 (Dependency Graph)")

    # 3. 僵尸代码 (Dimension 3)
    # Redirect output to file
    vulture_cmd = "vulture src/ --min-confidence 80 > docs/DEAD_CODE_REPORT.txt"
    # vulture returns non-zero if issues found, so don't check=True strictly or handle it
    print(f"🚀 扫描僵尸代码 (Dead Code)...")
    try:
        subprocess.run(vulture_cmd, shell=True)
        print(f"✅ 报告已生成: docs/DEAD_CODE_REPORT.txt\n")
    except Exception as e:
        print(f"❌ 扫描失败: {e}\n")

    print("======== 审计完成 ========")
    print("📄 索引: docs/CODE_INDEX.md")
    print("📉 缺失: docs/MISSING_DOCS.json (可用于 AI 补全)")
    print("🕸️ 依赖: docs/DEPENDENCY_GRAPH.svg")
    print("💀 僵尸: docs/DEAD_CODE_REPORT.txt")

if __name__ == "__main__":
    main()
