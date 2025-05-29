#!/bin/bash
# Docker环境配置脚本
# 自动安装和配置Docker环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🐳 Docker环境配置脚本${NC}"
echo "============================="

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
    
    echo -e "${BLUE}🖥️ 检测到操作系统: $OS $VER${NC}"
}

# 检查Docker是否已安装
check_docker() {
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        echo -e "${GREEN}✅ Docker已安装: $DOCKER_VERSION${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️ Docker未安装${NC}"
        return 1
    fi
}

# 安装Docker
install_docker() {
    echo -e "${BLUE}📦 开始安装Docker...${NC}"
    
    case "$OS" in
        *"Ubuntu"*|*"Debian"*)
            install_docker_ubuntu_debian
            ;;
        *"CentOS"*|*"Red Hat"*|*"Amazon Linux"*)
            install_docker_centos_rhel
            ;;
        *)
            echo -e "${RED}❌ 不支持的操作系统: $OS${NC}"
            exit 1
            ;;
    esac
}

# Ubuntu/Debian安装Docker
install_docker_ubuntu_debian() {
    echo -e "${BLUE}📦 在Ubuntu/Debian上安装Docker...${NC}"
    
    # 更新包索引
    apt-get update
    
    # 安装必要的包
    apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # 添加Docker官方GPG密钥
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # 设置稳定版仓库
    if [[ "$OS" == *"Ubuntu"* ]]; then
        echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    else
        echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    fi
    
    # 更新包索引
    apt-get update
    
    # 安装Docker Engine
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    echo -e "${GREEN}✅ Docker安装完成${NC}"
}

# CentOS/RHEL安装Docker
install_docker_centos_rhel() {
    echo -e "${BLUE}📦 在CentOS/RHEL上安装Docker...${NC}"
    
    # 安装yum-utils
    yum install -y yum-utils
    
    # 添加Docker仓库
    yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    
    # 安装Docker Engine
    yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    echo -e "${GREEN}✅ Docker安装完成${NC}"
}

# 启动和配置Docker
configure_docker() {
    echo -e "${BLUE}🔧 配置Docker服务...${NC}"
    
    # 启动Docker服务
    systemctl start docker
    systemctl enable docker
    
    # 检查Docker状态
    if systemctl is-active --quiet docker; then
        echo -e "${GREEN}✅ Docker服务已启动${NC}"
    else
        echo -e "${RED}❌ Docker服务启动失败${NC}"
        exit 1
    fi
    
    # 测试Docker安装
    echo -e "${BLUE}🧪 测试Docker安装...${NC}"
    if docker run --rm hello-world &>/dev/null; then
        echo -e "${GREEN}✅ Docker安装测试通过${NC}"
    else
        echo -e "${RED}❌ Docker安装测试失败${NC}"
        exit 1
    fi
}

# 安装Docker Compose
install_docker_compose() {
    echo -e "${BLUE}📦 安装Docker Compose...${NC}"
    
    # 检查是否已有docker-compose-plugin
    if docker compose version &>/dev/null; then
        echo -e "${GREEN}✅ Docker Compose Plugin已安装${NC}"
        return 0
    fi
    
    # 下载并安装Docker Compose
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # 创建符号链接
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    echo -e "${GREEN}✅ Docker Compose安装完成${NC}"
}

# 配置Docker用户权限
configure_docker_users() {
    echo -e "${BLUE}👥 配置Docker用户权限...${NC}"
    
    # 创建docker组（如果不存在）
    if ! getent group docker > /dev/null 2>&1; then
        groupadd docker
        echo -e "${GREEN}✅ 创建docker组${NC}"
    fi
    
    # 添加现有用户到docker组
    for user in luojie heyi; do
        if id "$user" &>/dev/null; then
            usermod -aG docker "$user"
            echo -e "${GREEN}✅ 用户 $user 已添加到docker组${NC}"
        fi
    done
    
    echo -e "${YELLOW}💡 用户需要重新登录才能使用Docker命令${NC}"
}

# 优化Docker配置
optimize_docker() {
    echo -e "${BLUE}⚡ 优化Docker配置...${NC}"
    
    # 创建Docker配置目录
    mkdir -p /etc/docker
    
    # 创建Docker daemon配置文件
    cat > /etc/docker/daemon.json << 'EOF'
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "100m",
        "max-file": "3"
    },
    "storage-driver": "overlay2",
    "live-restore": true,
    "registry-mirrors": [
        "https://docker.mirrors.ustc.edu.cn",
        "https://hub-mirror.c.163.com"
    ]
}
EOF
    
    # 重启Docker服务以应用配置
    systemctl restart docker
    
    echo -e "${GREEN}✅ Docker配置优化完成${NC}"
}

