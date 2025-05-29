#!/usr/bin/env python3
"""
GitHub上传助手 - 帮助luojie和heyi上传项目到GitHub
支持从服务器下载项目并上传到指定的GitHub仓库
"""

import os
import json
import subprocess
import shutil
import tempfile
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path
import threading
from datetime import datetime

class GitHubUploadHelper:
    def __init__(self, root):
        self.root = root
        self.root.title("📤 GitHub上传助手")
        self.root.geometry("900x700")
        
        # 预设的GitHub仓库配置
        self.github_repos = {
            "server_management_system": {
                "url": "https://github.com/AyanamiReix/server_manager.git",
                "description": "服务器管理系统",
                "local_path": "/home/luojie/CompressAI-Vision/server_management_system",
                "exclude_patterns": ["__pycache__", "*.pyc", ".git", "logs", "backups/*.tar.gz"]
            },
            "CompressAI-Vision": {
                "url": "https://github.com/Circe1111/AAAAAAAAAAProject.git", 
                "description": "CompressAI-Vision完整项目",
                "local_path": "/home/luojie/CompressAI-Vision",
                "exclude_patterns": ["__pycache__", "*.pyc", ".git", "logs", "*.log", "models/*.pth", "results/*", "datasets/*"]
            }
        }
        
        # SSH管理器（从主程序导入）
        self.ssh_manager = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="📤 GitHub项目上传助手", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 左侧：项目选择和配置
        left_frame = ttk.LabelFrame(main_frame, text="📁 项目配置", padding="10")
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 项目选择
        ttk.Label(left_frame, text="选择项目:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.project_var = tk.StringVar()
        project_combo = ttk.Combobox(left_frame, textvariable=self.project_var, width=30)
        project_combo['values'] = list(self.github_repos.keys())
        project_combo.grid(row=0, column=1, pady=5, sticky=(tk.W, tk.E))
        project_combo.bind("<<ComboboxSelected>>", self.on_project_select)
        
        # GitHub仓库URL
        ttk.Label(left_frame, text="GitHub仓库:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.repo_url_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.repo_url_var, width=40).grid(row=1, column=1, pady=5, sticky=(tk.W, tk.E))
        
        # 服务器路径
        ttk.Label(left_frame, text="服务器路径:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.server_path_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.server_path_var, width=40).grid(row=2, column=1, pady=5, sticky=(tk.W, tk.E))
        
        # 本地临时目录
        ttk.Label(left_frame, text="本地目录:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.local_path_var = tk.StringVar()
        local_frame = ttk.Frame(left_frame)
        local_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Entry(local_frame, textvariable=self.local_path_var, width=30).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(local_frame, text="选择", command=self.choose_local_dir).grid(row=0, column=1, padx=(5, 0))
        
        # Git配置
        git_frame = ttk.LabelFrame(left_frame, text="🔧 Git配置", padding="5")
        git_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(git_frame, text="用户名:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.git_user_var = tk.StringVar()
        ttk.Entry(git_frame, textvariable=self.git_user_var, width=20).grid(row=0, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(git_frame, text="邮箱:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.git_email_var = tk.StringVar()
        ttk.Entry(git_frame, textvariable=self.git_email_var, width=20).grid(row=1, column=1, pady=2, padx=(5, 0))
        
        # 操作按钮
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(20, 0))
        
        ttk.Button(button_frame, text="📥 从服务器下载", command=self.download_from_server).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="📤 上传到GitHub", command=self.upload_to_github).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="🔄 完整流程", command=self.full_upload_process).grid(row=0, column=2, padx=(5, 0))
        
        # 右侧：文件预览和日志
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 文件预览
        preview_frame = ttk.LabelFrame(right_frame, text="📂 文件预览", padding="10")
        preview_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.file_tree = ttk.Treeview(preview_frame, height=15)
        self.file_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        tree_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=self.file_tree.yview)
        tree_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.file_tree.configure(yscrollcommand=tree_scroll.set)
        
        # 日志输出
        log_frame = ttk.LabelFrame(right_frame, text="📝 操作日志", padding="10")
        log_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = tk.Text(log_frame, height=12, width=50)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=log_scroll.set)
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        left_frame.columnconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 设置默认值
        self.local_path_var.set(str(Path.home() / "Downloads" / "github_upload"))
        
        # 初始化日志
        self.log("🎉 GitHub上传助手已启动")
        self.log("💡 使用说明:")
        self.log("   1. 选择要上传的项目")
        self.log("   2. 配置Git用户信息")
        self.log("   3. 点击'完整流程'一键上传")
        self.log("")
    
    def log(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def on_project_select(self, event=None):
        """项目选择事件"""
        project_name = self.project_var.get()
        if project_name in self.github_repos:
            config = self.github_repos[project_name]
            self.repo_url_var.set(config['url'])
            self.server_path_var.set(config['local_path'])
            self.log(f"📝 已加载项目配置: {project_name}")
    
    def choose_local_dir(self):
        """选择本地目录"""
        from tkinter import filedialog
        directory = filedialog.askdirectory(title="选择本地工作目录")
        if directory:
            self.local_path_var.set(directory)
            self.log(f"📁 选择本地目录: {directory}")
    
    def set_ssh_manager(self, ssh_manager):
        """设置SSH管理器"""
        self.ssh_manager = ssh_manager
        if ssh_manager and ssh_manager.is_connected():
            self.log(f"🔗 SSH连接已就绪: {ssh_manager.ip_address}")
        else:
            self.log("⚠️ 请先在主程序中连接服务器")
    
    def download_from_server(self):
        """从服务器下载项目"""
        if not self.ssh_manager or not self.ssh_manager.is_connected():
            messagebox.showerror("错误", "请先在主程序中连接服务器")
            return
        
        server_path = self.server_path_var.get().strip()
        local_path = self.local_path_var.get().strip()
        project_name = self.project_var.get().strip()
        
        if not all([server_path, local_path, project_name]):
            messagebox.showerror("错误", "请填写完整的路径信息")
            return
        
        def download_task():
            try:
                self.log(f"📥 开始从服务器下载项目: {project_name}")
                
                # 创建本地目录
                local_project_path = Path(local_path) / project_name
                local_project_path.mkdir(parents=True, exist_ok=True)
                
                # 获取排除模式
                exclude_patterns = self.github_repos.get(project_name, {}).get('exclude_patterns', [])
                
                # 创建tar排除选项
                exclude_options = ""
                for pattern in exclude_patterns:
                    exclude_options += f" --exclude='{pattern}'"
                
                # 在服务器上创建压缩包
                remote_tar_path = f"/tmp/{project_name}_upload_{int(datetime.now().timestamp())}.tar.gz"
                tar_cmd = f"cd {Path(server_path).parent} && tar -czf {remote_tar_path} {exclude_options} {Path(server_path).name}"
                
                self.log("🗜️ 正在服务器上创建压缩包...")
                stdout, stderr, exit_status = self.ssh_manager.execute_command(tar_cmd, timeout=300)
                
                if exit_status != 0:
                    self.log(f"❌ 创建压缩包失败: {stderr}")
                    return False
                
                # 下载压缩包
                local_tar_path = local_project_path.parent / f"{project_name}.tar.gz"
                self.log("📥 正在下载压缩包...")
                
                if not self.ssh_manager.download_file(remote_tar_path, str(local_tar_path)):
                    self.log("❌ 下载失败")
                    return False
                
                # 解压缩
                self.log("📦 正在解压文件...")
                extract_cmd = ["tar", "-xzf", str(local_tar_path), "-C", str(local_project_path.parent)]
                result = subprocess.run(extract_cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    self.log(f"❌ 解压失败: {result.stderr}")
                    return False
                
                # 清理临时文件
                os.remove(local_tar_path)
                self.ssh_manager.execute_command(f"rm -f {remote_tar_path}")
                
                # 更新文件预览
                self.update_file_preview(local_project_path)
                
                self.log(f"✅ 项目下载完成: {local_project_path}")
                return True
                
            except Exception as e:
                self.log(f"❌ 下载出错: {e}")
                return False
        
        threading.Thread(target=download_task, daemon=True).start()
    
    def upload_to_github(self):
        """上传到GitHub"""
        local_path = self.local_path_var.get().strip()
        project_name = self.project_var.get().strip()
        repo_url = self.repo_url_var.get().strip()
        git_user = self.git_user_var.get().strip()
        git_email = self.git_email_var.get().strip()
        
        if not all([local_path, project_name, repo_url]):
            messagebox.showerror("错误", "请填写完整的配置信息")
            return
        
        if not all([git_user, git_email]):
            messagebox.showerror("错误", "请填写Git用户信息")
            return
        
        def upload_task():
            try:
                project_path = Path(local_path) / project_name
                
                if not project_path.exists():
                    self.log(f"❌ 本地项目不存在: {project_path}")
                    return False
                
                self.log(f"📤 开始上传到GitHub: {repo_url}")
                
                # 进入项目目录
                os.chdir(project_path)
                
                # 配置Git用户信息
                self.log("🔧 配置Git用户信息...")
                subprocess.run(["git", "config", "user.name", git_user], check=True)
                subprocess.run(["git", "config", "user.email", git_email], check=True)
                
                # 检查是否已经是Git仓库
                if not (project_path / ".git").exists():
                    self.log("🆕 初始化Git仓库...")
                    subprocess.run(["git", "init"], check=True)
                    subprocess.run(["git", "remote", "add", "origin", repo_url], check=True)
                else:
                    self.log("🔍 检查远程仓库...")
                    # 检查远程仓库URL
                    result = subprocess.run(["git", "remote", "get-url", "origin"], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        current_url = result.stdout.strip()
                        if current_url != repo_url:
                            self.log("🔄 更新远程仓库URL...")
                            subprocess.run(["git", "remote", "set-url", "origin", repo_url], check=True)
                    else:
                        subprocess.run(["git", "remote", "add", "origin", repo_url], check=True)
                
                # 创建.gitignore文件
                self.create_gitignore(project_path)
                
                # 添加所有文件
                self.log("📝 添加文件到Git...")
                subprocess.run(["git", "add", "."], check=True)
                
                # 提交
                commit_message = f"Upload {project_name} from server - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                self.log("💾 提交更改...")
                subprocess.run(["git", "commit", "-m", commit_message], check=True)
                
                # 推送到GitHub
                self.log("🚀 推送到GitHub...")
                # 首次推送可能需要设置upstream
                result = subprocess.run(["git", "push", "-u", "origin", "main"], 
                                      capture_output=True, text=True)
                
                if result.returncode != 0:
                    # 尝试推送到master分支
                    self.log("🔄 尝试推送到master分支...")
                    subprocess.run(["git", "push", "-u", "origin", "master"], check=True)
                
                self.log(f"✅ 上传完成: {repo_url}")
                messagebox.showinfo("成功", f"项目已成功上传到GitHub！\n\n仓库地址:\n{repo_url}")
                return True
                
            except subprocess.CalledProcessError as e:
                self.log(f"❌ Git命令执行失败: {e}")
                return False
            except Exception as e:
                self.log(f"❌ 上传出错: {e}")
                return False
        
        threading.Thread(target=upload_task, daemon=True).start()
    
    def full_upload_process(self):
        """完整的上传流程"""
        if not self.ssh_manager or not self.ssh_manager.is_connected():
            messagebox.showerror("错误", "请先在主程序中连接服务器")
            return
        
        project_name = self.project_var.get().strip()
        if not project_name:
            messagebox.showerror("错误", "请选择要上传的项目")
            return
        
        # 确认操作
        if not messagebox.askyesno("确认上传", 
            f"确定要执行完整的上传流程吗？\n\n"
            f"项目: {project_name}\n"
            f"仓库: {self.repo_url_var.get()}\n\n"
            f"这将会：\n"
            f"1. 从服务器下载项目\n"
            f"2. 清理不必要的文件\n"
            f"3. 上传到GitHub"):
            return
        
        def full_process():
            # 步骤1：下载
            self.log("🎯 开始完整上传流程...")
            download_success = False
            
            # 等待下载完成
            def wait_for_download():
                nonlocal download_success
                self.download_from_server()
                # 简单等待机制
                import time
                time.sleep(5)  # 等待下载开始
                download_success = True
            
            download_thread = threading.Thread(target=wait_for_download, daemon=True)
            download_thread.start()
            download_thread.join(timeout=300)  # 5分钟超时
            
            if download_success:
                # 等待一段时间确保下载完成
                import time
                time.sleep(10)
                
                # 步骤2：上传
                self.upload_to_github()
            else:
                self.log("❌ 下载超时或失败")
        
        threading.Thread(target=full_process, daemon=True).start()
    
    def create_gitignore(self, project_path):
        """创建.gitignore文件"""
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log

# Temporary files
*.tmp
*.temp
.DS_Store
Thumbs.db

# Large files
*.tar.gz
*.zip
*.7z

# Model files
*.pth
*.pt
*.ckpt
*.model

# Data files
datasets/
data/
results/
checkpoints/
wandb/

# Backup files
backups/
*.backup
"""
        gitignore_path = project_path / ".gitignore"
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        
        self.log("📝 已创建.gitignore文件")
    
    def update_file_preview(self, project_path):
        """更新文件预览"""
        # 清空现有内容
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        def add_directory(parent_id, dir_path, level=0):
            if level > 3:  # 限制显示深度
                return
            
            try:
                for item in sorted(dir_path.iterdir()):
                    if item.name.startswith('.') and item.name not in ['.gitignore', '.github']:
                        continue
                    
                    item_id = self.file_tree.insert(parent_id, "end", text=item.name)
                    
                    if item.is_dir() and level < 3:
                        add_directory(item_id, item, level + 1)
            except PermissionError:
                pass
        
        if project_path.exists():
            add_directory("", project_path)
            self.log(f"📂 文件预览已更新: {len(list(project_path.rglob('*')))} 个文件")

def main():
    """主函数"""
    root = tk.Tk()
    app = GitHubUploadHelper(root)
    
    # 如果是作为独立程序运行，显示提示
    app.log("⚠️ 独立运行模式")
    app.log("💡 建议从主程序启动以获得SSH连接")
    
    root.mainloop()

if __name__ == "__main__":
    main() 