# VoceChat Server for Synology DSM 7.x

[![Auto Monitor & Build VoceChat SPK](https://github.com/onelxzy/vocechat-spk/actions/workflows/auto-build.yml/badge.svg)](https://github.com/onelxzy/vocechat-spk/actions/workflows/auto-build.yml)
[![GitHub Release](https://img.shields.io/github/v/release/onelxzy/vocechat-spk?include_prereleases&style=flat-square)](https://github.com/onelxzy/vocechat-spk/releases)
[![DSM Version](https://img.shields.io/badge/DSM-7.1%20%7C%207.2+-blue?style=flat-square)](https://www.synology.com/dsm)
[![License](https://img.shields.io/badge/License-GPL%20v3-green?style=flat-square)](https://github.com/Privoce/vocechat-server-rust/blob/master/license)

本项目为 [VoceChat](https://voce.chat/) 官方开源服务端（[Privoce/vocechat-server-rust](https://github.com/Privoce/vocechat-server-rust)）的群晖 DSM 7.x 原生套件（`.spk`）自动化构建与维护仓库。

通过 GitHub Actions 持续监控上游官方仓库的最新发布，自动构建并分发支持平滑无损升级的群晖套件安装包。

---

## 架构支持与系统要求

| 架构 / 平台 | 包含机型（示例） | 对应套件安装包 |
| :--- | :--- | :--- |
| **x86_64** | Intel / AMD 处理器（如 DS920+, DS923+, DS220+, DS720+, DS1621+, SA/FS 系列等） | `vocechat-server_vX.Y.Z_x86_64.spk` |
| **ARM64** | Realtek / Rockchip 处理器（如 DS220j, DS223, DS420j, DS423 等） | `vocechat-server_vX.Y.Z_arm64.spk` |

- **最低系统版本**：Synology DSM 7.1-42661 或更高版本（完全兼容 DSM 7.1 与 DSM 7.2 全系列）。

---

## 套件特性

- **数据持久化隔离**：遵循 DSM 7 套件资源规范，业务数据（SQLite 数据库、聊天记录、上传文件、密钥及证书）均统一存储在群晖 `VoceChat` 共享文件夹内，套件升级或重装不影响业务数据。
- **平滑无损升级**：安装向导内置配置迁移与保护机制。在升级新版本时，自动备份现存的 `config.toml`、`config-tls.toml` 及自定义邮件模板，并在新版就位后完整还原，避免配置重置。
- **权限安全沙箱**：基于 DSM 7 最小权限模型，以受限系统用户 `package:vocechat-server` 独立运行，不占用 Root 权限。
- **全自动同步发布**：每天定时检测官方上游版本演进，自动触发云端隔离打包，所有构建制品均直接溯源自官方 Release，保障程序完整性。

---

## 安装与升级说明

### 1. 初次安装 / 升级安装

1. 从本仓库的 **[Releases](https://github.com/onelxzy/vocechat-spk/releases)** 页面下载对应机型架构的最新 `.spk` 安装包。
2. 登录群晖 DSM 管理界面，打开 **“套件中心” (Package Center)**。
3. 点击右上角 **“手动安装”** 按钮，选择下载的 `.spk` 文件，点击 **“下一步”**。
4. 确认安装信息：
   - **首次安装**：系统会自动创建 `VoceChat` 共享文件夹作为数据存储空间。
   - **升级安装**：系统会自动检测为现有 `vocechat-server` 的版本更新，并提示覆盖升级，原聊天记录与用户数据将完整保留。
5. 按照屏幕提示点击 **“完成”** 即可。

> **提示**：如遇到“未知发布者”提示，请在群晖 **“套件中心” -> “设置” -> “信任层级”** 中勾选 **“允许任何发布者”**。

---

## 网络配置与生产环境建议

- **默认端口**：`3009`（局域网访问地址：`http://群晖IP:3009`）。
- **反向代理与 HTTPS**：生产环境中建议通过群晖内置的反向代理功能启用 HTTPS：
  1. 进入 **控制面板 -> 登录门户 -> 高级 -> 反向代理服务器**。
  2. 新增反向代理规则：
     - **来源**：协议 `HTTPS`，主机名 `chat.yourdomain.com`，端口 `443`。
     - **目的地**：协议 `HTTP`，主机名 `127.0.0.1`，端口 `3009`。
  3. 在 **控制面板 -> 安全性 -> 证书** 中为该域名分配有效 SSL 证书。

---

## 本地构建指南

项目提供了跨平台的构建脚本，支持在本地 Python 环境中执行打包：

```bash
# 克隆仓库
git clone https://github.com/onelxzy/vocechat-spk.git
cd vocechat-spk

# 下载指定版本并打包所有架构
python build.py --version 0.5.39 --arch all

# 仅打包 x86_64 架构
python build.py --version 0.5.39 --arch x86_64
```

构建生成的 `.spk` 文件将输出至 `output/` 目录。

---

## 开源许可与致谢

- VoceChat Server 核心代码版权归原作者 [Privoce](https://github.com/Privoce) 所有。
- 本项目遵循 GPL-3.0 开源协议发布。
