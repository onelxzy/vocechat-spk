#!/usr/bin/env python3
"""
VoceChat Synology SPK Package Builder
Supports building x86_64 and aarch64 SPK packages with lossless upgrade support.
"""

import os
import sys
import shutil
import tarfile
import zipfile
import hashlib
import base64
import argparse
import urllib.request

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(ROOT_DIR, "template")
DEFAULT_OUTPUT_DIR = os.path.join(ROOT_DIR, "output")

ARCH_CONFIGS = {
    "x86_64": {
        "upstream_asset": "vocechat-server-v{version}-x86_64-unknown-linux-musl.zip",
        "syno_arch": "apollolake avoton braswell broadwell broadwellnk broadwellnkv2 broadwellntbap bromolow cedarview denverton epyc7002 epyc7003 epyc7003ntb geminilake geminilakenk grantley icelaked kvmx64 purley r1000 r1000nk v1000 v1000nk x86 x86_64",
        "spk_suffix": "x86_64"
    },
    "aarch64": {
        "upstream_asset": "vocechat-server-v{version}-aarch64-unknown-linux-musl.zip",
        "syno_arch": "armv8 aarch64 rtd1296 rtd1619b armada37xx v1000",
        "spk_suffix": "arm64"
    }
}

CONFIG_TOML_CONTENT = """# webclient_url = "https://github.com/Privoce/vocechat-web/releases/latest/download"

[webclient]
url = "https://sh.voce.chat/web_client/v0.4.x"

[system]
data_dir = "/var/packages/vocechat-server/shares/VoceChat/data"
token_expiry_seconds = 300
refresh_token_expiry_seconds = 864000000

# magic_token_expiry_seconds = 600

[network]
bind = "0.0.0.0:3009"
# domain = "chat.privoce.com"
# frontend_url = "http://localhost:3009"

# [network.tls]
# type = "self_signed"

# [network.tls]
# type = "certificate"
# cert = "...."
# key = "...."
# path = "./cert/"

# [network.tls]
# type = "acme_http_01"
# directory_url = "https://acme-v02.api.letsencrypt.org/directory"
# http_bind = "0.0.0.0:80"
# cache_path = "./data/cert"

# [network.tls]
# type = "acme_tls_alpn_01"
# directory_url = "https://acme-v02.api.letsencrypt.org/directory"
# cache_path = "./data/cert"

[template.register_by_email]
subject = "Register code"
file = "templates/register_by_email.html"

[template.login_by_email]
subject = "Your sign-in link for Vocechat"
file = "templates/login_by_email.html"

#[[user]]
#name = "Guest"
#password = "123456"
#email = "guest@voce.chat"

#[login]
#who_can_sign_up = "EveryOne"  # or "InvitationOnly"
#guest = false
#password = true
#magic_link = true
#google = false
#github = false
#metamask = false
#third_party = false
#passkey = false
"""

CONFIG_TLS_TOML_CONTENT = """[system]
server_key = "a secret key"
data_dir = "/var/packages/vocechat-server/shares/VoceChat/data"

[network]
bind = "0.0.0.0:3009"
tls = true
"""

def ensure_lf(text):
    return text.replace('\r\n', '\n').replace('\r', '\n')

def download_file(url, dest_path):
    print(f"Downloading: {url} -> {dest_path}")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(req) as resp, open(dest_path, "wb") as f:
        shutil.copyfileobj(resp, f)
    print(f"Downloaded successfully: {os.path.getsize(dest_path)} bytes")

