#!/usr/bin/env python3
"""
luojie & heyi 服务器管理器 - 主GUI程序
提供完整的图形界面服务器管理功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading
import json
import os
import sys
from pathlib import Path
import platform
from datetime import datetime

# 添加模块路径
sys.path.append(str(Path(__file__).parent))

from quick_setup import QuickSetup
from connect.ssh_manager import SSHManager
from connect.pem_handler import PEMHandler
from projects.github_manager import GitHubManager
from backup.backup_manager import BackupManager

class ServerManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 luojie & heyi 服务器管理器")
        self.root.geometry("1200x800")
        
        # 初始化管理器
        self.quick_setup = QuickSetup()
        self.ssh_manager = SSHManager()
        self.pem_handler = PEMHandler()
        self.github_manager = GitHubManager()
        self.backup_manager = BackupManager()
        
        # 连接状态
        self.connected = False
        self.current_ip = ""
        
        self.setup_ui()
        self.update_status()
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🚀 luojie & heyi 服务器管理器", 
                               font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 左侧面板 - 连接管理
        self.setup_connection_panel(main_frame)
        
        # 右侧面板 - 功能区域
        self.setup_function_panel(main_frame)
        
        # 底部状态栏
        self.setup_status_bar(main_frame)
    
    def setup_connection_panel(self, parent):
        """设置连接管理面板"""
        conn_frame = ttk.LabelFrame(parent, text="🔌 服务器连接", padding="10")
        conn_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # IP地址输入
        ttk.Label(conn_frame, text="服务器公网IP:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.ip_var = tk.StringVar()
        self.ip_entry = ttk.Entry(conn_frame, textvariable=self.ip_var, width=20)
        self.ip_entry.grid(row=0, column=1, pady=2, padx=(5, 0))
        
        # 用户选择
        ttk.Label(conn_frame, text="连接用户:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.connect_user_var = tk.StringVar(value="root")
        user_combo = ttk.Combobox(conn_frame, textvariable=self.connect_user_var, width=17)
        user_combo['values'] = ['root', 'luojie', 'heyi']
        user_combo.grid(row=1, column=1, pady=2, padx=(5, 0))
        
        # PEM文件路径和状态
        ttk.Label(conn_frame, text="PEM文件:").grid(row=2, column=0, sticky=tk.W, pady=2)
        pem_frame = ttk.Frame(conn_frame)
        pem_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        self.pem_var = tk.StringVar()
        self.pem_entry = ttk.Entry(pem_frame, textvariable=self.pem_var, width=12)
        self.pem_entry.grid(row=0, column=0)
        
        ttk.Button(pem_frame, text="浏览", command=self.browse_pem_file).grid(row=0, column=1, padx=(2, 0))
        ttk.Button(pem_frame, text="自动", command=self.auto_find_pem).grid(row=0, column=2, padx=(2, 0))
        
        # PEM文件状态显示
        self.pem_status_label = ttk.Label(conn_frame, text="❌ 未找到PEM文件", foreground="red")
        self.pem_status_label.grid(row=3, column=0, columnspan=2, pady=(2, 0))
        
        # 连接按钮
        self.connect_btn = ttk.Button(conn_frame, text="🔗 连接服务器", command=self.connect_server)
        self.connect_btn.grid(row=4, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E))
        
        # 连接状态
        self.status_label = ttk.Label(conn_frame, text="❌ 未连接", foreground="red")
        self.status_label.grid(row=5, column=0, columnspan=2, pady=(5, 0))
        
        # 快速连接预设
        preset_frame = ttk.LabelFrame(conn_frame, text="🚀 快速连接", padding="5")
        preset_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(preset_frame, text="💾 保存连接", command=self.save_connection_preset).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(preset_frame, text="📋 加载连接", command=self.load_connection_preset).grid(row=0, column=1, padx=(5, 0))
        
        # 服务器信息
        info_frame = ttk.LabelFrame(conn_frame, text="📊 服务器信息", padding="5")
        info_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.info_text = tk.Text(info_frame, height=6, width=30)
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        info_scroll = ttk.Scrollbar(info_frame, orient="vertical", command=self.info_text.yview)
        info_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.info_text.configure(yscrollcommand=info_scroll.set)
        
        # 初始化时自动查找PEM文件
        self.auto_find_pem()
    
    def setup_function_panel(self, parent):
        """设置功能面板"""
        func_frame = ttk.Frame(parent)
        func_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建标签页
        self.notebook = ttk.Notebook(func_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        func_frame.columnconfigure(0, weight=1)
        func_frame.rowconfigure(0, weight=1)
        
        # 服务器配置标签页
        self.setup_server_config_tab()
        
        # 项目管理标签页
        self.setup_project_management_tab()
        
        # 备份管理标签页
        self.setup_backup_management_tab()
        
        # 日志输出标签页
        self.setup_log_tab()
    
    def setup_server_config_tab(self):
        """设置服务器配置标签页"""
        server_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(server_frame, text="🚀 服务器配置")
        
        # 快速配置选项
        ttk.Label(server_frame, text="🚀 快速服务器配置", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # 配置选项
        config_options = [
            ("创建用户 (luojie, heyi)", self.create_users),
            ("配置Docker环境", self.setup_docker),
            ("完整服务器配置", self.full_server_setup),
            ("部署所有项目", self.deploy_all_projects)
        ]
        
        for i, (text, command) in enumerate(config_options):
            btn = ttk.Button(server_frame, text=text, command=command, width=25)
            btn.grid(row=i+1, column=0, pady=5, padx=(0, 10), sticky=tk.W)
        
        # 系统状态检查
        ttk.Label(server_frame, text="📊 系统状态检查", font=("Arial", 14, "bold")).grid(row=0, column=1, pady=(0, 10))
        
        status_options = [
            ("检查Docker状态", self.check_docker_status),
            ("查看用户信息", self.check_users),
            ("查看磁盘使用", self.check_disk_usage),
            ("查看系统信息", self.get_system_info)
        ]
        
        for i, (text, command) in enumerate(status_options):
            btn = ttk.Button(server_frame, text=text, command=command, width=25)
            btn.grid(row=i+1, column=1, pady=5, sticky=tk.W)
    
    def setup_project_management_tab(self):
        """设置项目管理标签页"""
        project_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(project_frame, text="📁 项目管理")
        
        # 左侧 - 项目列表
        left_frame = ttk.LabelFrame(project_frame, text="项目列表", padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 项目树形视图
        self.project_tree = ttk.Treeview(left_frame, columns=("status", "branch"), show="tree headings", height=15)
        self.project_tree.heading("#0", text="项目名称")
        self.project_tree.heading("status", text="状态")
        self.project_tree.heading("branch", text="分支")
        
        self.project_tree.column("#0", width=200)
        self.project_tree.column("status", width=80)
        self.project_tree.column("branch", width=80)
        
        self.project_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        proj_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.project_tree.yview)
        proj_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.project_tree.configure(yscrollcommand=proj_scroll.set)
        
        # 项目操作按钮
        proj_btn_frame = ttk.Frame(left_frame)
        proj_btn_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(proj_btn_frame, text="🔄 刷新列表", command=self.refresh_project_list).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(proj_btn_frame, text="🚀 部署项目", command=self.deploy_selected_project).grid(row=0, column=1, padx=5)
        ttk.Button(proj_btn_frame, text="🔄 更新项目", command=self.update_selected_project).grid(row=0, column=2, padx=(5, 0))
        
        # 右侧 - 项目详情和操作
        right_frame = ttk.LabelFrame(project_frame, text="➕ 项目操作", padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 添加项目表单
        ttk.Label(right_frame, text="项目名称:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.proj_name_var = tk.StringVar()
        ttk.Entry(right_frame, textvariable=self.proj_name_var, width=30).grid(row=0, column=1, pady=2)
        
        ttk.Label(right_frame, text="GitHub URL:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.proj_url_var = tk.StringVar()
        ttk.Entry(right_frame, textvariable=self.proj_url_var, width=30).grid(row=1, column=1, pady=2)
        
        ttk.Label(right_frame, text="分支:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.proj_branch_var = tk.StringVar(value="main")
        ttk.Entry(right_frame, textvariable=self.proj_branch_var, width=30).grid(row=2, column=1, pady=2)
        
        ttk.Label(right_frame, text="描述:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.proj_desc_var = tk.StringVar()
        ttk.Entry(right_frame, textvariable=self.proj_desc_var, width=30).grid(row=3, column=1, pady=2)
        
        # 项目操作按钮
        ttk.Button(right_frame, text="➕ 添加项目", command=self.add_project).grid(row=4, column=0, columnspan=2, pady=(10, 0))
        
        # 配置网格权重
        project_frame.columnconfigure(0, weight=1)
        project_frame.columnconfigure(1, weight=1)
        project_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
    
    def setup_backup_management_tab(self):
        """设置备份管理标签页"""
        backup_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(backup_frame, text="💾 备份管理")
        
        # 左侧 - 备份列表
        left_frame = ttk.LabelFrame(backup_frame, text="📋 备份列表", padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 备份树形视图
        self.backup_tree = ttk.Treeview(left_frame, columns=("type", "size", "date"), show="tree headings", height=15)
        self.backup_tree.heading("#0", text="项目")
        self.backup_tree.heading("type", text="类型")
        self.backup_tree.heading("size", text="大小")
        self.backup_tree.heading("date", text="日期")
        
        self.backup_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        backup_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.backup_tree.yview)
        backup_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.backup_tree.configure(yscrollcommand=backup_scroll.set)
        
        # 备份操作按钮
        backup_btn_frame = ttk.Frame(left_frame)
        backup_btn_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(backup_btn_frame, text="🔄 刷新列表", command=self.refresh_backup_list).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(backup_btn_frame, text="🔄 恢复备份", command=self.restore_selected_backup).grid(row=0, column=1, padx=5)
        ttk.Button(backup_btn_frame, text="🗑️ 删除备份", command=self.delete_selected_backup).grid(row=0, column=2, padx=(5, 0))
        
        # 右侧 - 备份操作
        right_frame = ttk.LabelFrame(backup_frame, text="💾 创建备份", padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 备份选项
        ttk.Label(right_frame, text="选择项目:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.backup_project_var = tk.StringVar()
        self.backup_project_combo = ttk.Combobox(right_frame, textvariable=self.backup_project_var, width=27)
        self.backup_project_combo.grid(row=0, column=1, pady=2)
        
        ttk.Label(right_frame, text="备份类型:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.backup_type_var = tk.StringVar(value="code")
        backup_type_combo = ttk.Combobox(right_frame, textvariable=self.backup_type_var, width=27)
        backup_type_combo['values'] = ['code', 'full', 'quick', 'custom']
        backup_type_combo.grid(row=1, column=1, pady=2)
        
        # 备份操作按钮
        ttk.Button(right_frame, text="💾 创建备份", command=self.create_backup).grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        # 备份统计
        stats_frame = ttk.LabelFrame(right_frame, text="📊 备份统计", padding="5")
        stats_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 0))
        
        self.stats_text = tk.Text(stats_frame, height=8, width=30)
        self.stats_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 配置网格权重
        backup_frame.columnconfigure(0, weight=1)
        backup_frame.columnconfigure(1, weight=1)
        backup_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
    
    def setup_log_tab(self):
        """设置日志标签页"""
        log_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(log_frame, text="📝 日志输出")
        
        # 日志文本区域
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=30)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 滚动条
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=log_scroll.set)
        
        # 日志控制按钮
        log_btn_frame = ttk.Frame(log_frame)
        log_btn_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(log_btn_frame, text="🧹 清空日志", command=self.clear_log).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(log_btn_frame, text="💾 保存日志", command=self.save_log).grid(row=0, column=1, padx=5)
        
        # 配置网格权重
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
    
    def setup_status_bar(self, parent):
        """设置状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.status_var = tk.StringVar(value="🔴 未连接到服务器")
        ttk.Label(status_frame, textvariable=self.status_var).grid(row=0, column=0, sticky=tk.W)
        
        # 进度条
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(20, 0))
        
        status_frame.columnconfigure(1, weight=1)
    
    def log(self, message):
        """添加日志消息"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def auto_find_pem(self):
        """自动查找PEM文件"""
        def find_task():
            self.log("🔍 正在自动查找PEM文件...")
            pem_path = self.pem_handler.find_pem_file_auto()
            
            if pem_path:
                self.pem_var.set(pem_path)
                self.pem_status_label.configure(text="✅ PEM文件已找到", foreground="green")
                self.log(f"✅ 自动找到PEM文件: {pem_path}")
                
                # 验证PEM文件
                if self.pem_handler.validate_pem_file(pem_path):
                    self.log("✅ PEM文件格式验证通过")
                else:
                    self.log("⚠️ PEM文件格式可能有问题")
            else:
                self.pem_status_label.configure(text="❌ 未找到PEM文件", foreground="red")
                self.log("❌ 未找到PEM文件，请手动选择或上传")
                messagebox.showinfo("提示", 
                    "未找到PEM文件！\n\n"
                    "请点击'浏览'按钮选择PEM文件，\n"
                    "或将luojie.pem文件放在以下位置之一：\n"
                    "• E:\\server_connect\\luojie.pem\n"
                    "• 用户文档文件夹\n"
                    "• 用户桌面\n"
                    "• 程序当前目录")
        
        threading.Thread(target=find_task, daemon=True).start()
    
    def browse_pem_file(self):
        """浏览PEM文件"""
        # 根据系统设置初始目录
        if platform.system() == "Windows":
            initial_dirs = [r"E:\server_connect", str(Path.home() / "Documents"), str(Path.home() / "Desktop")]
        else:
            initial_dirs = [str(Path.home() / ".ssh"), str(Path.home()), str(Path.home() / "Documents")]
        
        initial_dir = None
        for dir_path in initial_dirs:
            if os.path.exists(dir_path):
                initial_dir = dir_path
                break
        
        filename = filedialog.askopenfilename(
            title="选择PEM文件 (SSH私钥)",
            initialdir=initial_dir,
            filetypes=[
                ("PEM文件", "*.pem"),
                ("SSH私钥", "id_rsa*"),
                ("所有文件", "*.*")
            ])
        
        if filename:
            # 验证选择的文件
            if self.pem_handler._is_valid_pem_file(filename):
                self.pem_var.set(filename)
                self.pem_status_label.configure(text="✅ PEM文件已选择", foreground="green")
                self.log(f"✅ 选择PEM文件: {filename}")
                
                # 询问是否复制到标准位置
                if messagebox.askyesno("复制PEM文件", 
                    f"是否将PEM文件复制到标准位置？\n\n"
                    f"这样luojie和heyi都能使用同一个文件。\n"
                    f"标准位置: E:\\server_connect\\ (Windows) 或 ~/.ssh/ (Linux)"):
                    
                    new_path = self.pem_handler.copy_pem_file(filename)
                    if new_path:
                        self.pem_var.set(new_path)
                        self.log(f"✅ PEM文件已复制到标准位置: {new_path}")
            else:
                messagebox.showerror("文件格式错误", 
                    "选择的文件不是有效的PEM格式私钥文件！\n\n"
                    "请确保文件包含 '-----BEGIN PRIVATE KEY-----' 等标记。")
                self.log(f"❌ 无效的PEM文件: {filename}")
    
    def save_connection_preset(self):
        """保存连接预设"""
        ip = self.ip_var.get().strip()
        user = self.connect_user_var.get().strip()
        pem_file = self.pem_var.get().strip()
        
        if not all([ip, user, pem_file]):
            messagebox.showwarning("警告", "请先填写完整的连接信息")
            return
        
        preset_name = tk.simpledialog.askstring("保存连接", "请输入连接预设名称:")
        if not preset_name:
            return
        
        # 保存到配置文件
        presets_file = Path("config/connection_presets.json")
        
        if presets_file.exists():
            with open(presets_file, 'r', encoding='utf-8') as f:
                presets = json.load(f)
        else:
            presets = {}
        
        presets[preset_name] = {
            "ip": ip,
            "user": user,
            "pem_file": pem_file,
            "saved_at": datetime.now().isoformat()
        }
        
        os.makedirs("config", exist_ok=True)
        with open(presets_file, 'w', encoding='utf-8') as f:
            json.dump(presets, f, indent=2, ensure_ascii=False)
        
        self.log(f"✅ 连接预设已保存: {preset_name}")
        messagebox.showinfo("成功", f"连接预设 '{preset_name}' 已保存")
    
    def load_connection_preset(self):
        """加载连接预设"""
        presets_file = Path("config/connection_presets.json")
        
        if not presets_file.exists():
            messagebox.showinfo("提示", "没有保存的连接预设")
            return
        
        with open(presets_file, 'r', encoding='utf-8') as f:
            presets = json.load(f)
        
        if not presets:
            messagebox.showinfo("提示", "没有保存的连接预设")
            return
        
        # 创建选择对话框
        preset_window = tk.Toplevel(self.root)
        preset_window.title("选择连接预设")
        preset_window.geometry("400x300")
        
        ttk.Label(preset_window, text="选择要加载的连接预设:", font=("Arial", 12)).pack(pady=10)
        
        preset_list = tk.Listbox(preset_window, height=10)
        preset_list.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        for name, config in presets.items():
            preset_list.insert(tk.END, f"{name} ({config['user']}@{config['ip']})")
        
        def load_selected():
            selection = preset_list.curselection()
            if selection:
                preset_name = list(presets.keys())[selection[0]]
                config = presets[preset_name]
                
                self.ip_var.set(config['ip'])
                self.connect_user_var.set(config['user'])
                self.pem_var.set(config['pem_file'])
                
                # 验证PEM文件是否仍然存在
                if os.path.exists(config['pem_file']):
                    self.pem_status_label.configure(text="✅ PEM文件已加载", foreground="green")
                else:
                    self.pem_status_label.configure(text="⚠️ PEM文件不存在", foreground="orange")
                
                self.log(f"✅ 已加载连接预设: {preset_name}")
                preset_window.destroy()
        
        ttk.Button(preset_window, text="加载选中的连接", command=load_selected).pack(pady=10)
    
    def connect_server(self):
        """连接服务器"""
        ip = self.ip_var.get().strip()
        user = self.connect_user_var.get().strip()
        pem_file = self.pem_var.get().strip()
        
        if not ip:
            messagebox.showerror("错误", "请输入服务器IP地址")
            return
        
        if not user:
            messagebox.showerror("错误", "请选择连接用户")
            return
        
        def connect_thread():
            self.progress.start()
            self.connect_btn.configure(state='disabled')
            
            try:
                self.log(f"🔌 正在连接服务器: {user}@{ip}")
                
                # 智能PEM文件处理
                final_pem_file = self.pem_handler.validate_and_prepare_pem(pem_file)
                
                if not final_pem_file:
                    self.log("❌ PEM文件验证失败，尝试无密钥连接...")
                    final_pem_file = None
                
                if self.ssh_manager.connect(ip, user, final_pem_file):
                    self.connected = True
                    self.current_ip = ip
                    self.log(f"✅ 服务器连接成功！({user}@{ip})")
                    
                    # 更新PEM文件路径（如果自动找到了更好的路径）
                    if final_pem_file and final_pem_file != pem_file:
                        self.pem_var.set(final_pem_file)
                        self.pem_status_label.configure(text="✅ PEM文件已优化", foreground="green")
                    
                    # 获取服务器信息
                    info = self.ssh_manager.get_system_info()
                    if info:
                        self.display_server_info(info)
                    
                    self.update_status()
                    self.refresh_project_list()
                    self.refresh_backup_list()
                    
                    # 如果是root用户，提示可以创建其他用户
                    if user == "root":
                        self.log("💡 提示：连接成功后可以在'服务器配置'标签页创建luojie和heyi用户")
                    
                else:
                    self.log("❌ 服务器连接失败")
                    messagebox.showerror("连接失败", 
                        f"无法连接到服务器 {user}@{ip}\n\n"
                        f"可能的原因：\n"
                        f"• IP地址错误\n"
                        f"• PEM文件不正确\n"
                        f"• 用户不存在\n"
                        f"• 服务器SSH服务未启动\n\n"
                        f"建议：先用root用户连接并创建用户")
                    
            except Exception as e:
                self.log(f"❌ 连接错误: {e}")
                messagebox.showerror("连接错误", f"连接过程中发生错误:\n{e}")
            
            finally:
                self.progress.stop()
                self.connect_btn.configure(state='normal')
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def display_server_info(self, info):
        """显示服务器信息"""
        self.info_text.delete(1.0, tk.END)
        
        info_text = "🖥️ 系统信息:\n"
        info_text += f"OS: {info.get('os', 'N/A')}\n"
        info_text += f"CPU核心: {info.get('cpu_cores', 'N/A')}\n"
        info_text += f"内存: {info.get('memory_used', 'N/A')}/{info.get('memory_total', 'N/A')}\n"
        info_text += f"磁盘: {info.get('disk_used', 'N/A')}/{info.get('disk_total', 'N/A')} ({info.get('disk_usage', 'N/A')})\n"
        
        self.info_text.insert(1.0, info_text)
    
    def update_status(self):
        """更新状态显示"""
        if self.connected:
            self.status_var.set(f"🟢 已连接: {self.current_ip}")
            self.status_label.configure(text="✅ 已连接", foreground="green")
        else:
            self.status_var.set("🔴 未连接到服务器")
            self.status_label.configure(text="❌ 未连接", foreground="red")
    
    # 服务器配置方法
    def create_users(self):
        """创建用户"""
        if not self.connected:
            messagebox.showwarning("警告", "请先连接服务器")
            return
        
        def task():
            self.log("👥 开始创建用户...")
            success = self.quick_setup.setup_users()
            if success:
                self.log("✅ 用户创建完成")
            else:
                self.log("❌ 用户创建失败")
        
        threading.Thread(target=task, daemon=True).start()
    
    def setup_docker(self):
        """配置Docker"""
        if not self.connected:
            messagebox.showwarning("警告", "请先连接服务器")
            return
        
        def task():
            self.log("🐳 开始配置Docker...")
            success = self.quick_setup.setup_docker()
            if success:
                self.log("✅ Docker配置完成")
            else:
                self.log("❌ Docker配置失败")
        
        threading.Thread(target=task, daemon=True).start()
    
    def full_server_setup(self):
        """完整服务器配置"""
        if not self.connected:
            messagebox.showwarning("警告", "请先连接服务器")
            return
        
        def task():
            self.log("🚀 开始完整服务器配置...")
            success = self.quick_setup.full_setup(self.current_ip)
            if success:
                self.log("✅ 服务器配置完成")
            else:
                self.log("❌ 服务器配置失败")
        
        threading.Thread(target=task, daemon=True).start()
    
    # 项目管理方法
    def refresh_project_list(self):
        """刷新项目列表"""
        # 清空现有项目
        for item in self.project_tree.get_children():
            self.project_tree.delete(item)
        
        # 更新备份项目下拉列表
        projects = list(self.github_manager.projects.keys())
        self.backup_project_combo['values'] = projects
        
        # 添加项目到树形视图
        for name, config in self.github_manager.projects.items():
            status = "未知"
            if self.connected:
                # 检查项目是否已部署
                if self.ssh_manager.file_exists(config['deploy_path']):
                    status = "已部署"
                else:
                    status = "未部署"
            
            self.project_tree.insert("", "end", text=name,
                                    values=(status, config.get('branch', 'main')))
    
    def add_project(self):
        """添加项目"""
        name = self.proj_name_var.get().strip()
        url = self.proj_url_var.get().strip()
        branch = self.proj_branch_var.get().strip() or "main"
        description = self.proj_desc_var.get().strip()
        
        if not all([name, url]):
            messagebox.showerror("错误", "请填写项目名称和GitHub URL")
            return
        
        success = self.github_manager.add_project(name, url, branch, description)
        if success:
            self.log(f"✅ 项目已添加: {name}")
            self.refresh_project_list()
            # 清空表单
            self.proj_name_var.set("")
            self.proj_url_var.set("")
            self.proj_branch_var.set("main")
            self.proj_desc_var.set("")
        else:
            self.log(f"❌ 项目添加失败: {name}")
    
    def deploy_selected_project(self):
        """部署选中的项目"""
        if not self.connected:
            messagebox.showwarning("警告", "请先连接服务器")
            return
        
        selection = self.project_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要部署的项目")
            return
        
        item = selection[0]
        project_name = self.project_tree.item(item, "text")
        
        def task():
            self.log(f"🚀 开始部署项目: {project_name}")
            success = self.github_manager.deploy_project(project_name, self.ssh_manager)
            if success:
                self.log(f"✅ 项目部署完成: {project_name}")
                self.refresh_project_list()
            else:
                self.log(f"❌ 项目部署失败: {project_name}")
        
        threading.Thread(target=task, daemon=True).start()
    
    def deploy_all_projects(self):
        """部署所有项目"""
        if not self.connected:
            messagebox.showwarning("警告", "请先连接服务器")
            return
        
        def task():
            self.log("🚀 开始部署所有项目...")
            self.quick_setup.deploy_projects()
            self.log("✅ 所有项目部署完成")
            self.refresh_project_list()
        
        threading.Thread(target=task, daemon=True).start()
    
    def update_selected_project(self):
        """更新选中的项目"""
        if not self.connected:
            messagebox.showwarning("警告", "请先连接服务器")
            return
        
        selection = self.project_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要更新的项目")
            return
        
        item = selection[0]
        project_name = self.project_tree.item(item, "text")
        
        def task():
            self.log(f"🔄 开始更新项目: {project_name}")
            success = self.github_manager.update_project(project_name, self.ssh_manager)
            if success:
                self.log(f"✅ 项目更新完成: {project_name}")
            else:
                self.log(f"❌ 项目更新失败: {project_name}")
        
        threading.Thread(target=task, daemon=True).start()
    
    # 备份管理方法
    def refresh_backup_list(self):
        """刷新备份列表"""
        # 清空现有备份
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
        
        # 获取备份列表
        backups = self.backup_manager.list_backups()
        
        for backup in backups:
            size_str = self._format_size(backup['size'])
            date_str = backup['timestamp']
            
            self.backup_tree.insert("", "end", text=backup['project_name'],
                                  values=(backup['backup_type'], size_str, date_str))
        
        # 更新备份统计
        self.update_backup_stats()
    
    def create_backup(self):
        """创建备份"""
        if not self.connected:
            messagebox.showwarning("警告", "请先连接服务器")
            return
        
        project_name = self.backup_project_var.get().strip()
        backup_type = self.backup_type_var.get().strip()
        
        if not project_name:
            messagebox.showerror("错误", "请选择要备份的项目")
            return
        
        def task():
            self.log(f"💾 开始备份项目: {project_name} ({backup_type})")
            success = self.backup_manager.backup_project(project_name, self.ssh_manager, backup_type)
            if success:
                self.log(f"✅ 项目备份完成: {project_name}")
                self.refresh_backup_list()
            else:
                self.log(f"❌ 项目备份失败: {project_name}")
        
        threading.Thread(target=task, daemon=True).start()
    
    def restore_selected_backup(self):
        """恢复选中的备份"""
        if not self.connected:
            messagebox.showwarning("警告", "请先连接服务器")
            return
        
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要恢复的备份")
            return
        
        # 这里需要实现备份恢复逻辑
        messagebox.showinfo("提示", "备份恢复功能开发中...")
    
    def delete_selected_backup(self):
        """删除选中的备份"""
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的备份")
            return
        
        if messagebox.askyesno("确认", "确定要删除选中的备份吗？"):
            # 这里需要实现备份删除逻辑
            messagebox.showinfo("提示", "备份删除功能开发中...")
    
    def update_backup_stats(self):
        """更新备份统计"""
        stats = self.backup_manager.get_backup_statistics()
        
        self.stats_text.delete(1.0, tk.END)
        
        stats_text = "📊 备份统计:\n\n"
        stats_text += f"总备份数: {stats['total_backups']}\n"
        stats_text += f"总大小: {self._format_size(stats['total_size'])}\n\n"
        
        stats_text += "📁 项目统计:\n"
        for project, proj_stats in stats['projects'].items():
            stats_text += f"  {project}: {proj_stats['count']}个备份\n"
        
        stats_text += "\n📦 类型统计:\n"
        for backup_type, count in stats['backup_types'].items():
            stats_text += f"  {backup_type}: {count}个\n"
        
        self.stats_text.insert(1.0, stats_text)
    
    # 系统状态检查方法
    def check_docker_status(self):
        """检查Docker状态"""
        if not self.connected:
            messagebox.showwarning("警告", "请先连接服务器")
            return
        
        stdout, stderr, exit_status = self.ssh_manager.execute_command("docker ps")
        if exit_status == 0:
            self.log("🐳 Docker状态正常")
            self.log(stdout)
        else:
            self.log("❌ Docker状态异常")
            self.log(stderr)
    
    def check_users(self):
        """检查用户信息"""
        if not self.connected:
            messagebox.showwarning("警告", "请先连接服务器")
            return
        
        stdout, stderr, exit_status = self.ssh_manager.execute_command("cat /etc/passwd | grep -E '(luojie|heyi)'")
        if exit_status == 0:
            self.log("👥 用户信息:")
            self.log(stdout)
        else:
            self.log("❌ 获取用户信息失败")
    
    def check_disk_usage(self):
        """检查磁盘使用情况"""
        if not self.connected:
            messagebox.showwarning("警告", "请先连接服务器")
            return
        
        stdout, stderr, exit_status = self.ssh_manager.execute_command("df -h")
        if exit_status == 0:
            self.log("💽 磁盘使用情况:")
            self.log(stdout)
        else:
            self.log("❌ 获取磁盘信息失败")
    
    def get_system_info(self):
        """获取系统信息"""
        if not self.connected:
            messagebox.showwarning("警告", "请先连接服务器")
            return
        
        info = self.ssh_manager.get_system_info()
        if info:
            self.display_server_info(info)
            self.log("🖥️ 系统信息已更新")
        else:
            self.log("❌ 获取系统信息失败")
    
    # 日志管理方法
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
    
    def save_log(self):
        """保存日志"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("成功", f"日志已保存到: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"保存日志失败: {e}")
    
    def _format_size(self, size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

def main():
    """主函数"""
    try:
        root = tk.Tk()
        app = ServerManagerGUI(root)
        
        # 添加欢迎信息
        app.log("🎉 欢迎使用 luojie & heyi 服务器管理器!")
        app.log("💡 使用说明:")
        app.log("   1. 输入服务器IP地址和PEM文件路径")
        app.log("   2. 点击'连接服务器'建立连接")
        app.log("   3. 使用各个标签页管理服务器和项目")
        app.log("")
        
        root.mainloop()
        
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 