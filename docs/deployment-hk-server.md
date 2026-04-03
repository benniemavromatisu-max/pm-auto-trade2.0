# 香港服务器部署指南

## 概述

本文档说明如何将 PM Auto Trade 2.0 后端部署到香港服务器，以降低交易延迟。

## 架构

```
香港服务器 (Python 后端)
    │
    ├── WebSocket (端口 8766) → Chrome 扩展前端
    │
    └── HTTPS → Polymarket CLOB API (延迟 < 50ms)
```

## 部署步骤

### 1. 服务器准备

```bash
# 更新系统
apt update && apt upgrade -y

# 安装 Python 3.11+ 和必要工具
apt install -y python3.11 python3.11-venv python3-pip git screen ufw

# 创建代码目录
mkdir -p /opt/pm-auto-trade
cd /opt/pm-auto-trade
```

### 2. 克隆代码

```bash
# 如果已有 Git 仓库
git clone <your-repo-url> .

# 或手动上传代码（使用 scp 或 rsync）
scp -r ./pm-auto-trade2.0 ubuntu@your-server:/opt/pm-auto-trade/
```

### 3. 安装依赖

```bash
cd /opt/pm-auto-trade

# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 验证安装
python -c "import httpx, websockets; print('Dependencies OK')"
```

### 4. 配置环境变量

```bash
# 创建 .env 文件
cat > .env << 'EOF'
POLY_PRIVATE_KEY=your_private_key_here
POLY_FUNDER_ADDRESS=your_funder_address_here
EOF

# 设置文件权限（仅自己可读）
chmod 600 .env
```

### 5. 创建 systemd 服务

```bash
cat > /etc/systemd/system/pm-autotrade.service << 'EOF'
[Unit]
Description=PM Auto Trade 2.0
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/pm-auto-trade
EnvironmentFile=/opt/pm-auto-trade/.env
ExecStart=/opt/pm-auto-trade/venv/bin/python -m server.main
Restart=always
RestartSec=5
StandardOutput=append:/opt/pm-auto-trade/data/logs/server.log
StandardError=append:/opt/pm-auto-trade/data/logs/server.log

[Install]
WantedBy=multi-user.target
EOF
```

### 6. 创建日志目录

```bash
mkdir -p /opt/pm-auto-trade/data/logs
mkdir -p /opt/pm-auto-trade/data/trades
chown -R ubuntu:ubuntu /opt/pm-auto-trade
```

### 7. 启动服务

```bash
# 重新加载 systemd
systemctl daemon-reload

# 启用服务（开机自启）
systemctl enable pm-autotrade

# 启动服务
systemctl start pm-autotrade

# 查看状态
systemctl status pm-autotrade
```

### 8. 配置防火墙

```bash
# 开放端口（仅开放 WebSocket 端口）
ufw allow 22/tcp    # SSH
ufw allow 8766/tcp  # WebSocket

# 启用防火墙
ufw enable

# 查看规则
ufw status
```

### 9. 验证部署

```bash
# 查看日志
tail -f /opt/pm-auto-trade/data/logs/server.log

# 查看进程是否运行
ps aux | grep server.main

# 测试端口
curl -I http://localhost:8766  # WebSocket 不支持 HTTP，但可确认端口开放
```

## 前端配置

### 修改 Chrome 扩展连接地址

文件：`extension/sidepanel/app.js`

找到以下行并修改：
```javascript
// 第 43 行和第 98 行
this.ws = new WebSocket('ws://你的香港服务器IP:8766');
```

### 加载修改后的扩展

1. 打开 Chrome → `chrome://extensions/`
2. 关闭「开发者模式」
3. 重新加载插件 或 点击「更新」

## 常用命令

```bash
# 查看状态
systemctl status pm-autotrade

# 查看日志
journalctl -u pm-autotrade -f

# 重启服务
systemctl restart pm-autotrade

# 停止服务
systemctl stop pm-autotrade

# 禁用开机自启
systemctl disable pm-autotrade
```

## 香港服务器推荐

| 厂商 | 类型 | 推荐配置 |
|------|------|----------|
| 腾讯云 | CN2 GIA | 轻量应用服务器 2C4G |
| 阿里云 | 国际版 | ECS 2C2G |
| 华为云 | 香港 | 2C4G |
| RackNerd | 性价比 | 1C2G $10/月 |

## 注意事项

1. **安全**：务必使用防火墙，只开放必要端口
2. **备份**：定期备份 `.env` 文件和配置
3. **监控**：建议配置监控告警
4. **网络**：建议选择 CN2 GIA 线路到 Polymarket延迟更低

## 问题排查

```bash
# 服务启动失败
journalctl -u pm-autotrade -n 50

# 端口被占用
lsof -i :8766

# Python 模块缺失
source venv/bin/activate
pip install -r requirements.txt
```
