#!/usr/bin/env python3
"""
Code coverage measurement and SVG badge generator for ESP32_HeatMeterGateway.
Uses GCC gcov (JSON output with text fallback) and Python standard library only.
No third-party services or external packages required.
"""

import argparse
import glob
import json
import os
import subprocess
import sys
from typing import Dict, List, Tuple


def clean_stale_gcda_files(build_dir: str) -> None:
    """Remove stale or non-test .gcda files to prevent libgcov checksum warnings."""
    if not os.path.isdir(build_dir):
        return

    for gcda_path in glob.glob(os.path.join(build_dir, "**", "*.gcda"), recursive=True):
        norm_path = gcda_path.replace("\\", "/")
        # Unity and unity_config are shared across test binaries and not part of src/ coverage
        if "/test/" not in norm_path:
            try:
                os.remove(gcda_path)
            except OSError:
                pass
            continue

        gcno_path = os.path.splitext(gcda_path)[0] + ".gcno"
        if not os.path.isfile(gcno_path):
            try:
                os.remove(gcda_path)
            except OSError:
                pass
        elif os.path.getmtime(gcno_path) > os.path.getmtime(gcda_path):
            try:
                os.remove(gcda_path)
            except OSError:
                pass


def normalize_source_path(file_path: str, project_root: str) -> str:
    """Normalize a path reported by gcov relative to the repository root."""
    abs_root = os.path.abspath(project_root)
    abs_file = os.path.abspath(os.path.join(abs_root, file_path)) if not os.path.isabs(file_path) else os.path.abspath(file_path)
    try:
        rel = os.path.relpath(abs_file, abs_root)
    except ValueError:
        return ""
    return rel.replace("\\", "/")


