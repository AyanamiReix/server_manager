#!/usr/bin/env python3
"""
PEM文件处理模块
处理SSH私钥文件的权限、验证和管理
支持多路径检测和文件上传功能
"""

import os
import stat
import platform
import shutil
from pathlib import Path

class PEMHandler:
    def __init__(self):
        self.system = platform.system()
        
        # 定义多个可能的PEM文件路径
        self.default_pem_paths = self._get_default_pem_paths()
    
    def _get_default_pem_paths(self):
        """获取默认的PEM文件搜索路径"""
        paths = []
        
        if self.system == "Windows":
            # Windows环境下的常见路径
            paths.extend([
                r"E:\server_connect\luojie.pem",
                r"C:\Users\{}\Documents\SSH\luojie.pem".format(os.getenv('USERNAME', '')),
                r"C:\Users\{}\Desktop\luojie.pem".format(os.getenv('USERNAME', '')),
                r"C:\SSH\luojie.pem",
                str(Path.home() / "Documents" / "luojie.pem"),
                str(Path.home() / "Desktop" / "luojie.pem"),
                str(Path.home() / ".ssh" / "luojie.pem"),
                "./luojie.pem",
                "../luojie.pem"
            ])
        else:
            # Unix/Linux/Mac环境下的常见路径
            paths.extend([
                str(Path.home() / ".ssh" / "luojie.pem"),
                str(Path.home() / "luojie.pem"),
                "/etc/ssh/luojie.pem",
                "./luojie.pem",
                "../luojie.pem",
                str(Path.home() / "Documents" / "luojie.pem"),
                str(Path.home() / "Desktop" / "luojie.pem")
            ])
        
        return paths
    
    def find_pem_file_auto(self, filename="luojie.pem"):
        """自动查找PEM文件"""
        print(f"🔍 正在搜索PEM文件: {filename}")
        
        # 先检查默认路径
        for path in self.default_pem_paths:
            if filename not in path:
                # 如果路径中没有指定文件名，添加文件名
                test_path = str(Path(path).parent / filename)
            else:
                test_path = path
            
            if os.path.exists(test_path):
                print(f"✅ 找到PEM文件: {test_path}")
                return test_path
        
        # 如果没找到，进行更广泛的搜索
        search_dirs = self._get_search_directories()
        
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue
                
            try:
                for root, dirs, files in os.walk(search_dir):
                    for file in files:
                        if file == filename or file.endswith('.pem'):
                            file_path = os.path.join(root, file)
                            if self._is_valid_pem_file(file_path):
                                print(f"✅ 找到PEM文件: {file_path}")
                                return file_path
            except Exception as e:
                continue
        
        print(f"❌ 未找到PEM文件: {filename}")
        return None
    
    def _get_search_directories(self):
        """获取搜索目录列表"""
        search_dirs = []
        
        if self.system == "Windows":
            search_dirs.extend([
                str(Path.home()),
                str(Path.home() / "Documents"),
                str(Path.home() / "Desktop"),
                str(Path.home() / ".ssh"),
                r"E:\server_connect",
                r"C:\SSH",
                "."
            ])
        else:
            search_dirs.extend([
                str(Path.home()),
                str(Path.home() / ".ssh"),
                str(Path.home() / "Documents"),
                str(Path.home() / "Desktop"),
                "/etc/ssh",
                "."
            ])
        
        return search_dirs
    
    def _is_valid_pem_file(self, file_path):
        """检查是否是有效的PEM文件"""
        try:
            if not os.path.exists(file_path):
                return False
            
            # 检查文件大小（PEM文件一般不会太大也不会太小）
            file_size = os.path.getsize(file_path)
            if file_size < 100 or file_size > 10000:  # 100B到10KB之间
                return False
            
            # 检查文件内容
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 检查PEM格式标记
            pem_markers = [
                "-----BEGIN RSA PRIVATE KEY-----",
                "-----BEGIN PRIVATE KEY-----",
                "-----BEGIN OPENSSH PRIVATE KEY-----"
            ]
            
            return any(marker in content for marker in pem_markers)
            
        except Exception:
            return False
    
    def copy_pem_file(self, source_path, target_dir=None):
        """复制PEM文件到标准位置"""
        if not os.path.exists(source_path):
            print(f"❌ 源PEM文件不存在: {source_path}")
            return False
        
        if target_dir is None:
            if self.system == "Windows":
                target_dir = r"E:\server_connect"
            else:
                target_dir = str(Path.home() / ".ssh")
        
        # 创建目标目录
        os.makedirs(target_dir, exist_ok=True)
        
        # 生成目标文件路径
        filename = Path(source_path).name
        target_path = Path(target_dir) / filename
        
        try:
            # 复制文件
            shutil.copy2(source_path, target_path)
            
            # 设置权限
            if not self.fix_pem_permissions(str(target_path)):
                print(f"⚠️ PEM文件权限设置可能有问题")
            
            print(f"✅ PEM文件已复制到: {target_path}")
            return str(target_path)
            
        except Exception as e:
            print(f"❌ 复制PEM文件失败: {e}")
            return False
    
    def validate_and_prepare_pem(self, pem_path):
        """验证并准备PEM文件"""
        if not pem_path:
            print("🔍 开始自动查找PEM文件...")
            pem_path = self.find_pem_file_auto()
            if not pem_path:
                return None
        
        if not os.path.exists(pem_path):
            print(f"❌ PEM文件不存在: {pem_path}")
            return None
        
        # 验证PEM文件格式
        if not self.validate_pem_file(pem_path):
            print(f"❌ PEM文件格式无效: {pem_path}")
            return None
        
        # 检查和修复权限
        if not self.check_pem_permissions(pem_path):
            print("🔧 修复PEM文件权限...")
            if not self.fix_pem_permissions(pem_path):
                print("⚠️ PEM文件权限修复失败，但可能仍然可用")
        
        print(f"✅ PEM文件准备就绪: {pem_path}")
        return pem_path
    
    def check_pem_permissions(self, pem_file_path):
        """检查PEM文件权限"""
        if not os.path.exists(pem_file_path):
            print(f"❌ PEM文件不存在: {pem_file_path}")
            return False
        
        file_stat = os.stat(pem_file_path)
        file_mode = file_stat.st_mode
        
        # 在Windows上权限检查不同
        if self.system == "Windows":
            # Windows上主要检查文件是否可读
            if os.access(pem_file_path, os.R_OK):
                print(f"✅ Windows PEM文件可读: {pem_file_path}")
                return True
            else:
                print(f"❌ Windows PEM文件不可读: {pem_file_path}")
                return False
        else:
            # Unix/Linux系统权限检查
            # PEM文件应该是 600 (rw-------)
            expected_mode = stat.S_IRUSR | stat.S_IWUSR  # 0o600
            actual_mode = file_mode & 0o777
            
            if actual_mode == 0o600:
                print(f"✅ PEM文件权限正确: {pem_file_path} (600)")
                return True
            else:
                print(f"⚠️ PEM文件权限错误: {pem_file_path} ({oct(actual_mode)[2:]})")
                print("应该是 600 (rw-------)")
                return False
    
    def fix_pem_permissions(self, pem_file_path):
        """修复PEM文件权限"""
        if not os.path.exists(pem_file_path):
            print(f"❌ PEM文件不存在: {pem_file_path}")
            return False
        
        try:
            if self.system == "Windows":
                # Windows上确保文件可读
                print(f"🔧 Windows系统，检查文件访问权限...")
                if os.access(pem_file_path, os.R_OK):
                    print(f"✅ Windows PEM文件权限正常")
                    return True
                else:
                    print(f"❌ Windows PEM文件权限有问题，请手动检查")
                    return False
            else:
                # Unix/Linux系统设置权限为600
                os.chmod(pem_file_path, 0o600)
                print(f"✅ PEM文件权限已修复为 600: {pem_file_path}")
                return True
                
        except Exception as e:
            print(f"❌ 修复PEM文件权限失败: {e}")
            return False
    
    def validate_pem_file(self, pem_file_path):
        """验证PEM文件格式"""
        if not os.path.exists(pem_file_path):
            print(f"❌ PEM文件不存在: {pem_file_path}")
            return False
        
        try:
            with open(pem_file_path, 'r') as f:
                content = f.read()
            
            # 检查PEM格式标记
            required_headers = [
                "-----BEGIN RSA PRIVATE KEY-----",
                "-----BEGIN PRIVATE KEY-----",
                "-----BEGIN OPENSSH PRIVATE KEY-----"
            ]
            
            required_footers = [
                "-----END RSA PRIVATE KEY-----",
                "-----END PRIVATE KEY-----", 
                "-----END OPENSSH PRIVATE KEY-----"
            ]
            
            has_header = any(header in content for header in required_headers)
            has_footer = any(footer in content for footer in required_footers)
            
            if has_header and has_footer:
                print(f"✅ PEM文件格式验证通过: {pem_file_path}")
                return True
            else:
                print(f"❌ PEM文件格式错误: {pem_file_path}")
                print("文件应该包含 -----BEGIN ... PRIVATE KEY----- 和 -----END ... PRIVATE KEY-----")
                return False
                
        except Exception as e:
            print(f"❌ PEM文件验证失败: {e}")
            return False
    
    def backup_pem_file(self, pem_file_path, backup_dir="./backups/keys"):
        """备份PEM文件"""
        if not os.path.exists(pem_file_path):
            print(f"❌ PEM文件不存在: {pem_file_path}")
            return False
        
        try:
            # 创建备份目录
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # 生成备份文件名
            pem_name = Path(pem_file_path).name
            backup_file = backup_path / f"{pem_name}.backup"
            
            # 复制文件
            import shutil
            shutil.copy2(pem_file_path, backup_file)
            
            # 设置备份文件权限
            if self.system != "Windows":
                os.chmod(backup_file, 0o600)
            
            print(f"✅ PEM文件备份成功: {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            print(f"❌ PEM文件备份失败: {e}")
            return False
    
    def find_pem_files(self, search_dirs=None):
        """查找系统中的PEM文件"""
        if search_dirs is None:
            if self.system == "Windows":
                search_dirs = [
                    r"E:\server_connect",
                    str(Path.home() / ".ssh"),
                    str(Path.home() / "Documents"),
                    "."
                ]
            else:
                search_dirs = [
                    str(Path.home() / ".ssh"),
                    "/etc/ssh",
                    "."
                ]
        
        found_pems = []
        
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue
                
            try:
                for root, dirs, files in os.walk(search_dir):
                    for file in files:
                        if file.endswith(('.pem', '.key')) or 'id_rsa' in file:
                            file_path = os.path.join(root, file)
                            
                            # 简单验证是否是私钥文件
                            try:
                                with open(file_path, 'r') as f:
                                    content = f.read()
                                    if "PRIVATE KEY" in content:
                                        found_pems.append(file_path)
                            except:
                                continue
                                
            except Exception as e:
                print(f"⚠️ 搜索目录 {search_dir} 时出错: {e}")
                continue
        
        if found_pems:
            print(f"🔍 找到 {len(found_pems)} 个PEM文件:")
            for pem in found_pems:
                print(f"   📄 {pem}")
        else:
            print("🔍 未找到PEM文件")
        
        return found_pems
    
    def get_pem_info(self, pem_file_path):
        """获取PEM文件信息"""
        if not os.path.exists(pem_file_path):
            return None
        
        try:
            file_stat = os.stat(pem_file_path)
            
            info = {
                'path': pem_file_path,
                'size': file_stat.st_size,
                'modified': file_stat.st_mtime,
                'permissions': oct(file_stat.st_mode)[-3:] if self.system != "Windows" else "N/A"
            }
            
            # 检查文件类型
            with open(pem_file_path, 'r') as f:
                content = f.read()
                
                if "RSA PRIVATE KEY" in content:
                    info['type'] = "RSA Private Key"
                elif "OPENSSH PRIVATE KEY" in content:
                    info['type'] = "OpenSSH Private Key"
                elif "PRIVATE KEY" in content:
                    info['type'] = "Private Key"
                else:
                    info['type'] = "Unknown"
            
            return info
            
        except Exception as e:
            print(f"❌ 获取PEM文件信息失败: {e}")
            return None
    
    def create_ssh_config(self, host, hostname, user, pem_file_path, port=22):
        """创建SSH配置文件条目"""
        ssh_dir = Path.home() / ".ssh"
        ssh_dir.mkdir(exist_ok=True)
        
        config_file = ssh_dir / "config"
        
        config_entry = f"""
# {host} server configuration
Host {host}
    HostName {hostname}
    User {user}
    Port {port}
    IdentityFile {pem_file_path}
    IdentitiesOnly yes
    StrictHostKeyChecking no
"""
        
        try:
            # 检查是否已存在配置
            if config_file.exists():
                with open(config_file, 'r') as f:
                    existing_content = f.read()
                
                if f"Host {host}" in existing_content:
                    print(f"⚠️ SSH配置中已存在 {host}")
                    return False
            
            # 添加配置
            with open(config_file, 'a') as f:
                f.write(config_entry)
            
            # 设置权限
            if self.system != "Windows":
                os.chmod(config_file, 0o644)
            
            print(f"✅ SSH配置已添加: {host}")
            print(f"现在可以使用: ssh {host}")
            return True
            
        except Exception as e:
            print(f"❌ 创建SSH配置失败: {e}")
            return False 