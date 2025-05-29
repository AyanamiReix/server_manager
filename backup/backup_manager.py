#!/usr/bin/env python3
"""
备份管理器
支持项目的智能备份和恢复
"""

import os
import json
import time
import shutil
from pathlib import Path
from datetime import datetime

class BackupManager:
    def __init__(self, backup_dir="./backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置文件
        self.config_file = self.backup_dir / "backup_config.json"
        self.load_config()
    
    def load_config(self):
        """加载备份配置"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "exclude_patterns": [
                    "*.log", "*.tmp", "__pycache__/", ".git/",
                    "node_modules/", ".vscode/", ".idea/",
                    "*.pyc", "*.pyo", ".DS_Store"
                ],
                "max_backups": 10,
                "compress": True,
                "backup_types": {
                    "full": "完整备份 - 包含所有文件",
                    "code": "代码备份 - 只包含源代码",
                    "quick": "快速备份 - 关键文件",
                    "custom": "自定义备份 - 用户选择"
                }
            }
            self.save_config()
    
    def save_config(self):
        """保存备份配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def backup_project(self, project_name, ssh_manager, backup_type="code"):
        """备份指定项目"""
        print(f"💾 开始备份项目: {project_name}")
        print(f"📦 备份类型: {backup_type}")
        
        # 生成备份名称
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{project_name}_{backup_type}_{timestamp}"
        
        # 创建备份目录
        project_backup_dir = self.backup_dir / project_name
        project_backup_dir.mkdir(exist_ok=True)
        
        backup_file = project_backup_dir / f"{backup_name}.tar.gz"
        
        # 获取项目路径
        remote_project_path = f"/home/shared/projects/{project_name}"
        
        # 检查项目是否存在
        if not ssh_manager.file_exists(remote_project_path):
            print(f"❌ 项目不存在: {remote_project_path}")
            return False
        
        # 根据备份类型创建排除规则
        exclude_rules = self._get_exclude_rules(backup_type)
        
        # 创建备份命令
        exclude_options = " ".join([f"--exclude='{pattern}'" for pattern in exclude_rules])
        backup_cmd = f"cd /home/shared/projects && tar -czf /tmp/{backup_name}.tar.gz {exclude_options} {project_name}"
        
        print(f"🔧 执行备份命令...")
        stdout, stderr, exit_status = ssh_manager.execute_command(backup_cmd, timeout=1800)  # 30分钟超时
        
        if exit_status != 0:
            print(f"❌ 备份创建失败: {stderr}")
            return False
        
        # 下载备份文件
        print(f"📥 下载备份文件...")
        remote_backup_path = f"/tmp/{backup_name}.tar.gz"
        
        if not ssh_manager.download_file(remote_backup_path, str(backup_file)):
            print(f"❌ 备份文件下载失败")
            return False
        
        # 清理远程临时文件
        ssh_manager.execute_command(f"rm -f {remote_backup_path}")
        
        # 创建备份信息文件
        backup_info = {
            "project_name": project_name,
            "backup_type": backup_type,
            "timestamp": timestamp,
            "backup_file": str(backup_file),
            "size": os.path.getsize(backup_file),
            "created_at": datetime.now().isoformat(),
            "exclude_rules": exclude_rules
        }
        
        info_file = project_backup_dir / f"{backup_name}.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, indent=2, ensure_ascii=False)
        
        # 清理旧备份
        self._cleanup_old_backups(project_name)
        
        print(f"✅ 项目备份完成: {backup_file}")
        print(f"📊 备份大小: {self._format_size(backup_info['size'])}")
        
        return True
    
    def _get_exclude_rules(self, backup_type):
        """根据备份类型获取排除规则"""
        base_excludes = self.config["exclude_patterns"].copy()
        
        if backup_type == "code":
            # 代码备份：排除数据、模型、结果文件
            base_excludes.extend([
                "datasets/*", "data/*", "*.dataset",
                "models/*.pth", "models/*.pt", "models/*.ckpt", "*.model",
                "results/*/logs/*", "results/*/checkpoints/*",
                "logs/*", "checkpoints/*", "wandb/*",
                "*.tar.gz", "*.zip", "*.7z"
            ])
        elif backup_type == "quick":
            # 快速备份：只保留关键代码和配置
            base_excludes.extend([
                "datasets/*", "data/*", "models/*", "results/*",
                "logs/*", "checkpoints/*", "wandb/*",
                "*.tar.gz", "*.zip", "*.7z", "*.jpg", "*.png", "*.mp4"
            ])
        elif backup_type == "full":
            # 完整备份：只排除临时文件
            pass  # 使用基础排除规则
        
        return base_excludes
    
    def list_backups(self, project_name=None):
        """列出备份"""
        backups = []
        
        if project_name:
            # 列出指定项目的备份
            project_backup_dir = self.backup_dir / project_name
            if project_backup_dir.exists():
                backups.extend(self._scan_project_backups(project_name, project_backup_dir))
        else:
            # 列出所有项目的备份
            for project_dir in self.backup_dir.iterdir():
                if project_dir.is_dir() and project_dir.name != "." and not project_dir.name.startswith('.'):
                    project_name = project_dir.name
                    backups.extend(self._scan_project_backups(project_name, project_dir))
        
        # 按时间排序
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        if backups:
            print("📁 可用的备份:")
            print("=" * 80)
            for backup in backups:
                print(f"📦 {backup['project_name']} - {backup['backup_type']}")
                print(f"   📅 时间: {backup['timestamp']}")
                print(f"   📊 大小: {self._format_size(backup['size'])}")
                print(f"   📄 文件: {backup['backup_file']}")
                print("-" * 80)
        else:
            print("📭 没有找到备份文件")
        
        return backups
    
    def _scan_project_backups(self, project_name, project_dir):
        """扫描项目备份"""
        backups = []
        
        for info_file in project_dir.glob("*.json"):
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    backup_info = json.load(f)
                
                # 检查备份文件是否存在
                backup_file = Path(backup_info['backup_file'])
                if backup_file.exists():
                    backup_info['size'] = os.path.getsize(backup_file)
                    backups.append(backup_info)
                else:
                    print(f"⚠️ 备份文件缺失: {backup_file}")
                    
            except Exception as e:
                print(f"⚠️ 读取备份信息失败: {info_file}, {e}")
        
        return backups
    
    def restore_backup(self, backup_file, ssh_manager, restore_path=None):
        """恢复备份"""
        backup_file = Path(backup_file)
        if not backup_file.exists():
            print(f"❌ 备份文件不存在: {backup_file}")
            return False
        
        # 获取备份信息
        info_file = backup_file.with_suffix('.json')
        if info_file.exists():
            with open(info_file, 'r', encoding='utf-8') as f:
                backup_info = json.load(f)
            project_name = backup_info['project_name']
        else:
            # 从文件名推断项目名
            parts = backup_file.stem.split('_')
            project_name = parts[0] if parts else "unknown"
        
        if restore_path is None:
            restore_path = f"/home/shared/projects/{project_name}"
        
        print(f"🔄 恢复备份: {backup_file.name}")
        print(f"📂 目标路径: {restore_path}")
        
        # 上传备份文件
        remote_backup_path = f"/tmp/restore_{int(time.time())}.tar.gz"
        
        print(f"📤 上传备份文件...")
        if not ssh_manager.upload_file(str(backup_file), remote_backup_path):
            print(f"❌ 备份文件上传失败")
            return False
        
        # 创建恢复目录
        restore_parent = str(Path(restore_path).parent)
        ssh_manager.create_directory(restore_parent)
        
        # 解压备份
        print(f"📦 解压备份文件...")
        extract_cmd = f"cd {restore_parent} && tar -xzf {remote_backup_path}"
        stdout, stderr, exit_status = ssh_manager.execute_command(extract_cmd)
        
        if exit_status != 0:
            print(f"❌ 备份解压失败: {stderr}")
            ssh_manager.execute_command(f"rm -f {remote_backup_path}")
            return False
        
        # 清理临时文件
        ssh_manager.execute_command(f"rm -f {remote_backup_path}")
        
        print(f"✅ 备份恢复完成: {restore_path}")
        return True
    
    def _cleanup_old_backups(self, project_name):
        """清理旧备份"""
        project_backup_dir = self.backup_dir / project_name
        if not project_backup_dir.exists():
            return
        
        # 获取所有备份
        backups = self._scan_project_backups(project_name, project_backup_dir)
        
        # 如果备份数量超过限制，删除最旧的
        max_backups = self.config.get("max_backups", 10)
        if len(backups) > max_backups:
            # 按时间排序，保留最新的
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
            for backup in backups[max_backups:]:
                try:
                    backup_file = Path(backup['backup_file'])
                    info_file = backup_file.with_suffix('.json')
                    
                    if backup_file.exists():
                        backup_file.unlink()
                    if info_file.exists():
                        info_file.unlink()
                    
                    print(f"🗑️ 清理旧备份: {backup_file.name}")
                    
                except Exception as e:
                    print(f"⚠️ 清理备份失败: {e}")
    
    def get_backup_statistics(self):
        """获取备份统计信息"""
        stats = {
            "total_backups": 0,
            "total_size": 0,
            "projects": {},
            "backup_types": {}
        }
        
        for project_dir in self.backup_dir.iterdir():
            if project_dir.is_dir() and not project_dir.name.startswith('.'):
                project_name = project_dir.name
                project_backups = self._scan_project_backups(project_name, project_dir)
                
                project_stats = {
                    "count": len(project_backups),
                    "total_size": sum(b['size'] for b in project_backups),
                    "latest": max(project_backups, key=lambda x: x['created_at'])['created_at'] if project_backups else None
                }
                
                stats["projects"][project_name] = project_stats
                stats["total_backups"] += project_stats["count"]
                stats["total_size"] += project_stats["total_size"]
                
                # 统计备份类型
                for backup in project_backups:
                    backup_type = backup['backup_type']
                    if backup_type not in stats["backup_types"]:
                        stats["backup_types"][backup_type] = 0
                    stats["backup_types"][backup_type] += 1
        
        return stats
    
    def create_backup_schedule(self, project_name, schedule_type="daily", backup_type="code"):
        """创建备份计划"""
        schedule_file = self.backup_dir / "schedules.json"
        
        if schedule_file.exists():
            with open(schedule_file, 'r', encoding='utf-8') as f:
                schedules = json.load(f)
        else:
            schedules = {}
        
        schedules[project_name] = {
            "schedule_type": schedule_type,
            "backup_type": backup_type,
            "enabled": True,
            "last_backup": None,
            "created_at": datetime.now().isoformat()
        }
        
        with open(schedule_file, 'w', encoding='utf-8') as f:
            json.dump(schedules, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 备份计划已创建: {project_name} ({schedule_type})")
        return True
    
    def _format_size(self, size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def export_backup_info(self, output_file=None):
        """导出备份信息"""
        if output_file is None:
            output_file = self.backup_dir / f"backup_info_{datetime.now().strftime('%Y%m%d')}.json"
        
        stats = self.get_backup_statistics()
        backups = self.list_backups()
        
        export_data = {
            "export_date": datetime.now().isoformat(),
            "statistics": stats,
            "backups": backups,
            "config": self.config
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 备份信息已导出: {output_file}")
        return str(output_file) 