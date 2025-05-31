# user_logic.py

import paramiko

class UserLogic:
    """
    用户模式的业务逻辑层
    处理所有和服务器交互、数据处理等非UI逻辑
    """
    def __init__(self, ssh_manager):
        self.ssh = ssh_manager
        # 保存当前登录用户的信息
        self.current_user = None
        self.current_ip = None

    def check_user_and_key(self, ip, username, private_key_path=None):
        """
        用户模式下用用户名+私钥尝试SSH连接
        private_key_path: 用户上传的私钥路径（可选）
        """
        try:
            # 1. 如果提供了私钥路径，先验证私钥
            if private_key_path:
                valid, msg = self.validate_private_key(private_key_path)
                if not valid:
                    return 'key_invalid', msg
            
            # 2. 尝试直接连接（使用指定私钥或默认密钥）
            if self.ssh.connect(ip, username, private_key_path):
                self.current_user = username
                self.current_ip = ip
                return 'ok', '登录成功！'
            
            return 'auth_fail', '认证失败，请检查用户名和私钥是否匹配'
            
        except Exception as e:
            return 'error', f'连接出错: {str(e)}'

    def validate_private_key(self, key_path):
        """
        检查本地私钥文件是否有效
        支持RSA、DSA、ECDSA、Ed25519等多种类型
        """
        try:
            # 尝试多种类型的私钥
            key_types = [
                (paramiko.RSAKey, "RSA"),
                (paramiko.DSSKey, "DSA"),
                (paramiko.ECDSAKey, "ECDSA"),
                (paramiko.Ed25519Key, "Ed25519")
            ]
            
            for key_class, key_name in key_types:
                try:
                    key_class.from_private_key_file(key_path)
                    return True, f"{key_name}私钥有效"
                except Exception:
                    continue
                    
            return False, "不是有效的SSH私钥文件"
        except Exception as e:
            return False, f"检测出错: {str(e)}"

    def upload_user_pubkey(self, ip, username, pubkey_path):
        """
        上传用户的SSH公钥
        返回: (success, message)
        """
        try:
            # 1. 读取公钥文件
            with open(pubkey_path, 'r') as f:
                pubkey = f.read().strip()
                if not pubkey.startswith('ssh-'):
                    return False, "无效的SSH公钥格式"

            # 2. 用root连接服务器
            if not self.ssh.connect(ip, "root"):
                return False, "无法连接到服务器"

            # 3. 创建目录并设置权限
            cmds = [
                f"mkdir -p /home/{username}/.ssh",
                f"chmod 700 /home/{username}/.ssh",
                f"echo '{pubkey}' > /home/{username}/.ssh/authorized_keys",
                f"chmod 600 /home/{username}/.ssh/authorized_keys",
                f"chown -R {username}:{username} /home/{username}/.ssh"
            ]

            for cmd in cmds:
                _, stderr, exit_code = self.ssh.execute_command(cmd)
                if exit_code != 0:
                    return False, f"公钥上传失败: {stderr}"

            return True, "公钥上传成功！"

        except Exception as e:
            return False, f"公钥上传出错: {str(e)}"

    def get_user_info(self):
        """获取当前登录用户的信息"""
        if not self.current_user or not self.current_ip:
            return None
            
        try:
            # 获取用户详细信息
            info = {
                'username': self.current_user,
                'ip': self.current_ip,
                'home_dir': f'/home/{self.current_user}'
            }
            
            # 获取磁盘使用情况
            stdout, _, _ = self.ssh.execute_command(f"du -sh /home/{self.current_user}")
            if stdout:
                info['disk_usage'] = stdout.split()[0]
                
            # 获取所属组
            stdout, _, _ = self.ssh.execute_command(f"groups {self.current_user}")
            if stdout:
                info['groups'] = stdout.strip()
                
            # 获取最后登录时间
            stdout, _, _ = self.ssh.execute_command(f"lastlog -u {self.current_user}")
            if stdout:
                info['last_login'] = stdout.splitlines()[-1] if len(stdout.splitlines()) > 1 else "从未登录"
                
            return info
            
        except Exception:
            return None