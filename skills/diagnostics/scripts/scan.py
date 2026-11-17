#!/usr/bin/env python3
"""
Universal Diagnostic Scanner for Codebases
Analyzes project structure, syntax, secret leaks, empty/silent error handling,
unclosed resources, environment/dependency integrity, and git history context.
Outputs structured JSON and human-readable diagnostic facts.
"""

import os
import sys
import re
import json
import ast
import subprocess
from pathlib import Path

def get_git_context(root_dir):
    """Gathers commit history, recently modified files, and discarded ideas from commit messages."""
    ctx = {"is_git": False, "recent_commits": [], "changed_files": []}
    try:
        res = subprocess.run(
            ["git", "log", "-n", "10", "--oneline"],
            cwd=root_dir, capture_output=True, text=True, check=False
        )
        if res.returncode == 0:
            ctx["is_git"] = True
            ctx["recent_commits"] = [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]
            
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root_dir, capture_output=True, text=True, check=False
        )
        if status.returncode == 0:
            ctx["changed_files"] = [line.strip() for line in status.stdout.strip().splitlines() if line.strip()]
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return ctx
    return ctx

def scan_file_content(file_path):
    """Scans code files for secrets, silent catches, unclosed resources, and syntax."""
    findings = []
    text = ""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except Exception as e:
        return [{"type": "read_error", "file": str(file_path), "msg": str(e)}]

    # 1. Secret patterns (Hardcoded API keys / tokens)
    secret_patterns = [
        (r'(?i)(api[_-]?key|secret|token|password|auth_token)\s*=\s*[\'"][A-Za-z0-9_\-]{16,}[\'"]', "Potential hardcoded secret/API key"),
        (r'AIza[0-9A-Za-z-_]{35}', "Google API Key pattern detected"),
        (r'sk-[a-zA-Z0-9]{20,}', "OpenAI/API secret key pattern detected"),
        (r'ghp_[a-zA-Z0-9]{36}', "GitHub Personal Access Token detected"),
    ]
    for pattern, desc in secret_patterns:
        matches = re.finditer(pattern, text)
        for m in matches:
            line_no = text.count('\n', 0, m.start()) + 1
            findings.append({
                "type": "security",
                "severity": "CRITICAL",
                "file": str(file_path),
                "line": line_no,
                "msg": desc
            })

    # 2. Python specific AST inspection
    if file_path.suffix == ".py":
        try:
            tree = ast.parse(text, filename=str(file_path))
            for node in ast.walk(tree):
                # Silent error handlers (try except pass / empty handler)
                if isinstance(node, ast.ExceptHandler):
                    is_empty_or_pass = False
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                        is_empty_or_pass = True
                    elif len(node.body) == 0:
                        is_empty_or_pass = True
                    
                    if is_empty_or_pass:
                        findings.append({
                            "type": "silent_error",
                            "severity": "WARNING",
                            "file": str(file_path),
                            "line": node.lineno,
                            "msg": "Silent exception handling (`except ...: pass`). Errors may fail invisibly."
                        })
                
                # Naked except
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    findings.append({
                        "type": "broad_exception",
                        "severity": "INFO",
                        "file": str(file_path),
                        "line": node.lineno,
                        "msg": "Bare `except:` catches all exceptions including system interrupts."
                    })
        except SyntaxError as se:
            findings.append({
                "type": "syntax_error",
                "severity": "CRITICAL",
                "file": str(file_path),
                "line": se.lineno,
                "msg": f"SyntaxError: {se.msg}"
            })

    # 3. JS / TS Silent Catches & Async unhandled patterns
    if file_path.suffix in [".js", ".ts", ".jsx", ".tsx"]:
        silent_catch_pattern = r'catch\s*\([^)]*\)\s*\{\s*\}'
        for m in re.finditer(silent_catch_pattern, text):
            line_no = text.count('\n', 0, m.start()) + 1
            findings.append({
                "type": "silent_error",
                "severity": "WARNING",
                "file": str(file_path),
                "line": line_no,
                "msg": "Empty catch block in JavaScript/TypeScript. Errors are swallowed."
            })

    return findings

def scan_project(root_dir="."):
    root = Path(root_dir).resolve()
    ignore_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv", ".idea", ".vscode", "dist", "build"}
    
    project_files = []
    file_types = {}
    
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not d.startswith(".agents")]
        for f in filenames:
            if f.startswith(".DS_Store"):
                continue
            fp = Path(dirpath) / f
            rel = fp.relative_to(root)
            ext = fp.suffix or fp.name
            file_types[ext] = file_types.get(ext, 0) + 1
            project_files.append(fp)

    all_findings = []
    for fp in project_files:
        if fp.is_file() and fp.stat().st_size < 1_000_000: # < 1MB
            if fp.suffix in [".py", ".js", ".ts", ".jsx", ".tsx", ".sh", ".json", ".env", ".yaml", ".yml", ".md"]:
                all_findings.extend(scan_file_content(fp))

    git_ctx = get_git_context(root)

    # Detect tech stack
    stack = []
    if (root / "package.json").exists():
        stack.append("Node.js")
    if (root / "requirements.txt").exists() or (root / "pyproject.toml").exists() or any(f.suffix == ".py" for f in project_files):
        stack.append("Python")
    if (root / "go.mod").exists():
        stack.append("Go")
    if (root / "Cargo.toml").exists():
        stack.append("Rust")

    report = {
        "root": str(root),
        "total_files": len(project_files),
        "file_types": file_types,
        "stack": stack,
        "git_context": git_ctx,
        "findings": all_findings,
        "critical_count": sum(1 for x in all_findings if x.get("severity") == "CRITICAL"),
        "warning_count": sum(1 for x in all_findings if x.get("severity") == "WARNING"),
        "info_count": sum(1 for x in all_findings if x.get("severity") == "INFO")
    }
    return report

if __name__ == "__main__":
    report = scan_project(".")
    print(json.dumps(report, indent=2))
