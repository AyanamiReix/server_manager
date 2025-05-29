#!/usr/bin/env python3
"""
luojie & heyi 服务器管理系统 - 快速配置脚本
支持命令行快速连接和配置服务器
"""

import argparse
import os
import sys
import json
from pathlib import Path

# 添加模块路径
sys.path.append(str(Path(__file__).parent))

from connect.ssh_manager import SSHManager
from connect.pem_handler import PEMHandler
from projects.github_manager import GitHubManager
from backup.backup_manager import BackupManager

class QuickSetup:
    def __init__(self):
        self.pem_path = r"E:\server_connect\luojie.pem"
        self.ssh_manager = SSHManager()
        self.pem_handler = PEMHandler()
        self.github_manager = GitHubManager()
        self.backup_manager = BackupManager()
        
        # 加载配置
        self.load_config()
    
    def load_config(self):
        """加载系统配置"""
        config_file = Path("config/settings.json")
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "pem_file": self.pem_path,
                "default_users": ["luojie", "heyi"],
                "project_dir": "/home/shared/projects",
                "backup_dir": "./backups"
            }
            self.save_config()
    
    def save_config(self):
        """保存系统配置"""
        os.makedirs("config", exist_ok=True)
        with open("config/settings.json", 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def check_pem_file(self):
        """检查PEM文件是否存在"""
        if not os.path.exists(self.pem_path):
            print(f"❌ PEM文件不存在: {self.pem_path}")
            print("请确保 luojie.pem 文件放在 E:\\server_connect\\ 目录下")
            return False
        
        # 检查文件权限
        if not self.pem_handler.check_pem_permissions(self.pem_path):
            print("🔧 修复PEM文件权限...")
            self.pem_handler.fix_pem_permissions(self.pem_path)
        
        print(f"✅ PEM文件检查通过: {self.pem_path}")
        return True
    
    def connect_server(self, ip_address):
        """连接服务器"""
        print(f"🔌 连接服务器: {ip_address}")
        
        if not self.check_pem_file():
            return False
        
        # 尝试连接
        if self.ssh_manager.connect(ip_address, "root", self.pem_path):
            print("✅ 服务器连接成功！")
            return True
        else:
            print("❌ 服务器连接失败！")
            return False
    
    def setup_users(self):
        """设置用户"""
        print("👥 创建和配置用户...")
        
        users = self.config["default_users"]
        for user in users:
            print(f"📝 创建用户: {user}")
            success = self.ssh_manager.execute_script("scripts/user_setup.sh", user)
            if success:
                print(f"✅ 用户 {user} 创建成功")
            else:
                print(f"❌ 用户 {user} 创建失败")
    
    def setup_docker(self):
        """设置Docker环境"""
        print("🐳 配置Docker环境...")
        
        success = self.ssh_manager.execute_script("scripts/docker_setup.sh")
        if success:
            print("✅ Docker环境配置成功")
        else:
            print("❌ Docker环境配置失败")
    
    def deploy_projects(self, project_names=None):
        """部署项目"""
        print("📁 部署项目...")
        
        if project_names is None:
            # 加载项目配置
            projects_file = Path("config/projects.json")
            if projects_file.exists():
                with open(projects_file, 'r', encoding='utf-8') as f:
                    projects_config = json.load(f)
                project_names = list(projects_config.keys())
            else:
                print("⚠️ 没有配置项目，跳过部署")
                return
        
        for project_name in project_names:
            print(f"📥 部署项目: {project_name}")
            success = self.github_manager.deploy_project(project_name, self.ssh_manager)
            if success:
                print(f"✅ 项目 {project_name} 部署成功")
            else:
                print(f"❌ 项目 {project_name} 部署失败")
    
    def full_setup(self, ip_address, projects=None):
        """完整的服务器设置流程"""
        print("🚀 开始完整服务器配置...")
        print("=" * 50)
        
        # 1. 连接服务器
        if not self.connect_server(ip_address):
            return False
        
        # 2. 设置用户
        self.setup_users()
        
        # 3. 设置Docker
        self.setup_docker()
        
        # 4. 部署项目
        if projects:
            self.deploy_projects(projects)
        
        print("🎉 服务器配置完成！")
        return True
    
    def backup_projects(self, project_names=None):
        """备份项目"""
        print("💾 备份项目...")
        
        if not self.ssh_manager.is_connected():
            print("❌ 请先连接服务器")
            return False
        
        if project_names is None:
            project_names = self.github_manager.list_deployed_projects(self.ssh_manager)
        
        for project_name in project_names:
            print(f"📦 备份项目: {project_name}")
            success = self.backup_manager.backup_project(project_name, self.ssh_manager)
            if success:
                print(f"✅ 项目 {project_name} 备份成功")
            else:
                print(f"❌ 项目 {project_name} 备份失败")
    
    def interactive_mode(self):
        """交互模式"""
        print("🎯 luojie & heyi 服务器管理系统")
        print("=" * 40)
        
        # 获取IP地址
        ip_address = input("请输入服务器公网IP: ").strip()
        if not ip_address:
            print("❌ IP地址不能为空")
            return
        
        # 连接服务器
        if not self.connect_server(ip_address):
            return
        
        # 选择操作
        while True:
            print("\n选择操作:")
            print("1. 🛠️ 完整服务器配置")
            print("2. 👥 只创建用户")
            print("3. 🐳 只配置Docker")
            print("4. 📁 部署项目")
            print("5. 💾 备份项目")
            print("0. 退出")
            
            choice = input("请选择 (0-5): ").strip()
            
            if choice == "1":
                self.setup_users()
                self.setup_docker()
                self.deploy_projects()
            elif choice == "2":
                self.setup_users()
            elif choice == "3":
                self.setup_docker()
            elif choice == "4":
                self.deploy_projects()
            elif choice == "5":
                self.backup_projects()
            elif choice == "0":
                break
            else:
                print("❌ 无效选择")
        
        print("👋 再见！")

def main():
    parser = argparse.ArgumentParser(description="luojie & heyi 服务器管理系统")
    parser.add_argument("--ip", help="服务器公网IP地址")
    parser.add_argument("--setup", action="store_true", help="执行完整设置")
    parser.add_argument("--users", action="store_true", help="只创建用户")
    parser.add_argument("--docker", action="store_true", help="只配置Docker")
    parser.add_argument("--projects", nargs="*", help="部署指定项目")
    parser.add_argument("--backup", nargs="*", help="备份指定项目")
    parser.add_argument("--interactive", action="store_true", help="交互模式")
    
    args = parser.parse_args()
    
    setup = QuickSetup()
    
    if args.interactive or not any(vars(args).values()):
        # 交互模式
        setup.interactive_mode()
    elif args.ip:
        # 命令行模式
        if not setup.connect_server(args.ip):
            return
        
        if args.setup:
            setup.full_setup(args.ip, args.projects)
        elif args.users:
            setup.setup_users()
        elif args.docker:
            setup.setup_docker()
        elif args.projects is not None:
            setup.deploy_projects(args.projects if args.projects else None)
        elif args.backup is not None:
            setup.backup_projects(args.backup if args.backup else None)
    else:
        print("❌ 请提供服务器IP地址或使用 --interactive 模式")
        parser.print_help()

if __name__ == "__main__":
    main() 