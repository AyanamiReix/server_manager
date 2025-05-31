# 🚀 luojie & heyi 服务器管理系统

> 独立的服务器管理工具，专为luojie和heyi设计的多项目管理解决方案

## 📋 系统概述

这是一个**完全独立**的服务器管理系统，不依赖任何具体项目。可以：
- 🔌 一键连接服务器（pem文件 + 公网IP）
- 👥 自动创建和管理用户（luojie, heyi）
- 📁 管理多个GitHub项目
- 💾 项目备份和恢复
- 🐳 Docker环境自动配置

## 🛠️ 系统结构

```        
server_management_system/
├── 📱 服务器管理器.py              # 主程序GUI界面
├── 🔧 quick_setup.py               # 快速配置脚本
├── connect/                        # 连接管理模块
│   ├── ssh_manager.py             # SSH连接管理
│   └── pem_handler.py             # PEM密钥处理
├── projects/                       # 项目管理模块
│   ├── github_manager.py          # GitHub项目管理
│   └── project_deployer.py        # 项目部署工具
├── backup/                         # 备份管理模块
│   ├── backup_manager.py          # 备份管理器
│   └── restore_manager.py         # 恢复管理器
├── config/                         # 配置文件
│   ├── settings.json              # 系统配置
│   └── projects.json              # 项目配置
└── scripts/                        # 服务器端脚本
    ├── user_setup.sh              # 用户创建脚本
    ├── docker_setup.sh            # Docker环境配置
    └── project_deploy.sh          # 项目部署脚本
```

## 🚀 快速开始

### 1. 下载系统
```bash
# 下载到本地（比如桌面）
git clone https://github.com/luojie-heyi/server-management-system.git
cd server-management-system
```

### 2. 配置环境
```bash
# 安装依赖
pip install -r requirements.txt

# 配置PEM文件路径
# 将 luojie.pem 放在 E:\server_connect\ 目录下
```

### 3. 启动管理器
```bash
# 启动图形界面
python 服务器管理器.py

# 或使用命令行快速配置
python quick_setup.py --ip 你的公网IP
```

## 💡 使用流程

### 完整的服务器配置流程
```
1. 输入公网IP
2. 自动使用PEM文件连接root
3. 创建luojie和heyi用户（平等权限）
4. 配置Docker环境
5. 选择要部署的项目
6. 自动下载和配置项目
7. 完成！
```

### 项目备份流程
```
1. 选择要备份的项目
2. 自动压缩和下载
3. 保存到本地备份文件夹
4. 生成恢复脚本
```

## 🎯 核心功能

### 🔌 连接管理
- 自动使用 `E:\server_connect\luojie.pem`
- 支持公网IP一键连接
- 连接状态实时监控

### 👥 用户管理
- 自动创建luojie和heyi用户
- 两用户完全平等的管理员权限
- 共享项目目录配置

### 📁 项目管理
- 支持多个GitHub项目
- 自动克隆和部署
- 项目依赖自动安装

### 💾 备份恢复
- 智能项目备份
- 快速恢复到新服务器
- 支持增量备份

## ⚙️ 配置说明

系统会自动检测和配置：
- PEM文件路径：`E:\server_connect\luojie.pem`
- 备份目录：`./backups/`
- 项目目录：`/home/shared/projects/`
- 用户配置：luojie, heyi（sudo权限）

---

**🎉 这个系统完全独立，下载后直接使用，不依赖任何项目！** 