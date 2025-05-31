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
import configparser

# 添加模块路径
sys.path.append(str(Path(__file__).parent))

from quick_setup import QuickSetup
from connect.ssh_manager import SSHManager
from connect.pem_handler import PEMHandler
from projects.github_manager import GitHubManager
from backup.backup_manager import BackupManager
from user_mode import UserModePanel

class ServerManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 服务器管理系统")
        self.root.geometry("1200x800")
        
        # 加载配置
        self.config = configparser.ConfigParser()
        self.load_config()
        
        # 初始化管理器
        self.quick_setup = QuickSetup()
        self.ssh_manager = SSHManager()
        self.pem_handler = PEMHandler()
        self.github_manager = GitHubManager()
        self.backup_manager = BackupManager()
        
        # 状态变量
        self.connected = False
        self.current_ip = ""
        self.is_admin_mode = False
        
        # 设置初始模式选择UI
        self.setup_mode_selection()
        
    def load_config(self):
        """加载配置文件"""
        config_file = Path("config/server_config.ini")
        
        # 如果配置文件不存在，创建默认配置
        if not config_file.exists():
            os.makedirs("config", exist_ok=True)
            self.config["PEM"] = {
                "default_path": str(Path.home() / ".ssh"),
                "search_paths": "\n".join([
                    str(Path.home() / ".ssh"),
                    str(Path.home() / "Documents"),
                    str(Path.home() / "Desktop"),
                    "E:\\server_connect",
                    "."
                ])
            }
            with open(config_file, "w") as f:
                self.config.write(f)
        else:
            self.config.read(config_file)
    
    def setup_mode_selection(self):
        """设置初始模式选择界面"""
        # 清除现有界面
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        # 标题
        title_label = ttk.Label(main_frame, 
                              text="🚀 服务器管理系统",
                              font=("Arial", 24, "bold"))
        title_label.pack(pady=(0, 50))
        
        # 模式选择框架
        mode_frame = ttk.Frame(main_frame)
        mode_frame.pack(expand=True)
        
        # Root模式按钮
        root_btn = ttk.Button(mode_frame,
                            text="👑 Root管理模式",
                            command=lambda: self.select_mode(True),
                            width=30)
        root_btn.pack(pady=10)
        ttk.Label(mode_frame,
                 text="用于创建用户和管理系统",
                 font=("Arial", 10)).pack()
        
        # 分隔线
        ttk.Separator(mode_frame, orient="horizontal").pack(fill=tk.X, pady=30)
        
        # 用户模式按钮
        user_btn = ttk.Button(mode_frame,
                           text="👤 用户模式",
                           command=lambda: self.select_mode(False),
                           width=30)
        user_btn.pack(pady=10)
        ttk.Label(mode_frame,
                 text="用于管理个人项目和资源",
                 font=("Arial", 10)).pack()
    
    def select_mode(self, is_admin):
        """选择管理模式"""
        self.is_admin_mode = is_admin
        if is_admin:
            self.setup_connection_ui()  # root模式：原有连接界面
        else:
            # 用户模式：直接进入UserModePanel，不显示PEM和连接界面
            for widget in self.root.winfo_children():
                widget.destroy()
            self.user_panel = UserModePanel(
                self.root,
                self.ssh_manager,
                self.github_manager,
                self.backup_manager,
                self.log
            )
    
    def setup_connection_ui(self):
        """设置连接服务器界面"""
        # 清除现有界面
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        # 标题
        mode_text = "Root管理模式" if self.is_admin_mode else "用户模式"
        title_label = ttk.Label(main_frame, 
                              text=f"🚀 服务器管理系统 - {mode_text}",
                              font=("Arial", 24, "bold"))
        title_label.pack(pady=(0, 30))
        
        # 连接框架
        conn_frame = ttk.LabelFrame(main_frame, text="🔌 服务器连接", padding="20")
        conn_frame.pack(expand=True, fill=tk.BOTH)
        
        # IP地址输入
        ttk.Label(conn_frame, text="服务器IP:").pack(anchor=tk.W, pady=(0, 5))
        self.ip_var = tk.StringVar()
        ttk.Entry(conn_frame, textvariable=self.ip_var, width=40).pack(fill=tk.X)
        
        # PEM文件选择
        ttk.Label(conn_frame, text="PEM文件:").pack(anchor=tk.W, pady=(20, 5))
        pem_frame = ttk.Frame(conn_frame)
        pem_frame.pack(fill=tk.X)
        
        self.pem_var = tk.StringVar()
        ttk.Entry(pem_frame, textvariable=self.pem_var, width=30).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(pem_frame, text="浏览", command=self.browse_pem_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(pem_frame, text="自动查找", command=self.auto_find_pem).pack(side=tk.LEFT)
        
        # PEM文件状态
        self.pem_status_label = ttk.Label(conn_frame, text="❌ 未找到PEM文件", foreground="red")
        self.pem_status_label.pack(pady=10)
        
        # 连接按钮
        ttk.Button(conn_frame, 
                  text="🔗 连接服务器",
                  command=self.connect_and_enter_main,
                  width=30).pack(pady=20)
        
        # 返回按钮
        ttk.Button(main_frame,
                  text="⬅️ 返回模式选择",
                  command=self.setup_mode_selection,
                  width=20).pack(pady=20)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="📝 连接日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        self.log_text = tk.Text(log_frame, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 初始化时自动查找PEM文件
        self.auto_find_pem()
    
    def connect_and_enter_main(self):
        """连接服务器并进入主界面"""
        if self.connect_server():
            if self.is_admin_mode:
                self.setup_admin_main_ui()
            else:
                # 清除现有界面
                for widget in self.root.winfo_children():
                    widget.destroy()
                # 创建用户模式面板
                self.user_panel = UserModePanel(
                    self.root,
                    self.ssh_manager,
                    self.github_manager,
                    self.backup_manager,
                    self.log
                )
    
    def connect_server(self):
        """连接到服务器"""
        if not self.pem_var.get():
            messagebox.showwarning("警告", "请先选择PEM文件")
            return False
            
        ip = self.ip_var.get().strip()
        if not ip:
            messagebox.showwarning("警告", "请输入服务器IP")
            return False
            
        self.current_ip = ip
        self.log(f"🔄 正在连接到服务器 {ip}...")
        
        try:
            if self.ssh_manager.connect(ip, "root", self.pem_var.get()):
                self.connected = True
                self.log("✅ 服务器连接成功")
                return True
            else:
                self.log("❌ 服务器连接失败")
                return False
        except Exception as e:
            self.log(f"❌ 连接出错: {str(e)}")
            return False
    
    def setup_admin_main_ui(self):
        """设置管理员主界面"""
        # 清除现有界面
        for widget in self.root.winfo_children():
            widget.destroy()
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(expand=True, fill=tk.BOTH)
        # 顶部标题栏
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(title_frame, 
                 text="👑 服务器管理系统 - Root管理模式",
                 font=("Arial", 24, "bold")).pack(side=tk.LEFT)
        ttk.Button(title_frame,
                  text="⬅️ 返回连接",
                  command=self.setup_connection_ui,
                  width=15).pack(side=tk.RIGHT)
        # 创建左右分栏
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(expand=True, fill=tk.BOTH)
        # 左侧 - 用户管理面板
        left_frame = ttk.LabelFrame(content_frame, text="👥 用户管理", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        # 用户列表
        self.user_tree = ttk.Treeview(left_frame, columns=("权限", "状态"), height=15)
        self.user_tree.heading("#0", text="用户名")
        self.user_tree.heading("权限", text="权限")
        self.user_tree.heading("状态", text="状态")
        self.user_tree.column("#0", width=150)
        self.user_tree.column("权限", width=100)
        self.user_tree.column("状态", width=100)
        self.user_tree.pack(fill=tk.BOTH, expand=True)
        # 用户管理按钮
        user_btn_frame = ttk.Frame(left_frame)
        user_btn_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(user_btn_frame, text="➕ 创建用户",
                  command=self.create_new_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(user_btn_frame, text="❌ 删除用户",
                  command=self.delete_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(user_btn_frame, text="🔄 刷新列表",
                  command=self.refresh_user_list).pack(side=tk.LEFT, padx=5)
        # 右侧 - 系统信息和日志
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        # 系统信息面板
        sys_frame = ttk.LabelFrame(right_frame, text="📊 系统信息", padding="10")
        sys_frame.pack(fill=tk.BOTH, expand=True)
        self.sys_info_text = tk.Text(sys_frame, height=8)
        self.sys_info_text.pack(fill=tk.BOTH, expand=True)
        ttk.Button(sys_frame, text="🔄 刷新信息",
                  command=self.refresh_system_info).pack(pady=(10, 0))
        # 新增：用户详细信息面板
        detail_frame = ttk.LabelFrame(right_frame, text="👤 用户详细信息", padding="10")
        detail_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        self.user_detail_text = tk.Text(detail_frame, height=10)
        self.user_detail_text.pack(fill=tk.BOTH, expand=True)
        # 日志面板
        log_frame = ttk.LabelFrame(right_frame, text="📝 操作日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        self.log_text = tk.Text(log_frame, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        # 在right_frame下方加命令行面板
        cli_frame = ttk.LabelFrame(right_frame, text="🖥️ 服务器命令行 (root)", padding="10")
        cli_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.cli_input = tk.StringVar()
        ttk.Entry(cli_frame, textvariable=self.cli_input, width=60).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(cli_frame, text="执行", command=self.run_root_command).pack(side=tk.LEFT, padx=5)
        self.cli_output = tk.Text(cli_frame, height=6)
        self.cli_output.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        # 绑定用户选择事件，选中用户时显示详细信息
        self.user_tree.bind("<<TreeviewSelect>>", self.on_user_select)
        # 初始化数据
        self.refresh_user_list()
        self.refresh_system_info()
        # 新增：命令行弹窗按钮
        ttk.Button(right_frame, text="打开命令行窗口", command=self.open_cli_window).pack(pady=10)
    
    def open_cli_window(self):
        """弹出命令行窗口，支持回车执行"""
        cli_win = tk.Toplevel(self.root)
        cli_win.title("服务器命令行 (root)")
        cli_win.geometry("700x400")
        cli_input = tk.StringVar()
        input_entry = ttk.Entry(cli_win, textvariable=cli_input, width=80)
        input_entry.pack(fill=tk.X, padx=10, pady=10)
        cli_output = tk.Text(cli_win, height=20)
        cli_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        def run_cmd(event=None):
            cmd = cli_input.get().strip()
            if not cmd:
                return
            cli_output.insert(tk.END, f"$ {cmd}\n")
            stdout, stderr, exit_code = self.ssh_manager.execute_command(cmd)
            if stdout:
                cli_output.insert(tk.END, stdout + "\n")
            if stderr:
                cli_output.insert(tk.END, stderr + "\n")
            cli_output.see(tk.END)
            cli_input.set("")
        input_entry.bind('<Return>', run_cmd)
        ttk.Button(cli_win, text="执行", command=run_cmd).pack(pady=5)
        input_entry.focus_set()
    
    def on_user_select(self, event):
        """选中用户时，显示详细信息（项目列表、空间使用）"""
        selection = self.user_tree.selection()
        if not selection:
            return
        username = self.user_tree.item(selection[0])["text"]
        projects, _, _ = self.ssh_manager.execute_command(f"ls /home/{username}/projects")
        disk, _, _ = self.ssh_manager.execute_command(f"du -sh /home/{username}")
        # 获取SSH公钥内容
        pubkey, _, _ = self.ssh_manager.execute_command(f"cat /home/{username}/.ssh/authorized_keys")
        pubkey_status = "未上传"
        pubkey_preview = ""
        if pubkey and pubkey.strip():
            pubkey_status = "已上传"
            pubkey_preview = pubkey.strip()[:50] + ("..." if len(pubkey.strip()) > 50 else "")
        # 获取所属组
        groups, _, _ = self.ssh_manager.execute_command(f"groups {username}")
        # 获取家目录
        home_dir = f"/home/{username}"
        # 获取最近登录时间
        lastlog, _, _ = self.ssh_manager.execute_command(f"lastlog -u {username}")
        # 组织显示内容
        detail = f"用户名: {username}\n"
        detail += f"项目列表:\n{projects if projects else '无项目'}\n"
        detail += f"空间使用: {disk if disk else '未知'}\n"
        detail += f"SSH公钥: {pubkey_status}\n"
        if pubkey_status == "已上传":
            detail += f"公钥预览: {pubkey_preview}\n"
        detail += f"所属组: {groups.strip()}\n"
        detail += f"家目录: {home_dir}\n"
        detail += f"最近登录: {lastlog.splitlines()[-1] if lastlog else '未知'}\n"
        self.user_detail_text.delete(1.0, tk.END)
        self.user_detail_text.insert(1.0, detail)
        # 添加上传公钥按钮
        if not hasattr(self, 'upload_key_btn'):
            self.upload_key_btn = ttk.Button(self.user_detail_text.master, text="上传/更新SSH公钥", command=lambda: self.upload_user_pubkey(username))
            self.upload_key_btn.pack(pady=5)
        else:
            self.upload_key_btn.config(command=lambda: self.upload_user_pubkey(username))

    def upload_user_pubkey(self, username):
        """上传/更新用户SSH公钥"""
        pubkey_file = filedialog.askopenfilename(title="选择SSH公钥文件", filetypes=[("公钥文件", "*.pub"), ("所有文件", "*.*")])
        if not pubkey_file:
            return
        with open(pubkey_file, 'r') as f:
            pubkey = f.read().strip()
        cmd = f"echo '{pubkey}' > /home/{username}/.ssh/authorized_keys && chown {username}:{username} /home/{username}/.ssh/authorized_keys && chmod 600 /home/{username}/.ssh/authorized_keys"
        _, stderr, exit_code = self.ssh_manager.execute_command(f"sudo {cmd}")
        if exit_code == 0:
            self.log(f"✅ 公钥已上传到 {username} 用户")
            messagebox.showinfo("成功", f"公钥已上传到 {username} 用户！")
        else:
            self.log(f"❌ 公钥上传失败: {stderr}")
            messagebox.showerror("失败", f"公钥上传失败: {stderr}")

    def setup_admin_user_panel(self, parent):
        """设置管理员的用户管理面板"""
        user_frame = ttk.LabelFrame(parent, text="👥 用户管理", padding="10")
        user_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # 用户列表
        ttk.Label(user_frame, text="系统用户:").grid(row=0, column=0, sticky=tk.W)
        
        # 用户列表树形视图
        self.user_tree = ttk.Treeview(user_frame, columns=("权限", "状态"), height=10)
        self.user_tree.heading("#0", text="用户名")
        self.user_tree.heading("权限", text="权限")
        self.user_tree.heading("状态", text="状态")
        
        self.user_tree.column("#0", width=120)
        self.user_tree.column("权限", width=80)
        self.user_tree.column("状态", width=80)
        
        self.user_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 滚动条
        user_scroll = ttk.Scrollbar(user_frame, orient="vertical", command=self.user_tree.yview)
        user_scroll.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.user_tree.configure(yscrollcommand=user_scroll.set)
        
        # 用户操作按钮
        btn_frame = ttk.Frame(user_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="➕ 创建用户", command=self.create_new_user).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="❌ 删除用户", command=self.delete_user).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="🔄 刷新列表", command=self.refresh_user_list).grid(row=0, column=2, padx=5)
        
    def setup_admin_info_panel(self, parent):
        """设置管理员的系统信息和日志面板"""
        info_frame = ttk.Frame(parent)
        info_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 系统信息
        sys_frame = ttk.LabelFrame(info_frame, text="📊 系统信息", padding="10")
        sys_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.sys_info_text = tk.Text(sys_frame, height=8, width=50)
        self.sys_info_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(sys_frame, text="🔄 刷新信息", 
                  command=self.refresh_system_info).grid(row=1, column=0, pady=(5, 0))
        
        # 日志输出
        log_frame = ttk.LabelFrame(info_frame, text="📝 操作日志", padding="10")
        log_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = tk.Text(log_frame, height=12, width=50)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 滚动条
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=log_scroll.set)
        
        # 配置权重
        info_frame.rowconfigure(1, weight=1)
        info_frame.columnconfigure(0, weight=1)
        
    def create_new_user(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("创建新用户")
        dialog.geometry("600x520")
        dialog.minsize(600, 520)
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        # 用户信息
        input_frame = ttk.LabelFrame(main_frame, text="用户信息", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(input_frame, text="用户名*:").grid(row=0, column=0, sticky=tk.W)
        username_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=username_var, width=18).grid(row=0, column=1, sticky=tk.W)
        ttk.Label(input_frame, text="密码*:").grid(row=0, column=2, sticky=tk.W)
        password_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=password_var, show="*", width=18).grid(row=0, column=3, sticky=tk.W)
        ttk.Label(input_frame, text="确认密码*:").grid(row=1, column=0, sticky=tk.W)
        confirm_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=confirm_var, show="*", width=18).grid(row=1, column=1, sticky=tk.W)
        # SSH公钥上传（文件方式）
        ttk.Label(input_frame, text="SSH公钥(可选):").grid(row=2, column=0, sticky=tk.W)
        sshkey_file_var = tk.StringVar()
        sshkey_preview_var = tk.StringVar(value="未上传")
        def upload_sshkey_file():
            pubkey_file = filedialog.askopenfilename(title="选择SSH公钥文件", filetypes=[("公钥文件", "*.pub"), ("所有文件", "*.*")])
            if not pubkey_file:
                return
            sshkey_file_var.set(pubkey_file)
            with open(pubkey_file, 'r') as f:
                pubkey = f.read().strip()
            sshkey_preview_var.set(pubkey[:50] + ("..." if len(pubkey) > 50 else ""))
        ttk.Button(input_frame, text="上传公钥", command=upload_sshkey_file).grid(row=2, column=1, sticky=tk.W)
        ttk.Label(input_frame, textvariable=sshkey_preview_var, foreground="gray").grid(row=2, column=2, columnspan=2, sticky=tk.W)
        ttk.Label(input_frame, text="（可留空，后续可在管理界面上传）", foreground="gray").grid(row=3, column=1, columnspan=3, sticky=tk.W)
        # 资源限制
        resource_frame = ttk.LabelFrame(main_frame, text="资源限制", padding="10")
        resource_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(resource_frame, text="磁盘配额(GB)*:").grid(row=0, column=0, sticky=tk.W)
        disk_quota_var = tk.StringVar(value="10")
        disk_entry = ttk.Entry(resource_frame, textvariable=disk_quota_var, width=8)
        disk_entry.grid(row=0, column=1, sticky=tk.W)
        # 获取剩余磁盘空间
        total, used, free = 0, 0, 0
        try:
            stdout, _, _ = self.ssh_manager.execute_command("df -BG / | tail -1")
            if stdout:
                parts = stdout.split()
                total = int(parts[1].replace('G',''))
                used = int(parts[2].replace('G',''))
                free = int(parts[3].replace('G',''))
        except:
            pass
        disk_remain_var = tk.StringVar(value=f"可分配剩余空间: {free} GB")
        ttk.Label(resource_frame, textvariable=disk_remain_var, foreground="gray").grid(row=0, column=2, columnspan=2, sticky=tk.W)
        # 权限
        perm_frame = ttk.LabelFrame(main_frame, text="用户权限", padding="10")
        perm_frame.pack(fill=tk.X, pady=(0, 10))
        sudo_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(perm_frame, text="授予sudo权限", variable=sudo_var).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(perm_frame, text="所有用户自动拥有Docker权限", foreground="gray").grid(row=0, column=1, sticky=tk.W)
        # 预览和按钮
        preview_frame = ttk.LabelFrame(main_frame, text="创建预览", padding="10")
        preview_frame.pack(fill=tk.X, pady=(0, 10))
        preview_text = tk.Text(preview_frame, height=4, wrap=tk.WORD)
        preview_text.pack(fill=tk.X)
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(btn_frame, text="预览", command=lambda: update_preview()).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="确认", command=lambda: validate_and_create()).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        def update_preview():
            preview = f"用户名: {username_var.get()}\n磁盘配额: {disk_quota_var.get()} GB\nsudo权限: {'是' if sudo_var.get() else '否'}\nDocker权限: 是\nSSH公钥: {'已上传' if sshkey_file_var.get() else '未上传'}"
            preview_text.delete(1.0, tk.END)
            preview_text.insert(1.0, preview)
        def validate_and_create():
            username = username_var.get().strip()
            password = password_var.get()
            confirm = confirm_var.get()
            sshkey_file = sshkey_file_var.get().strip()
            if not username:
                messagebox.showerror("错误", "请输入用户名")
                return
            if not password:
                messagebox.showerror("错误", "请输入密码")
                return
            if password != confirm:
                messagebox.showerror("错误", "两次输入的密码不一致")
                return
            if not disk_quota_var.get().isdigit():
                messagebox.showerror("错误", "磁盘配额必须是数字")
                return
            # 检查磁盘剩余空间
            if int(disk_quota_var.get()) > free:
                messagebox.showerror("错误", f"磁盘配额不能超过剩余空间 ({free} GB)")
                return
            preview = f"确认创建以下用户：\n\n用户名: {username}\n磁盘配额: {disk_quota_var.get()} GB\nsudo权限: {'是' if sudo_var.get() else '否'}\nDocker权限: 是\nSSH公钥: {'已上传' if sshkey_file else '未上传'}\n\n是否确认创建？"
            if not messagebox.askyesno("确认创建", preview):
                return
            commands = [
                f"useradd -m -s /bin/bash {username}",
                f"echo '{username}:{password}' | chpasswd",
                f"mkdir -p /home/{username}/.ssh",
                f"touch /home/{username}/.ssh/authorized_keys",
                f"chmod 700 /home/{username}/.ssh",
                f"chmod 600 /home/{username}/.ssh/authorized_keys",
                f"chown -R {username}:{username} /home/{username}/.ssh",
                f"chown {username}:{username} /home/{username}",
                f"chmod 755 /home/{username}",
                f"usermod -aG docker {username}"
            ]
            if sudo_var.get():
                commands.append(f"usermod -aG sudo {username}")
            quota_kb = int(disk_quota_var.get()) * 1024 * 1024
            commands.append(f"setquota -u {username} {quota_kb} {quota_kb} 0 0 /")
            success = True
            for cmd in commands:
                _, stderr, exit_code = self.ssh_manager.execute_command(f"sudo {cmd}")
                if exit_code != 0:
                    if "useradd" in cmd and "already exists" in stderr:
                        messagebox.showwarning("用户已存在", f"用户 {username} 已存在！")
                        self.log(f"⚠️ 用户 {username} 已存在")
                        dialog.destroy()
                        return
                    if "setquota" in cmd and ("not found" in stderr or "未找到" in stderr):
                        messagebox.showwarning("未安装setquota", "服务器未安装setquota，磁盘配额未生效。可用 sudo apt install quota 安装。")
                        self.log("⚠️ 服务器未安装setquota，磁盘配额未生效")
                        continue
                    self.log(f"❌ 命令执行失败: {cmd}")
                    self.log(f"错误信息: {stderr}")
                    success = False
                    break
            # 如果上传了ssh key文件，自动写入authorized_keys
            if sshkey_file and success:
                with open(sshkey_file, 'r') as f:
                    pubkey = f.read().strip()
                cmd = f"echo '{pubkey}' > /home/{username}/.ssh/authorized_keys && chown {username}:{username} /home/{username}/.ssh/authorized_keys && chmod 600 /home/{username}/.ssh/authorized_keys"
                _, stderr, exit_code = self.ssh_manager.execute_command(f"sudo {cmd}")
                if exit_code == 0:
                    self.log(f"✅ SSH公钥已写入 {username} 用户")
                else:
                    self.log(f"❌ SSH公钥写入失败: {stderr}")
            if success:
                self.log(f"✅ 用户 {username} 创建成功")
                self.refresh_user_list()
                dialog.destroy()
            else:
                messagebox.showerror("错误", "创建用户失败，请查看日志")
        update_preview()
        dialog.grab_set()
        dialog.wait_window()
    
    def delete_user(self):
        """删除选中的用户"""
        selection = self.user_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的用户")
            return
            
        username = self.user_tree.item(selection[0])["text"]
        
        if username == "root":
            messagebox.showerror("错误", "不能删除root用户")
            return
            
        if not messagebox.askyesno("确认删除", 
                                  f"确定要删除用户 {username} 吗？\n"
                                  "这将删除该用户的所有数据！"):
            return
            
        # 执行删除用户的命令
        cmd = f"sudo userdel -r {username}"
        _, stderr, exit_code = self.ssh_manager.execute_command(cmd)
        
        if exit_code == 0:
            self.log(f"✅ 用户 {username} 删除成功")
            self.refresh_user_list()
        else:
            self.log(f"❌ 删除用户失败: {stderr}")
            messagebox.showerror("错误", f"删除用户失败：{stderr}")
            
    def refresh_user_list(self):
        """刷新用户列表"""
        # 清空现有列表
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
            
        # 获取用户列表
        stdout, _, _ = self.ssh_manager.execute_command("cat /etc/passwd")
        if stdout:
            for line in stdout.splitlines():
                if "/home" in line:  # 只显示普通用户
                    user_info = line.split(":")
                    username = user_info[0]
                    
                    # 检查sudo权限
                    _, _, exit_code = self.ssh_manager.execute_command(f"groups {username} | grep -q sudo")
                    has_sudo = "sudo" if exit_code == 0 else "普通用户"
                    
                    # 检查是否活跃
                    _, _, exit_code = self.ssh_manager.execute_command(f"ps -u {username} | grep -q bash")
                    status = "活跃" if exit_code == 0 else "离线"
                    
                    self.user_tree.insert("", "end", text=username, values=(has_sudo, status))
                    
    def refresh_system_info(self):
        """刷新系统信息"""
        if not hasattr(self, 'sys_info_text'):
            return
            
        self.sys_info_text.delete(1.0, tk.END)
        
        # 获取系统信息
        info = self.ssh_manager.get_system_info()
        if info:
            info_text = f"""🖥️ 系统信息：
操作系统：{info.get('os', 'N/A')}
CPU核心：{info.get('cpu_cores', 'N/A')}
内存使用：{info.get('memory_used', 'N/A')}/{info.get('memory_total', 'N/A')}
磁盘使用：{info.get('disk_used', 'N/A')}/{info.get('disk_total', 'N/A')} ({info.get('disk_usage', 'N/A')})
"""
            self.sys_info_text.insert(1.0, info_text)
        else:
            self.sys_info_text.insert(1.0, "❌ 无法获取系统信息")
    
    def setup_user_ui(self):
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
        self.root.after(0, self._log_message, message)
    
    def _log_message(self, message):
        """在主线程中添加日志消息"""
        if self.log_text:
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.see(tk.END)
            self.root.update()
    
    def auto_find_pem(self):
        """自动查找PEM文件"""
        def find_task():
            self.log("🔍 正在自动查找PEM文件...")
            
            # 从配置文件获取搜索路径
            search_paths = self.config.get("PEM", "search_paths", fallback="").split("\n")
            search_paths = [path.strip() for path in search_paths if path.strip()]
            
            # 添加当前目录到搜索路径
            search_paths.append(os.path.dirname(os.path.abspath(__file__)))
            
            # 遍历所有可能的路径
            for path in search_paths:
                expanded_path = os.path.expanduser(path)
                if not os.path.exists(expanded_path):
                    continue
                    
                # 搜索.pem文件
                for file in os.listdir(expanded_path):
                    if file.endswith('.pem'):
                        pem_path = os.path.join(expanded_path, file)
                        if self.pem_handler._is_valid_pem_file(pem_path):
                            self.root.after(0, lambda: self.update_pem_status(pem_path))
                            return
            
            self.root.after(0, lambda: self.show_pem_not_found())
        
        threading.Thread(target=find_task, daemon=True).start()

    def update_pem_status(self, pem_path):
        """更新PEM文件状态"""
        self.pem_var.set(pem_path)
        self.pem_status_label.configure(text="✅ PEM文件已找到", foreground="green")
        self.log(f"✅ 自动找到PEM文件: {pem_path}")
                
    def show_pem_not_found(self):
        """显示未找到PEM文件的提示"""
        self.pem_status_label.configure(text="❌ 未找到PEM文件", foreground="red")
        self.log("❌ 未找到PEM文件，请手动选择或上传")
        messagebox.showinfo("提示", 
                    "未找到PEM文件！\n\n"
                    "请点击'浏览'按钮选择PEM文件，\n"
                    "或将luojie.pem文件放在以下位置之一：\n"
                    "• E:\\server_connect\\ (Windows) 或 ~/.ssh/ (Linux)")
    
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
        """连接到服务器"""
        if not self.pem_var.get():
            messagebox.showwarning("警告", "请先选择PEM文件")
            return False
            
        ip = self.ip_var.get().strip()
        if not ip:
            messagebox.showwarning("警告", "请输入服务器IP")
            return False
            
        self.current_ip = ip
        self.log(f"🔄 正在连接到服务器 {ip}...")
        
        try:
            if self.ssh_manager.connect(ip, "root", self.pem_var.get()):
                    self.connected = True
                    self.log("✅ 服务器连接成功")
                    return True
            else:
                    self.log("❌ 服务器连接失败")
                    return False
        except Exception as e:
            self.log(f"❌ 连接出错: {str(e)}")
            return False
    
    def create_users(self):
        """创建用户"""
        if not self.connected:
            messagebox.showwarning("警告", "请先连接服务器")
            return
        
        if not self.ssh_manager.is_connected():
            self.log("🔌 重新连接服务器...")
            try:
                if not self.ssh_manager.connect(self.current_ip, "root", self.pem_var.get()):
                    self.log("❌ 服务器连接失败")
                    return
            except Exception as e:
                self.log(f"❌ 连接失败: {str(e)}")
            return
        
        def task():
            self.log("👥 开始创建用户...")
            try:
                success = self.quick_setup.setup_users()
                if success:
                    self.log("✅ 用户创建完成")
                    self.root.after(1000, self.check_users)
                else:
                    self.log("❌ 用户创建失败")
            except Exception as e:
                self.log(f"❌ 创建用户时发生错误: {str(e)}")
        
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

    def run_root_command(self):
        """在root模式下执行命令并显示结果"""
        cmd = self.cli_input.get().strip()
        if not cmd:
            return
        self.cli_output.insert(tk.END, f"$ {cmd}\n")
        stdout, stderr, exit_code = self.ssh_manager.execute_command(cmd)
        if stdout:
            self.cli_output.insert(tk.END, stdout + "\n")
        if stderr:
            self.cli_output.insert(tk.END, stderr + "\n")
        self.cli_output.see(tk.END)

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

#嘿嘿