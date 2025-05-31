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
                print(f"🔄 开始连接到 {username}@{ip_address}")
                print(f"⏳ 连接超时设置: {timeout}秒")
                
                # 关闭现有连接
                if self.client:
                    print("🔄 关闭现有连接...")
                    self.client.close()
                
                # 创建新连接
                print("🔄 创建新的SSH客户端...")
                self.client = paramiko.SSHClient()
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # 连接参数
                connect_kwargs = {
                    'hostname': ip_address,
                    'username': username,
                    'timeout': timeout,
                    'look_for_keys': False,
                    'allow_agent': False,
                    'banner_timeout': 60,  # 增加banner超时时间
                    'auth_timeout': 60,    # 增加认证超时时间
                    'port': 22             # 明确指定端口
                }
                
                # 使用PEM文件或密码
                if pem_file_path and os.path.exists(pem_file_path):
                    print(f"🔑 正在读取PEM文件: {pem_file_path}")
                    try:
                        # 尝试不同的密钥类型
                        try:
                            pkey = paramiko.RSAKey.from_private_key_file(pem_file_path)
                        except:
                            try:
                                pkey = paramiko.Ed25519Key.from_private_key_file(pem_file_path)
                            except:
                                pkey = paramiko.DSSKey.from_private_key_file(pem_file_path)
                        
                        connect_kwargs['pkey'] = pkey
                        print("✅ PEM文件读取成功")
                    except Exception as e:
                        print(f"❌ PEM文件读取失败: {str(e)}")
                        if "not a valid RSA private key file" in str(e):
                            print("提示: 请确保PEM文件是有效的私钥格式")
                        return False
                elif password:
                    print("🔑 使用密码连接")
                    connect_kwargs['password'] = password
                else:
                    print("❌ 没有提供有效的认证方式")
                    return False
                
                print(f"🔄 正在连接到 {ip_address}...")
                print("连接参数:")
                print(f"  - 用户名: {username}")
                print(f"  - 超时时间: {timeout}秒")
                print(f"  - 认证方式: {'PEM密钥' if pem_file_path else '密码'}")
                
                # 建立连接
                try:
                    self.client.connect(**connect_kwargs)
                    print("✅ 初始连接成功")
                except paramiko.AuthenticationException as e:
                    print(f"❌ SSH认证失败: {str(e)}")
                    print("请检查:")
                    print("1. PEM文件是否正确")
                    print("2. 用户名是否正确")
                    print("3. 服务器是否允许密钥认证")
                    print("4. PEM文件的格式和权限是否正确")
                    return False
                except paramiko.SSHException as e:
                    print(f"❌ SSH连接错误: {str(e)}")
                    print("可能的原因:")
                    print("1. SSH服务未启动")
                    print("2. SSH配置问题")
                    print("3. 网络连接问题")
                    return False
                except socket.timeout:
                    print("❌ 连接超时，请检查:")
                    print("1. 服务器IP是否正确")
                    print("2. 服务器是否在线")
                    print("3. 防火墙是否允许SSH连接")
                    print("4. 网络连接是否稳定")
                    return False
                except socket.error as e:
                    print(f"❌ 网络错误: {str(e)}")
                    print("可能的原因:")
                    print("1. 网络连接不稳定")
                    print("2. DNS解析问题")
                    print("3. 防火墙拦截")
                    return False
                
                print("🔄 正在测试连接...")
                
                # 测试连接
                try:
                    print("发送测试命令: echo 'connection test'")
                    stdin, stdout, stderr = self.client.exec_command('echo "connection test"', timeout=10)
                    result = stdout.read().decode().strip()
                    error = stderr.read().decode().strip()
                    
                    if error:
                        print(f"⚠️ 命令错误输出: {error}")
                    
                    if result == "connection test":
                        self.ip_address = ip_address
                        self.username = username
                        self.is_connected_flag = True
                        print(f"✅ SSH连接测试成功: {username}@{ip_address}")
                        
                        # 获取系统信息
                        try:
                            print("🔄 获取系统信息...")
                            stdin, stdout, stderr = self.client.exec_command("uname -a")
                            system_info = stdout.read().decode().strip()
                            print(f"📊 系统信息: {system_info}")
                        except Exception as e:
                            print(f"⚠️ 无法获取系统信息: {str(e)}")
                        
                        return True
                    else:
                        print("❌ 连接测试失败")
                        print(f"预期输出: 'connection test'")
                        print(f"实际输出: '{result}'")
                        return False
                except Exception as e:
                    print(f"❌ 连接测试失败: {str(e)}")
                    return False
                    
        except Exception as e:
            print(f"❌ 连接过程中发生错误: {str(e)}")
            print(f"错误类型: {type(e).__name__}")
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