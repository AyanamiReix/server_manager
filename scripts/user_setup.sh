#!/bin/bash
# 用户创建和配置脚本
# 创建luojie和heyi两个平等的管理员用户

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}👥 创建和配置用户系统${NC}"
echo "================================="

# 获取要创建的用户名（从参数获取，默认为luojie和heyi）
if [ $# -gt 0 ]; then
    USERS=("$@")
else
    USERS=("luojie" "heyi")
fi

echo -e "${YELLOW}将创建以下用户: ${USERS[*]}${NC}"

# 创建共享项目目录
SHARED_DIR="/home/shared"
PROJECTS_DIR="$SHARED_DIR/projects"
BACKUPS_DIR="$SHARED_DIR/backups"

echo -e "${BLUE}📁 创建共享目录...${NC}"
mkdir -p $SHARED_DIR
mkdir -p $PROJECTS_DIR
mkdir -p $BACKUPS_DIR

# 为每个用户进行配置
for username in "${USERS[@]}"; do
    echo -e "${BLUE}👤 配置用户: $username${NC}"
    
    # 检查用户是否已存在
    if id "$username" &>/dev/null; then
        echo -e "${YELLOW}⚠️ 用户 $username 已存在，跳过创建${NC}"
    else
        echo -e "${GREEN}📝 创建用户: $username${NC}"
        
        # 创建用户并设置密码
        useradd -m -s /bin/bash "$username"
        
        # 设置临时密码（建议首次登录后修改）
        echo "$username:${username}123!" | chpasswd
        
        # 强制用户下次登录时修改密码
        passwd -e "$username"
        
        echo -e "${GREEN}✅ 用户 $username 创建成功${NC}"
        echo -e "${YELLOW}💡 临时密码: ${username}123! (首次登录需修改)${NC}"
    fi
    
    # 添加到sudo组（管理员权限）
    echo -e "${BLUE}🔧 添加管理员权限...${NC}"
    usermod -aG sudo "$username"
    
    # 添加到docker组（如果docker已安装）
    if command -v docker &> /dev/null; then
        usermod -aG docker "$username"
        echo -e "${GREEN}✅ 已添加到docker组${NC}"
    fi
    
    # 创建用户的SSH目录
    USER_HOME="/home/$username"
    SSH_DIR="$USER_HOME/.ssh"
    
    if [ ! -d "$SSH_DIR" ]; then
        mkdir -p "$SSH_DIR"
        chmod 700 "$SSH_DIR"
        chown "$username:$username" "$SSH_DIR"
        echo -e "${GREEN}✅ SSH目录创建完成${NC}"
    fi
    
    # 创建authorized_keys文件
    AUTH_KEYS="$SSH_DIR/authorized_keys"
    if [ ! -f "$AUTH_KEYS" ]; then
        touch "$AUTH_KEYS"
        chmod 600 "$AUTH_KEYS"
        chown "$username:$username" "$AUTH_KEYS"
        echo -e "${GREEN}✅ authorized_keys文件创建完成${NC}"
    fi
    
    # 配置用户的bashrc
    BASHRC="$USER_HOME/.bashrc"
    
    # 添加有用的别名和环境变量
    cat >> "$BASHRC" << 'EOF'

# CompressAI-Vision 项目环境变量
export PROJECTS_DIR="/home/shared/projects"
export SHARED_DIR="/home/shared"

# 有用的别名
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'

# 项目相关别名
alias projects='cd /home/shared/projects'
alias shared='cd /home/shared'
alias backups='cd /home/shared/backups'

# Docker别名
alias docker-ps='docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
alias docker-clean='docker container prune -f && docker image prune -f'

# Git别名
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git pull'
alias glog='git log --oneline --graph --decorate'

EOF

    chown "$username:$username" "$BASHRC"
    echo -e "${GREEN}✅ bashrc配置完成${NC}"
    
    echo -e "${GREEN}🎉 用户 $username 配置完成${NC}"
    echo "----------------------------------------"
done

# 设置共享目录权限
echo -e "${BLUE}🔧 配置共享目录权限...${NC}"

# 设置共享目录的基本权限
chown -R root:root $SHARED_DIR
chmod 755 $SHARED_DIR

# 设置项目目录权限（所有用户可读写）
chmod 775 $PROJECTS_DIR
chmod 775 $BACKUPS_DIR

# 为每个用户设置ACL权限（如果支持）
for username in "${USERS[@]}"; do
    if command -v setfacl &> /dev/null; then
        setfacl -R -m u:${username}:rwx $PROJECTS_DIR
        setfacl -R -m u:${username}:rwx $BACKUPS_DIR
        setfacl -d -m u:${username}:rwx $PROJECTS_DIR
        setfacl -d -m u:${username}:rwx $BACKUPS_DIR
        echo -e "${GREEN}✅ 用户 $username ACL权限设置完成${NC}"
    else
        # 如果不支持ACL，使用组权限
        groupadd -f shared_users
        usermod -aG shared_users "$username"
        chgrp -R shared_users $PROJECTS_DIR
        chgrp -R shared_users $BACKUPS_DIR
        echo -e "${GREEN}✅ 用户 $username 组权限设置完成${NC}"
    fi
done

# 创建欢迎信息
cat > /etc/motd << 'EOF'
🚀 CompressAI-Vision 研究服务器
================================

👥 用户: luojie, heyi
📁 项目目录: /home/shared/projects
💾 备份目录: /home/shared/backups

🔧 常用命令:
  projects     - 进入项目目录
  shared       - 进入共享目录
  docker-ps    - 查看Docker容器
  docker-clean - 清理Docker资源

📚 获取帮助:
  man <command>  - 查看命令手册
  --help         - 查看命令帮助

🎯 开始工作:
  cd /home/shared/projects
  
EOF

echo -e "${GREEN}🎉 用户系统配置完成！${NC}"
echo ""
echo -e "${BLUE}📋 配置摘要：${NC}"
echo "✅ 创建用户: ${USERS[*]}"
echo "✅ 管理员权限: 已授予"
echo "✅ Docker权限: 已授予"
echo "✅ 共享目录: $PROJECTS_DIR"
echo "✅ 备份目录: $BACKUPS_DIR"
echo ""
echo -e "${YELLOW}💡 下一步:${NC}"
echo "1. 用户首次登录需修改密码"
echo "2. 配置SSH密钥认证"
echo "3. 开始项目部署"
echo ""
echo -e "${GREEN}🎊 用户配置完成！${NC}" 