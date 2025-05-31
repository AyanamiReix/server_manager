#!/usr/bin/env python3
"""
SSH连接管理器
支持PEM文件连接和远程命令执行
"""

import paramiko
import socket
import time
import threading
import os
from pathlib import Path

class SSHManager:
    def __init__(self):
        self.client = None
        self.ip_address = None
        self.username = None
        self.is_connected_flag = False
        self.connection_lock = threading.Lock()
    
    def connect(self, ip_address, username="root", pem_file_path=None, password=None, timeout=30):
        """连接SSH服务器"""
        try:
            with self.connection_lock:
                # 关闭现有连接
                if self.client:
                    self.client.close()
                
                # 创建新连接
                self.client = paramiko.SSHClient()
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # 连接参数
                connect_kwargs = {
                    'hostname': ip_address,
                    'username': username,
                    'timeout': timeout,
                    'look_for_keys': False,
                    'allow_agent': False
                }
                
                # 使用PEM文件或密码
                if pem_file_path and Path(pem_file_path).exists():
                    print(f"🔑 使用PEM文件连接: {pem_file_path}")
                    pkey = paramiko.RSAKey.from_private_key_file(pem_file_path)
                    connect_kwargs['pkey'] = pkey
                elif password:
                    print("🔑 使用密码连接")
                    connect_kwargs['password'] = password
                else:
                    print("❌ 没有提供有效的认证方式")
                    return False
                
                # 建立连接
                self.client.connect(**connect_kwargs)
                
                # 测试连接
                stdin, stdout, stderr = self.client.exec_command('echo "connection test"')
                result = stdout.read().decode().strip()
                
                if result == "connection test":
                    self.ip_address = ip_address
                    self.username = username
                    self.is_connected_flag = True
                    print(f"✅ SSH连接成功: {username}@{ip_address}")
                    
                    # 获取系统信息
                    try:
                        stdin, stdout, stderr = self.client.exec_command("uname -a")
                        system_info = stdout.read().decode().strip()
                        print(f"📊 系统信息: {system_info}")
                    except Exception as e:
                        print(f"⚠️ 无法获取系统信息: {str(e)}")
                    
                    return True
                else:
                    print("❌ 连接测试失败")
                    return False
                    
        except paramiko.AuthenticationException:
            print("❌ SSH认证失败，请检查PEM文件或密码")
            return False
        except paramiko.SSHException as e:
            print(f"❌ SSH连接错误: {e}")
            return False
        except socket.timeout:
            print("❌ 连接超时")
            return False
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    def is_connected(self):
        """检查是否已连接"""
        try:
            if not self.client or not self.is_connected_flag:
                return False
            
            # 发送测试命令
            transport = self.client.get_transport()
            if transport and transport.is_active():
                return True
            else:
                self.is_connected_flag = False
                return False
        except:
            self.is_connected_flag = False
            return False
    
    def execute_command(self, command, timeout=60):
        """执行单个命令"""
        if not self.is_connected():
            print("❌ SSH未连接")
            return None, None, None
        
        try:
            print(f"🔧 执行命令: {command}")
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            
            # 等待命令完成
            exit_status = stdout.channel.recv_exit_status()
            
            stdout_text = stdout.read().decode('utf-8')
            stderr_text = stderr.read().decode('utf-8')
            
            if exit_status == 0:
                print(f"✅ 命令执行成功")
                if stdout_text.strip():
                    print(f"输出: {stdout_text.strip()}")
            else:
                print(f"⚠️ 命令退出状态: {exit_status}")
                if stderr_text.strip():
                    print(f"错误: {stderr_text.strip()}")
            
            return stdout_text, stderr_text, exit_status
            
        except Exception as e:
            print(f"❌ 命令执行失败: {e}")
            return None, None, -1
    
    def execute_script(self, script_path, *args):
        """执行本地脚本文件"""
        if not self.is_connected():
            print("❌ SSH未连接")
            return False
        
        script_file = Path(script_path)
        if not script_file.exists():
            print(f"❌ 脚本文件不存在: {script_path}")
            return False
        
        try:
            # 读取脚本内容
            with open(script_file, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            # 替换参数
            for i, arg in enumerate(args):
                script_content = script_content.replace(f"$ARG{i+1}", str(arg))
                script_content = script_content.replace(f"${i+1}", str(arg))
            
            # 上传并执行脚本
            remote_script_path = f"/tmp/temp_script_{int(time.time())}.sh"
            
            # 创建临时脚本
            sftp = self.client.open_sftp()
            with sftp.file(remote_script_path, 'w') as remote_file:
                remote_file.write(script_content)
            sftp.close()
            
            # 添加执行权限并运行
            stdout, stderr, exit_status = self.execute_command(f"chmod +x {remote_script_path}")
            if exit_status != 0:
                print(f"❌ 无法设置脚本权限")
                return False
            
            stdout, stderr, exit_status = self.execute_command(f"bash {remote_script_path}")
            
            # 清理临时文件
            self.execute_command(f"rm -f {remote_script_path}")
            
            return exit_status == 0
            
        except Exception as e:
            print(f"❌ 脚本执行失败: {e}")
            return False
    
    def upload_file(self, local_path, remote_path):
        """上传文件"""
        if not self.is_connected():
            print("❌ SSH未连接")
            return False
        
        try:
            sftp = self.client.open_sftp()
            
            # 确保远程目录存在
            remote_dir = str(Path(remote_path).parent)
            try:
                sftp.makedirs(remote_dir)
            except:
                pass  # 目录可能已存在
            
            sftp.put(local_path, remote_path)
            sftp.close()
            
            print(f"✅ 文件上传成功: {local_path} -> {remote_path}")
            return True
            
        except Exception as e:
            print(f"❌ 文件上传失败: {e}")
            return False
    
    def download_file(self, remote_path, local_path):
        """下载文件"""
        if not self.is_connected():
            print("❌ SSH未连接")
            return False
        
        try:
            sftp = self.client.open_sftp()
            
            # 确保本地目录存在
            local_dir = Path(local_path).parent
            local_dir.mkdir(parents=True, exist_ok=True)
            
            sftp.get(remote_path, local_path)
            sftp.close()
            
            print(f"✅ 文件下载成功: {remote_path} -> {local_path}")
            return True
            
        except Exception as e:
            print(f"❌ 文件下载失败: {e}")
            return False
    
    def create_directory(self, remote_path, mode=0o755):
        """创建远程目录"""
        if not self.is_connected():
            print("❌ SSH未连接")
            return False
        
        command = f"mkdir -p {remote_path} && chmod {oct(mode)[2:]} {remote_path}"
        stdout, stderr, exit_status = self.execute_command(command)
        
        if exit_status == 0:
            print(f"✅ 目录创建成功: {remote_path}")
            return True
        else:
            print(f"❌ 目录创建失败: {stderr}")
            return False
    
    def file_exists(self, remote_path):
        """检查远程文件是否存在"""
        if not self.is_connected():
            return False
        
        stdout, stderr, exit_status = self.execute_command(f"test -e {remote_path} && echo 'exists'")
        return exit_status == 0 and "exists" in stdout
    
    def get_system_info(self):
        """获取系统信息"""
        if not self.is_connected():
            return None
        
        info = {}
        
        # 操作系统
        stdout, _, _ = self.execute_command("cat /etc/os-release | grep PRETTY_NAME")
        if stdout:
            info['os'] = stdout.split('=')[1].strip().strip('"')
        
        # CPU信息
        stdout, _, _ = self.execute_command("nproc")
        if stdout:
            info['cpu_cores'] = int(stdout.strip())
        
        # 内存信息
        stdout, _, _ = self.execute_command("free -h | grep Mem")
        if stdout:
            parts = stdout.split()
            info['memory_total'] = parts[1]
            info['memory_used'] = parts[2]
            info['memory_free'] = parts[3]
        
        # 磁盘信息
        stdout, _, _ = self.execute_command("df -h / | tail -1")
        if stdout:
            parts = stdout.split()
            info['disk_total'] = parts[1]
            info['disk_used'] = parts[2]
            info['disk_free'] = parts[3]
            info['disk_usage'] = parts[4]
        
        return info
    
    def close(self):
        """关闭连接"""
        try:
            if self.client:
                self.client.close()
                self.is_connected_flag = False
                print("🔌 SSH连接已关闭")
        except:
            pass
    
    def __del__(self):
        """析构函数"""
        self.close() 