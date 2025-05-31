import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from user_logic import UserLogic
import os
import glob
import json

class UserModePanel:
    """
    用户模式主面板，负责用户模式下的所有界面和功能
    参数：
        root: Tk主窗口
        ssh_manager: SSH管理器实例
        github_manager: GitHub管理器实例
        backup_manager: 备份管理器实例
        log_func: 日志输出函数
    """
    def __init__(self, root, ssh_manager, github_manager, backup_manager, log_func):
        self.root = root
        self.ssh_manager = ssh_manager
        self.github_manager = github_manager
        self.backup_manager = backup_manager
        self.log = log_func
        
        # 初始化业务逻辑层
        self.logic = UserLogic(ssh_manager)
        
        # 设置窗口标题
        self.root.title("🚀 服务器管理系统 - 用户模式")
        
        # 显示登录界面
        self.setup_login_ui()
        
        self.private_key_path = None  # 新增：记录用户上传的私钥路径
        
    def setup_login_ui(self):
        """设置用户登录界面"""
        # 清除现有界面
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # 创建主框架，居中显示
        main_frame = ttk.Frame(self.root, padding="40")
        main_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # 标题
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 30))
        ttk.Label(title_frame, 
                 text="🚀 服务器管理系统", 
                 font=("Arial", 24, "bold")).pack()
        ttk.Label(title_frame,
                 text="用户模式登录",
                 font=("Arial", 16)).pack()
        
        # 登录表单
        form_frame = ttk.LabelFrame(main_frame, text="👤 用户登录", padding="20")
        form_frame.pack(fill=tk.X)
        
        # 历史记录下拉框
        history_frame = ttk.Frame(form_frame)
        history_frame.pack(fill=tk.X, pady=5)
        ttk.Label(history_frame, text="📜 历史登录记录:", foreground="gray").pack(side=tk.LEFT)
        self.history_var = tk.StringVar()
        self.history_combo = ttk.Combobox(history_frame, textvariable=self.history_var, width=40)
        self.history_combo.pack(side=tk.LEFT, padx=5)
        self.load_login_history()
        self.history_combo.bind("<<ComboboxSelected>>", self.handle_select_history)
        
        # 服务器IP
        ip_frame = ttk.Frame(form_frame)
        ip_frame.pack(fill=tk.X, pady=5)
        ttk.Label(ip_frame, text="服务器IP*:", width=12).pack(side=tk.LEFT)
        self.ip_var = tk.StringVar()
        ttk.Entry(ip_frame, textvariable=self.ip_var, width=30).pack(side=tk.LEFT, padx=5)
        
        # 用户名
        user_frame = ttk.Frame(form_frame)
        user_frame.pack(fill=tk.X, pady=5)
        ttk.Label(user_frame, text="用户名*:", width=12).pack(side=tk.LEFT)
        self.username_var = tk.StringVar()
        ttk.Entry(user_frame, textvariable=self.username_var, width=30).pack(side=tk.LEFT, padx=5)
        
        # SSH私钥选择区域
        key_frame = ttk.LabelFrame(form_frame, text="🔑 SSH私钥", padding="10")
        key_frame.pack(fill=tk.X, pady=10)
        
        # 手动上传私钥
        upload_frame = ttk.Frame(key_frame)
        upload_frame.pack(fill=tk.X, pady=5)
        ttk.Button(upload_frame, 
                  text="📂 手动上传私钥",
                  style="Accent.TButton",
                  command=self.handle_upload_private_key).pack(side=tk.LEFT)
        ttk.Button(upload_frame,
                  text="🔍 自动检测私钥",
                  command=self.handle_auto_detect_keys).pack(side=tk.LEFT, padx=10)
        
        # 私钥状态显示
        self.key_status_var = tk.StringVar(value="未选择私钥")
        ttk.Label(key_frame, 
                 textvariable=self.key_status_var,
                 foreground="gray").pack(pady=5)
        
        # 按钮区域
        btn_frame = ttk.Frame(form_frame)
        btn_frame.pack(pady=20)
        
        # 创建登录按钮样式
        style = ttk.Style()
        style.configure("Accent.TButton", 
                       font=("Arial", 10, "bold"))
        
        ttk.Button(btn_frame, 
                  text="登 录",
                  style="Accent.TButton",
                  command=self.handle_login,
                  width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame,
                  text="返回模式选择",
                  command=self.back_to_mode_select,
                  width=20).pack(side=tk.LEFT, padx=5)
        
        # 状态提示
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(main_frame, 
                                    textvariable=self.status_var,
                                    wraplength=400,
                                    justify=tk.CENTER)
        self.status_label.pack(pady=20)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="📝 登录日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_text = tk.Text(log_frame, height=6, width=50)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def back_to_mode_select(self):
        """返回模式选择界面"""
        from 服务器管理器 import ServerManagerGUI
        # 清除现有界面
        for widget in self.root.winfo_children():
            widget.destroy()
        # 重新创建主程序实例
        app = ServerManagerGUI(self.root)
        app.setup_mode_selection()

    def handle_login(self):
        """处理登录按钮点击事件"""
        # 获取输入
        ip = self.ip_var.get().strip()
        username = self.username_var.get().strip()

        # 输入验证
        if not ip or not username:
            self.show_status("请输入服务器IP和用户名", "error")
            return

        # 更新状态
        self.show_status("正在连接服务器...", "info")
        self.root.update()

        # 登录时传递私钥路径
        status, message = self.logic.check_user_and_key(ip, username, self.private_key_path)

        if status == 'no_user':
            self.show_status("用户不存在，请联系管理员创建账号", "error")
        
        elif status == 'no_key':
            self.show_status("未找到SSH公钥，请上传", "warning")
            if messagebox.askyesno("上传公钥", "是否现在上传SSH公钥？"):
                self.handle_upload_key(ip, username)
        
        elif status == 'ok':
            self.show_status("登录成功！正在进入主界面...", "success")
            self.root.after(1000, self.enter_main_ui)
            self.save_login_history(ip, username, self.private_key_path)
        
        else:  # error
            self.show_status(message, "error")

    def handle_upload_key(self, ip, username):
        """处理公钥上传"""
        # 选择公钥文件
        pubkey_file = filedialog.askopenfilename(
            title="选择SSH公钥文件",
            filetypes=[("公钥文件", "*.pub"), ("所有文件", "*.*")]
        )
        if not pubkey_file:
            return

        # 上传公钥
        success, message = self.logic.upload_user_pubkey(ip, username, pubkey_file)
        
        if success:
            messagebox.showinfo("成功", "公钥上传成功，请重新登录！")
            self.show_status("公钥上传成功，请重新登录", "success")
        else:
            messagebox.showerror("错误", message)
            self.show_status(message, "error")

    def handle_upload_private_key(self):
        """处理上传本地SSH私钥"""
        key_file = filedialog.askopenfilename(
            title="选择SSH私钥文件",
            filetypes=[("私钥文件", "*.pem *.rsa *.id_rsa *.id_ed25519"), ("所有文件", "*.*")]
        )
        if not key_file:
            return
        # 检查私钥有效性
        valid, msg = self.logic.validate_private_key(key_file)
        if valid:
            self.private_key_path = key_file
            self.key_status_var.set(f"已选择: {os.path.basename(key_file)}")
            messagebox.showinfo("成功", "私钥文件有效，可以用于登录！")
        else:
            self.private_key_path = None
            self.key_status_var.set("未选择私钥")
            messagebox.showerror("错误", f"私钥无效: {msg}")

    def handle_auto_detect_keys(self):
        """自动检测并选择私钥"""
        keys = self.auto_detect_private_keys()
        if not keys:
            messagebox.showwarning("未找到私钥", "未在常见位置检测到任何SSH私钥文件，请手动上传。")
            return
        # 弹出选择框
        win = tk.Toplevel(self.root)
        win.title("选择检测到的SSH私钥")
        win.geometry("500x300")
        lb = tk.Listbox(win, width=60, height=10)
        for k in keys:
            lb.insert(tk.END, k)
        lb.pack(pady=10)
        def select_key():
            idx = lb.curselection()
            if idx:
                key_file = keys[idx[0]]
                valid, msg = self.logic.validate_private_key(key_file)
                if valid:
                    self.private_key_path = key_file
                    self.key_status_var.set(f"已选择: {os.path.basename(key_file)}")
                    messagebox.showinfo("成功", "私钥文件有效，可以用于登录！")
                    win.destroy()
                else:
                    messagebox.showerror("错误", f"私钥无效: {msg}")
        ttk.Button(win, text="选择", command=select_key).pack(pady=5)

    def auto_detect_private_keys(self):
        """自动检测本地所有常见私钥文件"""
        key_candidates = []
        # 1. 检查当前用户主目录下的.ssh
        home = os.path.expanduser("~")
        ssh_dir = os.path.join(home, ".ssh")
        if os.path.exists(ssh_dir):
            for ext in ["id_rsa", "id_ed25519", "*.pem"]:
                key_candidates += glob.glob(os.path.join(ssh_dir, ext))
        # 2. 检查C盘所有用户目录
        if os.name == "nt":
            users_dir = "C:\\Users"
            if os.path.exists(users_dir):
                for user in os.listdir(users_dir):
                    user_ssh = os.path.join(users_dir, user, ".ssh")
                    if os.path.exists(user_ssh):
                        for ext in ["id_rsa", "id_ed25519", "*.pem"]:
                            key_candidates += glob.glob(os.path.join(user_ssh, ext))
        # 3. 检查桌面、文档等
        for folder in [home, os.path.join(home, "Desktop"), os.path.join(home, "Documents")]:
            if os.path.exists(folder):
                for ext in ["id_rsa", "id_ed25519", "*.pem"]:
                    key_candidates += glob.glob(os.path.join(folder, ext))
        # 去重
        key_candidates = list(set(key_candidates))
        return key_candidates

    def show_status(self, message, status_type="info"):
        """显示状态信息"""
        colors = {
            "error": "red",
            "success": "green",
            "warning": "orange",
            "info": "black"
        }
        self.status_var.set(message)
        self.status_label.configure(foreground=colors.get(status_type, "black"))

    def enter_main_ui(self):
        """进入用户主界面"""
        # 清除现有界面
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部信息栏
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(info_frame,
                 text=f"👤 当前用户: {self.logic.current_user}",
                 font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        ttk.Label(info_frame,
                 text=f"🌐 服务器: {self.logic.current_ip}",
                 font=("Arial", 12)).pack(side=tk.LEFT, padx=20)
        
        # 创建终端区域
        terminal_frame = ttk.LabelFrame(main_frame, text="🖥️ 终端", padding="10")
        terminal_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 终端输出
        self.terminal_output = tk.Text(terminal_frame, 
                                     height=20,
                                     width=80,
                                     bg="black",
                                     fg="white",
                                     font=("Consolas", 10))
        self.terminal_output.pack(fill=tk.BOTH, expand=True)
        
        # 命令输入区
        cmd_frame = ttk.Frame(terminal_frame)
        cmd_frame.pack(fill=tk.X, pady=(10, 0))
        self.cmd_var = tk.StringVar()
        cmd_entry = ttk.Entry(cmd_frame, textvariable=self.cmd_var)
        cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        def execute_command():
            cmd = self.cmd_var.get()
            if cmd:
                self.terminal_output.insert(tk.END, f"\n$ {cmd}\n")
                stdout, stderr, _ = self.ssh_manager.execute_command(cmd)
                if stdout:
                    self.terminal_output.insert(tk.END, stdout)
                if stderr:
                    self.terminal_output.insert(tk.END, f"错误: {stderr}\n", "error")
                self.terminal_output.see(tk.END)
                self.cmd_var.set("")
        
        ttk.Button(cmd_frame,
                  text="执行",
                  command=execute_command).pack(side=tk.LEFT, padx=(5, 0))
        
        # 绑定回车键
        cmd_entry.bind("<Return>", lambda e: execute_command())
        
        # 底部按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame,
                  text="清空终端",
                  command=lambda: self.terminal_output.delete(1.0, tk.END)).pack(side=tk.LEFT)
        ttk.Button(btn_frame,
                  text="退出登录",
                  command=self.setup_login_ui).pack(side=tk.RIGHT)
        
        # 配置终端样式
        self.terminal_output.tag_configure("error", foreground="red")
        
        # 显示欢迎信息
        welcome_msg = """
🎉 登录成功！欢迎使用服务器管理系统
===============================
- 这是一个临时的功能页面
- 你可以在这里执行一些基本的命令
- 更多功能正在开发中...

输入命令并按回车执行，例如:
ls -l
pwd
whoami
        """
        self.terminal_output.insert(tk.END, welcome_msg)

    def setup_user_main_ui(self):
        """设置用户主界面"""
        # 清除现有界面
        for widget in self.root.winfo_children():
            widget.destroy()
        # 创建用户模式主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        # 标题
        title_label = ttk.Label(main_frame, 
                              text="👤 服务器管理系统 - 用户模式",
                              font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        # 左侧连接面板
        self.setup_user_connection_panel(main_frame)
        # 右侧功能区
        self.setup_user_function_panel(main_frame)
        # 底部状态栏
        self.setup_status_bar(main_frame)

    def setup_user_connection_panel(self, parent):
        """设置用户模式下的连接面板（可根据需要扩展）"""
        conn_frame = ttk.LabelFrame(parent, text="🔌 服务器连接", padding="10")
        conn_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        # 示例：显示连接信息
        ttk.Label(conn_frame, text="已连接服务器").grid(row=0, column=0, sticky=tk.W, pady=2)
        # 可扩展更多用户相关的连接信息

    def setup_user_function_panel(self, parent):
        """设置用户模式下的功能面板（如项目管理、资源监控等）"""
        func_frame = ttk.Frame(parent)
        func_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        # 创建标签页
        self.notebook = ttk.Notebook(func_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        func_frame.columnconfigure(0, weight=1)
        func_frame.rowconfigure(0, weight=1)
        # 项目管理标签页
        self.setup_project_management_tab()
        # 资源监控标签页（可扩展）
        self.setup_resource_monitor_tab()
        # 日志输出标签页
        self.setup_log_tab()

    def setup_project_management_tab(self):
        """设置项目管理标签页（可根据需要扩展）"""
        project_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(project_frame, text="📁 项目管理")
        # 示例：项目列表
        ttk.Label(project_frame, text="这里显示项目列表和操作").pack()
        # 你可以把原有的项目管理相关UI和逻辑搬过来

    def setup_resource_monitor_tab(self):
        """设置资源监控标签页（可根据需要扩展）"""
        resource_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(resource_frame, text="📊 资源监控")
        ttk.Label(resource_frame, text="这里显示资源使用情况").pack()
        # 可扩展更多资源监控功能

    def setup_log_tab(self):
        """设置日志标签页"""
        log_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(log_frame, text="📝 日志输出")
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def setup_status_bar(self, parent):
        """设置状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        self.status_var = tk.StringVar(value="🟢 用户模式已连接")
        ttk.Label(status_frame, textvariable=self.status_var).grid(row=0, column=0, sticky=tk.W)
        # 进度条
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(20, 0))
        status_frame.columnconfigure(1, weight=1)

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

    def save_login_history(self, ip, username, key_path):
        os.makedirs("config", exist_ok=True)
        history_file = "config/user_login_history.json"
        try:
            if os.path.exists(history_file):
                with open(history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            else:
                history = []
            # 去重
            entry = {"ip": ip, "username": username, "key_path": key_path or ""}
            if entry not in history:
                history.insert(0, entry)
            # 最多保存10条
            history = history[:10]
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print("保存历史失败", e)

    def load_login_history(self):
        history_file = "config/user_login_history.json"
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
            items = [f"{h['ip']} | {h['username']} | {os.path.basename(h['key_path']) if h['key_path'] else '默认'}" for h in history]
            self.history_combo['values'] = items
            self.login_history = history
        else:
            self.login_history = []

    def handle_select_history(self, event):
        idx = self.history_combo.current()
        if idx >= 0 and idx < len(self.login_history):
            h = self.login_history[idx]
            self.ip_var.set(h['ip'])
            self.username_var.set(h['username'])
            if h['key_path']:
                self.private_key_path = h['key_path']
                self.key_status_var.set(f"已选择: {os.path.basename(h['key_path'])}")
            else:
                self.private_key_path = None
                self.key_status_var.set("未选择私钥")

# 你可以继续在本文件中扩展更多用户模式相关的功能和UI
# 只要在UserModePanel类中添加方法即可
# 这样主程序和root模式完全隔离，开发维护更方便 