def collect_coverage(build_dir: str, project_root: str) -> Dict[str, Dict[str, Dict[int, int]]]:
    """
    Run gcov on all test .gcda files and aggregate line and function execution counts
    for project source files under src/.
    """
    coverage_data: Dict[str, Dict[str, Dict]] = {}
    test_gcda_pattern = os.path.join(build_dir, "test", "**", "*.gcda")
    gcda_files = sorted(glob.glob(test_gcda_pattern, recursive=True))

    for gcda_path in gcda_files:
        gcno_path = os.path.splitext(gcda_path)[0] + ".gcno"
        if not os.path.isfile(gcno_path):
            continue
        if os.path.getmtime(gcno_path) > os.path.getmtime(gcda_path):
            continue

        try:
            proc = subprocess.run(
                ["gcov", "--json-format", "--stdout", gcda_path],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            print("[Coverage] Warning: 'gcov' executable not found in PATH.", file=sys.stderr)
            return coverage_data

        if proc.returncode != 0 or not proc.stdout.strip():
            continue

        for raw_line in proc.stdout.splitlines():
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                payload = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            for file_entry in payload.get("files", []):
                rel_path = normalize_source_path(file_entry.get("file", ""), project_root)
                if not rel_path.startswith("src/"):
                    continue

                if rel_path not in coverage_data:
                    coverage_data[rel_path] = {"lines": {}, "functions": {}}

                file_lines = coverage_data[rel_path]["lines"]
                for line_info in file_entry.get("lines", []):
                    line_num = int(line_info.get("line_number", 0))
                    count = int(line_info.get("count", 0))
                    if line_num > 0:
                        file_lines[line_num] = file_lines.get(line_num, 0) + count

                file_funcs = coverage_data[rel_path]["functions"]
                for func_info in file_entry.get("functions", []):
                    func_name = func_info.get("demangled_name") or func_info.get("name") or ""
                    exec_count = int(func_info.get("execution_count", 0))
                    if func_name:
                        file_funcs[func_name] = file_funcs.get(func_name, 0) + exec_count

    return coverage_data


def summarize_coverage(coverage_data: Dict[str, Dict[str, Dict]]) -> Tuple[List[Dict], Dict]:
    """Compute per-file and total coverage metrics."""
    rows = []
    total_lines = 0
    covered_lines = 0
    total_funcs = 0
    covered_funcs = 0

    for file_path in sorted(coverage_data.keys()):
        lines_map = coverage_data[file_path]["lines"]
        funcs_map = coverage_data[file_path]["functions"]

        f_total_lines = len(lines_map)
        f_covered_lines = sum(1 for c in lines_map.values() if c > 0)
        f_line_pct = (f_covered_lines * 100.0 / f_total_lines) if f_total_lines > 0 else 100.0

        f_total_funcs = len(funcs_map)
        f_covered_funcs = sum(1 for c in funcs_map.values() if c > 0)
        f_func_pct = (f_covered_funcs * 100.0 / f_total_funcs) if f_total_funcs > 0 else 100.0

        total_lines += f_total_lines
        covered_lines += f_covered_lines
        total_funcs += f_total_funcs
        covered_funcs += f_covered_funcs

        rows.append({
            "file": file_path,
            "covered_lines": f_covered_lines,
            "total_lines": f_total_lines,
            "line_pct": f_line_pct,
            "covered_funcs": f_covered_funcs,
            "total_funcs": f_total_funcs,
            "func_pct": f_func_pct,
        })

    overall_line_pct = (covered_lines * 100.0 / total_lines) if total_lines > 0 else 0.0
    overall_func_pct = (covered_funcs * 100.0 / total_funcs) if total_funcs > 0 else 0.0

    totals = {
        "covered_lines": covered_lines,
        "total_lines": total_lines,
        "line_pct": overall_line_pct,
        "covered_funcs": covered_funcs,
        "total_funcs": total_funcs,
        "func_pct": overall_func_pct,
    }
    return rows, totals


def get_badge_color(percentage: float) -> str:
    """Return a shields.io-compatible hex color based on coverage percentage."""
    if percentage >= 80.0:
        return "#4c1"
    if percentage >= 70.0:
        return "#97ca00"
    if percentage >= 60.0:
        return "#a4a61d"
    if percentage >= 40.0:
        return "#dfb317"
    if percentage >= 20.0:
        return "#fe7d37"
    return "#e05d44"


def generate_svg_badge(percentage: float, output_path: str, label: str = "coverage") -> None:
    """Generate a self-contained SVG badge without any external service."""
    value_text = f"{percentage:.1f}%"
    color = get_badge_color(percentage)

    label_width = 61
    value_width = max(45, len(value_text) * 7 + 10)
    total_width = label_width + value_width

    label_x = int((label_width / 2.0) * 10)
    label_text_len = (label_width - 10) * 10
    value_x = int((label_width + value_width / 2.0) * 10)
    value_text_len = (value_width - 10) * 10

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20" role="img" aria-label="{label}: {value_text}">
  <title>{label}: {value_text}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="{total_width}" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_width}" height="20" fill="#555"/>
    <rect x="{label_width}" width="{value_width}" height="20" fill="{color}"/>
    <rect width="{total_width}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="110">
    <text aria-hidden="true" x="{label_x}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="{label_text_len}">{label}</text>
    <text x="{label_x}" y="140" transform="scale(.1)" fill="#fff" textLength="{label_text_len}">{label}</text>
    <text aria-hidden="true" x="{value_x}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="{value_text_len}">{value_text}</text>
    <text x="{value_x}" y="140" transform="scale(.1)" fill="#fff" textLength="{value_text_len}">{value_text}</text>
  </g>