# 安装NVIDIA Docker支持（如果有GPU）
install_nvidia_docker() {
    echo -e "${BLUE}🎮 检查GPU支持...${NC}"
    
    # 检查是否有NVIDIA GPU
    if command -v nvidia-smi &> /dev/null; then
        echo -e "${GREEN}🎮 检测到NVIDIA GPU${NC}"
        
        # 安装NVIDIA Docker运行时
        case "$OS" in
            *"Ubuntu"*|*"Debian"*)
                curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
                distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
                curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list
                apt-get update
                apt-get install -y nvidia-docker2
                ;;
            *"CentOS"*|*"Red Hat"*)
                distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
                curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.repo | tee /etc/yum.repos.d/nvidia-docker.repo
                yum install -y nvidia-docker2
                ;;
        esac
        
        # 重启Docker服务
        systemctl restart docker
        
        # 测试NVIDIA Docker
        if docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi &>/dev/null; then
            echo -e "${GREEN}✅ NVIDIA Docker配置成功${NC}"
        else
            echo -e "${YELLOW}⚠️ NVIDIA Docker测试失败，但可能是正常的${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ 未检测到NVIDIA GPU，跳过GPU支持配置${NC}"
    fi
}

# 清理和维护脚本
create_maintenance_scripts() {
    echo -e "${BLUE}🧹 创建维护脚本...${NC}"
    
    # 创建Docker清理脚本
    cat > /usr/local/bin/docker-cleanup.sh << 'EOF'
#!/bin/bash
# Docker清理脚本

echo "🧹 清理Docker资源..."

# 清理停止的容器
echo "清理停止的容器..."
docker container prune -f

# 清理未使用的镜像
echo "清理未使用的镜像..."
docker image prune -f

# 清理未使用的网络
echo "清理未使用的网络..."
docker network prune -f

# 清理未使用的卷
echo "清理未使用的卷..."
docker volume prune -f

# 显示清理结果
echo "✅ Docker清理完成"
docker system df

EOF
    
    chmod +x /usr/local/bin/docker-cleanup.sh
    
    # 创建Docker监控脚本
    cat > /usr/local/bin/docker-monitor.sh << 'EOF'
#!/bin/bash
# Docker监控脚本

echo "🖥️ Docker系统状态"
echo "=================="

echo "📊 系统资源使用:"
docker system df

echo ""
echo "🚀 运行中的容器:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Size}}"

echo ""
echo "🖼️ 镜像列表:"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

EOF
    
    chmod +x /usr/local/bin/docker-monitor.sh
    
    echo -e "${GREEN}✅ 维护脚本创建完成${NC}"
    echo -e "${YELLOW}💡 使用方式:${NC}"
    echo "   docker-cleanup.sh  - 清理Docker资源"
    echo "   docker-monitor.sh  - 监控Docker状态"
}

# 主执行流程
main() {
    echo -e "${BLUE}🚀 开始Docker环境配置...${NC}"
    
    # 检测操作系统
    detect_os
    
    # 检查Docker是否已安装
    if check_docker; then
        echo -e "${YELLOW}⚠️ Docker已安装，跳过安装步骤${NC}"
    else
        # 安装Docker
        install_docker
    fi
    
    # 配置Docker
    configure_docker
    
    # 安装Docker Compose
    install_docker_compose
    
    # 配置用户权限
    configure_docker_users
    
    # 优化Docker配置
    optimize_docker
    
    # 安装NVIDIA Docker支持
    install_nvidia_docker
    
    # 创建维护脚本
    create_maintenance_scripts
    
    echo -e "${GREEN}🎉 Docker环境配置完成！${NC}"
    echo ""
    echo -e "${BLUE}📋 配置摘要：${NC}"
    docker --version
    docker compose version 2>/dev/null || docker-compose --version
    
    echo ""
    echo -e "${YELLOW}💡 下一步:${NC}"
    echo "1. 用户重新登录以使用Docker命令"
    echo "2. 运行 docker-monitor.sh 检查状态"
    echo "3. 开始构建项目镜像"
    echo ""
    echo -e "${GREEN}🐳 Docker配置完成！${NC}"
}

# 执行主函数
main "$@" 