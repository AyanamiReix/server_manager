#!/usr/bin/env python3
"""
GitHub项目管理器
支持多项目克隆、部署和管理
"""

import json
import os
import subprocess
from pathlib import Path
from datetime import datetime

class GitHubManager:
    def __init__(self, config_file="config/projects.json"):
        self.config_file = config_file
        self.projects = self.load_projects()
    
    def load_projects(self):
        """加载项目配置"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 默认项目配置
            default_projects = {
                "CompressAI-Vision": {
                    "url": "https://github.com/luojie-heyi/CompressAI-Vision.git",
                    "branch": "main",
                    "description": "CompressAI-Vision项目 - 视频压缩和目标检测",
                    "deploy_path": "/home/shared/projects/CompressAI-Vision",
                    "dependencies": ["docker", "python3", "git"],
                    "setup_script": "setup.sh",
                    "docker_build": True
                }
            }
            self.save_projects(default_projects)
            return default_projects
    
    def save_projects(self, projects=None):
        """保存项目配置"""
        if projects is None:
            projects = self.projects
        
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(projects, f, indent=2, ensure_ascii=False)
    
    def add_project(self, name, url, branch="main", description="", 
                   deploy_path=None, dependencies=None, setup_script=None,
                   docker_build=False):
        """添加新项目"""
        if deploy_path is None:
            deploy_path = f"/home/shared/projects/{name}"
        
        if dependencies is None:
            dependencies = ["git"]
        
        project_config = {
            "url": url,
            "branch": branch,
            "description": description,
            "deploy_path": deploy_path,
            "dependencies": dependencies,
            "setup_script": setup_script,
            "docker_build": docker_build,
            "added_date": datetime.now().isoformat()
        }
        
        self.projects[name] = project_config
        self.save_projects()
        
        print(f"✅ 项目已添加: {name}")
        return True
    
    def remove_project(self, name):
        """删除项目"""
        if name in self.projects:
            del self.projects[name]
            self.save_projects()
            print(f"✅ 项目已删除: {name}")
            return True
        else:
            print(f"❌ 项目不存在: {name}")
            return False
    
    def list_projects(self):
        """列出所有项目"""
        if not self.projects:
            print("📭 没有配置任何项目")
            return []
        
        print("📁 已配置的项目:")
        for name, config in self.projects.items():
            print(f"   🔹 {name}")
            print(f"      📄 描述: {config.get('description', 'N/A')}")
            print(f"      🌐 URL: {config['url']}")
            print(f"      🌿 分支: {config.get('branch', 'main')}")
            print(f"      📂 部署路径: {config['deploy_path']}")
            print()
        
        return list(self.projects.keys())
    
    def deploy_project(self, project_name, ssh_manager):
        """部署指定项目到服务器"""
        if project_name not in self.projects:
            print(f"❌ 项目不存在: {project_name}")
            return False
        
        project = self.projects[project_name]
        
        print(f"🚀 开始部署项目: {project_name}")
        print("=" * 50)
        
        # 1. 检查依赖
        if not self._check_dependencies(project, ssh_manager):
            print(f"❌ 依赖检查失败")
            return False
        
        # 2. 创建部署目录
        deploy_path = project["deploy_path"]
        if not ssh_manager.create_directory(deploy_path):
            print(f"❌ 创建部署目录失败: {deploy_path}")
            return False
        
        # 3. 克隆或更新项目
        if not self._clone_or_update_project(project, ssh_manager):
            print(f"❌ 项目克隆/更新失败")
            return False
        
        # 4. 运行设置脚本
        if project.get("setup_script"):
            if not self._run_setup_script(project, ssh_manager):
                print(f"⚠️ 设置脚本执行失败")
        
        # 5. 构建Docker镜像
        if project.get("docker_build"):
            if not self._build_docker_image(project, ssh_manager):
                print(f"⚠️ Docker镜像构建失败")
        
        print(f"🎉 项目部署完成: {project_name}")
        return True
    
    def _check_dependencies(self, project, ssh_manager):
        """检查项目依赖"""
        print("🔍 检查项目依赖...")
        
        dependencies = project.get("dependencies", [])
        for dep in dependencies:
            print(f"   📦 检查依赖: {dep}")
            
            if dep == "docker":
                stdout, stderr, exit_status = ssh_manager.execute_command("docker --version")
                if exit_status != 0:
                    print(f"❌ Docker未安装")
                    return False
            elif dep == "python3":
                stdout, stderr, exit_status = ssh_manager.execute_command("python3 --version")
                if exit_status != 0:
                    print(f"❌ Python3未安装")
                    return False
            elif dep == "git":
                stdout, stderr, exit_status = ssh_manager.execute_command("git --version")
                if exit_status != 0:
                    print(f"❌ Git未安装")
                    return False
        
        print("✅ 依赖检查通过")
        return True
    
    def _clone_or_update_project(self, project, ssh_manager):
        """克隆或更新项目"""
        deploy_path = project["deploy_path"]
        url = project["url"]
        branch = project.get("branch", "main")
        
        print(f"📥 克隆/更新项目...")
        
        # 检查项目是否已存在
        if ssh_manager.file_exists(f"{deploy_path}/.git"):
            print("🔄 项目已存在，执行更新...")
            
            # 进入项目目录并更新
            commands = [
                f"cd {deploy_path}",
                "git fetch origin",
                f"git checkout {branch}",
                f"git pull origin {branch}"
            ]
            
            for cmd in commands:
                stdout, stderr, exit_status = ssh_manager.execute_command(cmd)
                if exit_status != 0:
                    print(f"❌ 命令执行失败: {cmd}")
                    print(f"错误: {stderr}")
                    return False
            
            print("✅ 项目更新成功")
        else:
            print("📦 首次克隆项目...")
            
            # 克隆项目
            clone_cmd = f"git clone -b {branch} {url} {deploy_path}"
            stdout, stderr, exit_status = ssh_manager.execute_command(clone_cmd)
            
            if exit_status != 0:
                print(f"❌ 项目克隆失败: {stderr}")
                return False
            
            print("✅ 项目克隆成功")
        
        return True
    
    def _run_setup_script(self, project, ssh_manager):
        """运行项目设置脚本"""
        deploy_path = project["deploy_path"]
        setup_script = project["setup_script"]
        
        print(f"🔧 运行设置脚本: {setup_script}")
        
        script_path = f"{deploy_path}/{setup_script}"
        
        # 检查脚本是否存在
        if not ssh_manager.file_exists(script_path):
            print(f"⚠️ 设置脚本不存在: {script_path}")
            return False
        
        # 执行脚本
        commands = [
            f"cd {deploy_path}",
            f"chmod +x {setup_script}",
            f"bash {setup_script}"
        ]
        
        for cmd in commands:
            stdout, stderr, exit_status = ssh_manager.execute_command(cmd, timeout=300)
            if exit_status != 0:
                print(f"❌ 设置脚本执行失败: {cmd}")
                print(f"错误: {stderr}")
                return False
        
        print("✅ 设置脚本执行成功")
        return True
    
    def _build_docker_image(self, project, ssh_manager):
        """构建Docker镜像"""
        deploy_path = project["deploy_path"]
        
        print(f"🐳 构建Docker镜像...")
        
        # 检查Dockerfile是否存在
        dockerfile_paths = [
            f"{deploy_path}/Dockerfile",
            f"{deploy_path}/docker/Dockerfile",
            f"{deploy_path}/docker/vcm/Dockerfile"
        ]
        
        dockerfile_found = False
        dockerfile_dir = deploy_path
        
        for dockerfile_path in dockerfile_paths:
            if ssh_manager.file_exists(dockerfile_path):
                dockerfile_found = True
                dockerfile_dir = str(Path(dockerfile_path).parent)
                break
        
        if not dockerfile_found:
            print("⚠️ 未找到Dockerfile，跳过镜像构建")
            return True
        
        # 构建镜像
        project_name = Path(deploy_path).name.lower()
        build_cmd = f"cd {dockerfile_dir} && docker build -t {project_name}:latest ."
        
        stdout, stderr, exit_status = ssh_manager.execute_command(build_cmd, timeout=1800)  # 30分钟超时
        
        if exit_status != 0:
            print(f"❌ Docker镜像构建失败: {stderr}")
            return False
        
        print("✅ Docker镜像构建成功")
        return True
    
    def update_project(self, project_name, ssh_manager):
        """更新指定项目"""
        if project_name not in self.projects:
            print(f"❌ 项目不存在: {project_name}")
            return False
        
        project = self.projects[project_name]
        return self._clone_or_update_project(project, ssh_manager)
    
    def list_deployed_projects(self, ssh_manager):
        """列出服务器上已部署的项目"""
        deployed = []
        
        for name, project in self.projects.items():
            deploy_path = project["deploy_path"]
            if ssh_manager.file_exists(deploy_path):
                deployed.append(name)
        
        if deployed:
            print("🚀 已部署的项目:")
            for name in deployed:
                print(f"   ✅ {name}")
        else:
            print("📭 没有已部署的项目")
        
        return deployed
    
    def get_project_status(self, project_name, ssh_manager):
        """获取项目状态"""
        if project_name not in self.projects:
            return None
        
        project = self.projects[project_name]
        deploy_path = project["deploy_path"]
        
        status = {
            "name": project_name,
            "deployed": ssh_manager.file_exists(deploy_path),
            "url": project["url"],
            "branch": project.get("branch", "main"),
            "deploy_path": deploy_path
        }
        
        if status["deployed"]:
            # 获取Git信息
            stdout, stderr, exit_status = ssh_manager.execute_command(f"cd {deploy_path} && git log -1 --format='%H|%s|%ad' --date=short")
            if exit_status == 0 and stdout:
                parts = stdout.strip().split('|')
                if len(parts) >= 3:
                    status["last_commit"] = {
                        "hash": parts[0][:8],
                        "message": parts[1],
                        "date": parts[2]
                    }
        
        return status
    
    def create_project_template(self):
        """创建项目配置模板"""
        template = {
            "project-name": {
                "url": "https://github.com/username/repository.git",
                "branch": "main",
                "description": "项目描述",
                "deploy_path": "/home/shared/projects/project-name",
                "dependencies": ["git", "docker", "python3"],
                "setup_script": "setup.sh",
                "docker_build": True
            }
        }
        
        template_file = "config/projects_template.json"
        os.makedirs(os.path.dirname(template_file), exist_ok=True)
        
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 项目配置模板已创建: {template_file}")
        return template_file 