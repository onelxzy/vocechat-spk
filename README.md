# VoceChat Synology DSM 7.x SPK 套件自动化监控与构建

[![Auto Monitor & Build VoceChat SPK](https://github.com/onelxzy/vocechat-spk/actions/workflows/auto-build.yml/badge.svg)](https://github.com/onelxzy/vocechat-spk/actions/workflows/auto-build.yml)

本项目用于为群晖 DSM 7.x 系统自动监控并打包 **[VoceChat](https://github.com/Privoce/vocechat-server-rust)** 最新服务端的 `.spk` 安装包，支持 **无损平滑升级**（自动保留所有聊天数据、用户、文件与自定义配置）。

---

## 🌟 特性

1. **自动监控与发布**：
   - 通过 GitHub Actions 每天自动监控官方仓库 `Privoce/vocechat-server-rust` 的最新发布。
   - 官方一旦发布新版本，自动触发构建并发布到本仓库的 **Releases** 页面供直接下载。
   - 也支持在 Actions 页面手动点击 `Run workflow` 触发指定版本的构建。
2. **多架构支持**：
   - 自动同时构建 **`x86_64`**（Intel / AMD）与 **`arm64`**（Realtek / Rockchip 等）架构套件。
3. **100% 无损升级**：
   - 升级时自动备份现有的 `config.toml`、`config-tls.toml` 和邮件模板，并在更新后恢复。
   - 数据目录严格锁定在群晖共享文件夹 `/var/packages/vocechat-server/shares/VoceChat/data`，无论如何升级、重装，共享文件夹中的聊天记录、账号、数据库永不丢失。
4. **安全纯净**：
   - 构建过程 100% 由 GitHub Actions 云端虚拟环境完成，直接拉取官方 Release 二进制，**绝不包含任何个人敏感信息或私有数据**。
   - 遵循 DSM 7 官方最小权限沙箱规范，以非 root 专属系统用户 `package:vocechat-server` 运行。

---

## 📥 安装与升级教程

### 1. 覆盖安装 / 无损升级
1. 进入本仓库的 **[Releases](../../releases)** 页面，下载对应 CPU 架构的最新 `.spk` 套件包：
   - `vocechat-server_vX.Y.Z_x86_64.spk`（主流 Intel / AMD 群晖机型）
   - `vocechat-server_vX.Y.Z_arm64.spk`（ARM 架构群晖机型）
2. 登录群晖 DSM，打开 **“套件中心” (Package Center)**。
3. 点击右上角 **“手动安装”**，选择下载的 `.spk` 文件，点击“下一步”。
4. 群晖将自动识别为现有 `vocechat-server` 的更新，确认后即可完成覆盖升级。升级后原有的聊天历史、用户登录态均完整保留。

> **关于套件发布者与覆盖安装冲突问题**：
> - 群晖 DSM 识别一个套件是否为同一软件，**仅依据 `INFO` 文件中的 `package="vocechat-server"`**。
> - `maintainer`（维护者）或 `distributor`（分发者）字段仅作为界面文字展示，更改不会导致任何冲突，亦不会被识别为新应用，可安全直接覆盖安装。
> - 若提示“未知发布者”，只需在“套件中心 -> 设置 -> 信任层级”中选择“允许任何发布者”。

---

## 🛠️ 本地手动构建

如需在本地构建，只需运行：

```bash
# 自动从官方下载指定版本并构建所有架构
python build.py --version 0.5.39 --arch all

# 或仅构建 x86_64
python build.py --version 0.5.39 --arch x86_64
```
生成的 `.spk` 安装包将保存在 `output/` 目录下。