</svg>
"""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)


def format_console_report(rows: List[Dict], totals: Dict) -> str:
    """Format a human-readable ASCII table of code coverage."""
    lines = [
        "",
        "==================================== CODE COVERAGE ====================================",
        f"{'Source File':<30} | {'Lines':<18} | {'Functions':<18}",
        "-" * 71,
    ]
    for row in rows:
        line_str = f"{row['covered_lines']}/{row['total_lines']} ({row['line_pct']:.1f}%)"
        func_str = f"{row['covered_funcs']}/{row['total_funcs']} ({row['func_pct']:.1f}%)"
        lines.append(f"{row['file']:<30} | {line_str:<18} | {func_str:<18}")

    lines.append("-" * 71)
    tot_line_str = f"{totals['covered_lines']}/{totals['total_lines']} ({totals['line_pct']:.1f}%)"
    tot_func_str = f"{totals['covered_funcs']}/{totals['total_funcs']} ({totals['func_pct']:.1f}%)"
    lines.append(f"{'TOTAL':<30} | {tot_line_str:<18} | {tot_func_str:<18}")
    lines.append("=======================================================================================")
    return "\n".join(lines)


def write_github_step_summary(rows: List[Dict], totals: Dict, summary_path: str) -> None:
    """Append a Markdown coverage report table to GitHub Actions $GITHUB_STEP_SUMMARY."""
    md_lines = [
        "## 📊 Code Coverage Report",
        "",
        "| Source File | Line Coverage | Lines (`Covered / Total`) | Function Coverage | Functions (`Covered / Total`) |",
        "| :--- | :---: | :---: | :---: | :---: |",
    ]
    for row in rows:
        md_lines.append(
            f"| `{row['file']}` | **{row['line_pct']:.1f}%** | `{row['covered_lines']} / {row['total_lines']}` "
            f"| {row['func_pct']:.1f}% | `{row['covered_funcs']} / {row['total_funcs']}` |"
        )
    md_lines.append(
        f"| **Total** | **{totals['line_pct']:.1f}%** | **`{totals['covered_lines']} / {totals['total_lines']}`** "
        f"| **{totals['func_pct']:.1f}%** | **`{totals['covered_funcs']} / {totals['total_funcs']}`** |"
    )
    md_lines.append("")

    with open(summary_path, "a", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")


def run_test_wrapper(test_cmd: List[str], build_dir: str, badge_path: str, project_root: str) -> int:
    """Execute a PlatformIO native test binary and update the coverage badge afterward."""
    clean_stale_gcda_files(build_dir)

    proc = subprocess.run(test_cmd, capture_output=True, text=True, check=False)
    stdout_lines = proc.stdout.splitlines(keepends=True)

    coverage_data = collect_coverage(build_dir, project_root)
    rows, totals = summarize_coverage(coverage_data)
    if totals["total_lines"] > 0:
        generate_svg_badge(totals["line_pct"], badge_path)

    summary_idx = None
    for idx, line in enumerate(stdout_lines):
        if "Tests" in line and "Failures" in line and "Ignored" in line:
            summary_idx = idx
            break

    cov_msg = (
        f"[Coverage] Accumulated line coverage: {totals['line_pct']:.1f}% "
        f"({totals['covered_lines']}/{totals['total_lines']} lines) -> {badge_path}\n"
    )

    if summary_idx is not None:
        output_text = "".join(stdout_lines[:summary_idx]) + cov_msg + "".join(stdout_lines[summary_idx:])
    else:
        output_text = proc.stdout + cov_msg

    sys.stdout.write(output_text)
    sys.stdout.flush()
    if proc.stderr:
        sys.stderr.write(proc.stderr)
        sys.stderr.flush()

    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure C++ unit test code coverage and generate SVG badge.")
    parser.add_argument("--build-dir", default=".pio/build/native", help="Path to PlatformIO native build directory.")
    parser.add_argument("--badge", default="docs/coverage.svg", help="Output path for generated SVG coverage badge.")
    parser.add_argument("--summary", action="store_true", help="Write Markdown table to GITHUB_STEP_SUMMARY if set.")
    parser.add_argument("--run-test", nargs=argparse.REMAINDER, help="Run a test binary and update coverage.")
    args = parser.parse_args()

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    build_dir = os.path.join(project_root, args.build_dir) if not os.path.isabs(args.build_dir) else args.build_dir
    badge_path = os.path.join(project_root, args.badge) if not os.path.isabs(args.badge) else args.badge

    if args.run_test:
        return run_test_wrapper(args.run_test, build_dir, badge_path, project_root)

    clean_stale_gcda_files(build_dir)
    coverage_data = collect_coverage(build_dir, project_root)
    rows, totals = summarize_coverage(coverage_data)

    if totals["total_lines"] == 0:
        print("[Coverage] No coverage data found in", build_dir, "- run 'pio test -e native' first.", file=sys.stderr)
        return 1

    generate_svg_badge(totals["line_pct"], badge_path)
    print(format_console_report(rows, totals))
    print(f"[Coverage] Badge generated at: {args.badge} ({totals['line_pct']:.1f}%)")

    summary_env = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_env and (args.summary or True):
        write_github_step_summary(rows, totals, summary_env)

    return 0


if __name__ == "__main__":
    sys.exit(main())