def build_spk(version, arch, zip_path, output_dir):
    arch_cfg = ARCH_CONFIGS[arch]
    clean_version = version.lstrip('v')
    
    build_work_dir = os.path.join(ROOT_DIR, f"build_tmp_{arch}")
    target_dir = os.path.join(build_work_dir, "target")
    
    if os.path.exists(build_work_dir):
        shutil.rmtree(build_work_dir)
    os.makedirs(target_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n--- Building SPK: VoceChat v{clean_version} ({arch}) ---")

    # 1. Prepare target/
    # Copy app/
    shutil.copytree(os.path.join(TEMPLATE_DIR, "app"), os.path.join(target_dir, "app"))

    # Extract binary and templates from upstream zip
    with zipfile.ZipFile(zip_path, 'r') as z:
        with open(os.path.join(target_dir, "vocechat-server"), "wb") as f:
            f.write(z.read("vocechat-server"))

        cfg_dir = os.path.join(target_dir, "config")
        tmpl_dir = os.path.join(cfg_dir, "templates")
        os.makedirs(tmpl_dir, exist_ok=True)

        with open(os.path.join(tmpl_dir, "login_by_email.html"), "wb") as f:
            f.write(z.read("config/templates/login_by_email.html"))
        with open(os.path.join(tmpl_dir, "register_by_email.html"), "wb") as f:
            f.write(z.read("config/templates/register_by_email.html"))

    with open(os.path.join(target_dir, "config", "config.toml"), "wb") as f:
        f.write(ensure_lf(CONFIG_TOML_CONTENT).encode('utf-8'))
    with open(os.path.join(target_dir, "config", "config-tls.toml"), "wb") as f:
        f.write(ensure_lf(CONFIG_TLS_TOML_CONTENT).encode('utf-8'))

    # 2. Package package.tgz
    package_tgz_path = os.path.join(build_work_dir, "package.tgz")
    def target_filter(tarinfo):
        tarinfo.uid = 0
        tarinfo.gid = 0
        tarinfo.uname = "root"
        tarinfo.gname = "root"
        if tarinfo.isdir():
            tarinfo.mode = 0o755
        elif tarinfo.name.endswith("vocechat-server"):
            tarinfo.mode = 0o755
        else:
            tarinfo.mode = 0o644
        return tarinfo

    with tarfile.open(package_tgz_path, "w:gz", format=tarfile.PAX_FORMAT) as tar:
        for item in sorted(os.listdir(target_dir)):
            item_path = os.path.join(target_dir, item)
            tar.add(item_path, arcname=item, filter=target_filter)

    with open(package_tgz_path, "rb") as f:
        pkg_md5 = hashlib.md5(f.read()).hexdigest()

    # 3. Prepare other package elements
    shutil.copytree(os.path.join(TEMPLATE_DIR, "conf"), os.path.join(build_work_dir, "conf"))
    shutil.copytree(os.path.join(TEMPLATE_DIR, "WIZARD_UIFILES"), os.path.join(build_work_dir, "WIZARD_UIFILES"))
    shutil.copytree(os.path.join(TEMPLATE_DIR, "scripts"), os.path.join(build_work_dir, "scripts"))

    icon_path = os.path.join(TEMPLATE_DIR, "icons", "PACKAGE_ICON.PNG")
    icon_256_path = os.path.join(TEMPLATE_DIR, "icons", "PACKAGE_ICON_256.PNG")
    shutil.copyfile(icon_path, os.path.join(build_work_dir, "PACKAGE_ICON.PNG"))
    shutil.copyfile(icon_256_path, os.path.join(build_work_dir, "PACKAGE_ICON_256.PNG"))

    with open(icon_path, "rb") as f:
        icon_b64 = base64.b64encode(f.read()).decode('utf-8')
    with open(icon_256_path, "rb") as f:
        icon_256_b64 = base64.b64encode(f.read()).decode('utf-8')

    with open(os.path.join(TEMPLATE_DIR, "INFO.template"), "r", encoding="utf-8") as f:
        info_tmpl = f.read()

    changelog_str = f"1. 更新 VoceChat 服务端核心至 v{clean_version}<br>2. 优化群晖 DSM 7.x 兼容性与配置恢复机制"
    info_rendered = info_tmpl.format(
        version=clean_version,
        arch=arch_cfg["syno_arch"],
        changelog=changelog_str,
        checksum=pkg_md5,
        package_icon=icon_b64,
        package_icon_256=icon_256_b64
    )

    with open(os.path.join(build_work_dir, "INFO"), "wb") as f:
        f.write(ensure_lf(info_rendered).encode('utf-8'))

    # Normalize line endings
    for root, _, files in os.walk(build_work_dir):
        for f in files:
            p = os.path.join(root, f)
            if f.endswith('.PNG') or f == 'package.tgz':
                continue
            try:
                with open(p, 'rb') as fp:
                    content = fp.read()
                content_lf = ensure_lf(content.decode('utf-8', errors='ignore')).encode('utf-8')
                with open(p, 'wb') as fp:
                    fp.write(content_lf)
            except Exception:
                pass

    # 4. Create final SPK archive (tar)
    spk_name = f"vocechat-server_v{clean_version}_{arch_cfg['spk_suffix']}.spk"
    final_spk_path = os.path.join(output_dir, spk_name)

    def spk_filter(tarinfo):
        tarinfo.uid = 0
        tarinfo.gid = 0
        tarinfo.uname = "root"
        tarinfo.gname = "root"
        if tarinfo.isdir():
            tarinfo.mode = 0o755
        elif "scripts" in tarinfo.name:
            tarinfo.mode = 0o755
        else:
            tarinfo.mode = 0o644
        return tarinfo

    entries = ["INFO", "PACKAGE_ICON.PNG", "PACKAGE_ICON_256.PNG", "WIZARD_UIFILES", "conf", "package.tgz", "scripts"]
    with tarfile.open(final_spk_path, "w", format=tarfile.PAX_FORMAT) as spk:
        for e in entries:
            spk.add(os.path.join(build_work_dir, e), arcname=e, filter=spk_filter)

    # Cleanup temp build directory
    shutil.rmtree(build_work_dir)

    spk_size_mb = os.path.getsize(final_spk_path) / 1024 / 1024
    print(f"Created SPK: {final_spk_path} ({spk_size_mb:.2f} MB)")
    return final_spk_path

def main():
    parser = argparse.ArgumentParser(description="VoceChat SPK Builder")
    parser.add_argument("--version", required=True, help="VoceChat version, e.g. 0.5.39")
    parser.add_argument("--arch", choices=["x86_64", "aarch64", "all"], default="x86_64", help="Architecture to build")
    parser.add_argument("--zip", help="Local zip file path (if not downloading)")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory")
    args = parser.parse_args()

    clean_version = args.version.lstrip('v')
    arches = ["x86_64", "aarch64"] if args.arch == "all" else [args.arch]

    downloads_dir = os.path.join(ROOT_DIR, "downloads")
    os.makedirs(downloads_dir, exist_ok=True)

    for arch in arches:
        if args.zip and os.path.exists(args.zip) and len(arches) == 1:
            zip_file = args.zip
        else:
            asset_name = ARCH_CONFIGS[arch]["upstream_asset"].format(version=clean_version)
            url = f"https://github.com/Privoce/vocechat-server-rust/releases/download/v{clean_version}/{asset_name}"
            zip_file = os.path.join(downloads_dir, asset_name)
            if not os.path.exists(zip_file):
                download_file(url, zip_file)
        
        build_spk(clean_version, arch, zip_file, args.output_dir)

if __name__ == "__main__":
    main()
