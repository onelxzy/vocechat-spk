#!/usr/bin/env python3
"""
GitHub Actions Orchestration Script:
Checks upstream Privoce/vocechat-server-rust for latest release,
and builds SPK packages if an update is found.
"""

import os
import sys
import json
import urllib.request
import subprocess

UPSTREAM_REPO = "Privoce/vocechat-server-rust"

def get_json(url, token=None):
    headers = {"User-Agent": "VoceChat-SPK-AutoBuilder"}
    if token:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return None

def set_github_output(name, value):
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a", encoding="utf-8") as f:
            if "\n" in value:
                delimiter = "EOF"
                f.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")
            else:
                f.write(f"{name}={value}\n")
    print(f"[OUTPUT] {name}={value}")

def main():
    token = os.environ.get("GITHUB_TOKEN")
    current_repo = os.environ.get("GITHUB_REPOSITORY")
    force_version = os.environ.get("FORCE_VERSION", "").strip()

    print("=== Checking for VoceChat Upstream Releases ===")
    
    # 1. Determine target version
    if force_version:
        target_tag = force_version if force_version.startswith("v") else f"v{force_version}"
        target_version = target_tag.lstrip("v")
        print(f"Force version requested: {target_tag}")
        upstream_release = get_json(f"https://api.github.com/repos/{UPSTREAM_REPO}/releases/tags/{target_tag}")
    else:
        latest = get_json(f"https://api.github.com/repos/{UPSTREAM_REPO}/releases/latest")
        if not latest or "tag_name" not in latest:
            # Fallback to releases list if 'latest' is not marked
            releases = get_json(f"https://api.github.com/repos/{UPSTREAM_REPO}/releases")
            if not releases:
                print("Failed to fetch releases from upstream repository.", file=sys.stderr)
                sys.exit(1)
            upstream_release = releases[0]
        else:
            upstream_release = latest
        target_tag = upstream_release["tag_name"]
        target_version = target_tag.lstrip("v")
        print(f"Latest upstream release: {target_tag}")

    # 2. Check if already built in current repo
    if current_repo and not force_version:
        my_releases = get_json(f"https://api.github.com/repos/{current_repo}/releases", token=token) or []
        existing_tags = [r.get("tag_name") for r in my_releases]
        print(f"Existing releases in current repo: {existing_tags}")
        if target_tag in existing_tags:
            print(f"Release {target_tag} already exists in {current_repo}. Up to date!")
            set_github_output("new_version", "false")
            return

    # 3. Build SPK packages for both x86_64 and aarch64
    print(f"\nBuilding SPK for VoceChat {target_tag}...")
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    
    cmd = [
        sys.executable,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "build.py"),
        "--version", target_version,
        "--arch", "all",
        "--output-dir", output_dir
    ]
    
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print("Build failed!", file=sys.stderr)
        sys.exit(res.returncode)

    # 4. Prepare release notes
    release_body = f"""## VoceChat Server {target_tag} 群晖 DSM 7.x 安装包

基于官方上游 [{UPSTREAM_REPO}](https://github.com/{UPSTREAM_REPO}/releases/tag/{target_tag}) 自动构建发布。

### 📦 套件安装包下载
- **`vocechat-server_{target_tag}_x86_64.spk`**: 适用于 Intel / AMD x86_64 架构机型
- **`vocechat-server_{target_tag}_arm64.spk`**: 适用于 Realtek / Rockchip 等 ARM64 架构机型

### 🚀 特性与说明
- **无损升级支持**：自动继承历史数据（存储在 `/var/packages/vocechat-server/shares/VoceChat/data` 共享文件夹）。
- **配置持久化保护**：升级时自动备份并还原用户的自定义配置与邮件模板。
- **权限安全沙箱**：基于 DSM 7 规范以非 root 专有系统用户 `package:vocechat-server` 运行。
- **纯净安全**：编译构建过程 100% 由 GitHub Actions 自动化沙盒执行，二进制直接溯源自官方 Release，不含任何第三方修改或私有信息。
"""

    set_github_output("new_version", "true")
    set_github_output("tag_name", target_tag)
    set_github_output("release_name", f"VoceChat Server {target_tag} 群晖 SPK")
    set_github_output("release_body", release_body)
    print("\nCheck and build finished successfully!")

if __name__ == "__main__":
    main()
