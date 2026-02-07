# 离线部署指南

当你的Debian服务器无法访问互联网时，可以使用离线tar包进行部署。

## 📦 获取离线镜像

### 方式一：从GitHub Release下载

1. 访问 [GitHub Releases](https://github.com/your-username/printer_server/releases)
2. 下载对应版本的离线包：
   - `print-service-arm64.tar` - ARM64架构镜像
   - `print-service-arm64.tar.sha256` - SHA256校验文件

### 方式二：从Actions Artifacts下载

1. 访问 [GitHub Actions](https://github.com/your-username/printer_server/actions)
2. 选择最近的构建流程
3. 下载 `print-service-arm64-offline` artifact

---

## 🚀 部署步骤

### 步骤 1: 传输文件到服务器

使用SCP或其他工具将文件传输到Debian服务器：

```bash
# 传输镜像文件
scp print-service-arm64.tar user@debian-server:/path/to/
scp print-service-arm64.tar.sha256 user@debian-server:/path/to/
```

### 步骤 2: 验证文件完整性

```bash
# 进入传输目录
cd /path/to/

# 校验SHA256
sha256sum -c print-service-arm64.tar.sha256

# 预期输出:
# print-service-arm64.tar: OK
```

### 步骤 3: 加载Docker镜像

```bash
# 加载镜像
docker load < print-service-arm64.tar

# 查看加载的镜像
docker images | grep print-service
```

### 步骤 4: 运行容器

```bash
# 创建数据目录
mkdir -p /opt/print-service/uploads
mkdir -p /opt/print-service/logs

# 运行容器
docker run -d \
  --name remote-print \
  --restart=unless-stopped \
  -p 5000:5000 \
  -p 631:631 \
  -v /opt/print-service/uploads:/app/uploads \
  -v /opt/print-service/logs:/app/logs \
  -e TZ=Asia/Shanghai \
  print-service:latest
```

### 步骤 5: 验证服务

```bash
# 检查容器状态
docker ps | grep remote-print

# 检查健康状态
curl http://localhost:5000/api/health

# 查看日志
docker logs remote-print
```

---

## 🔧 高级配置

### 使用自定义网络

```bash
# 创建专用网络
docker network create print-network

# 运行容器并连接到网络
docker run -d \
  --name remote-print \
  --network print-network \
  -p 5000:5000 \
  -p 631:631 \
  -v /opt/print-service/uploads:/app/uploads \
  print-service:latest
```

### 使用docker-compose

创建 `docker-compose-offline.yml`：

```yaml
version: '3.8'

services:
  print-service:
    image: print-service:latest
    container_name: remote-print
    restart: unless-stopped
    ports:
      - "5000:5000"
      - "631:631"
    environment:
      - TZ=Asia/Shanghai
      - CUPS_PRINTER_NAME=HP_DeskJet_4900
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    devices:
      - /dev/bus/usb:/dev/bus/usb
    privileged: true

volumes:
  uploads:
  logs:
```

启动：

```bash
docker-compose -f docker-compose-offline.yml up -d
```

### 配置打印机

如果打印机需要特殊配置：

```bash
# 进入容器
docker exec -it remote-print bash

# 在容器内配置CUPS
# 访问CUPS管理界面或使用命令行
```

---

## 📋 常用命令

### 查看容器状态

```bash
# 查看运行状态
docker ps

# 查看容器资源使用
docker stats remote-print

# 查看容器日志
docker logs -f remote-print
```

### 停止和启动

```bash
# 停止容器
docker stop remote-print

# 启动容器
docker start remote-print

# 重启容器
docker restart remote-print
```

### 更新服务

```bash
# 停止并删除旧容器
docker stop remote-print
docker rm remote-print

# 加载新镜像
docker load < print-service-new.tar

# 使用新镜像运行
docker run -d ... print-service:latest
```

### 清理

```bash
# 删除旧镜像
docker rmi print-service:old-tag

# 清理未使用的资源
docker system prune -a
```

---

## 🔍 故障排除

### 问题1: 镜像加载失败

**错误**: `Error processing tar file: unexpected EOF`

**解决**:
1. 确认文件传输完整
2. 重新校验SHA256
3. 重新下载文件

### 问题2: 容器无法启动

**错误**: `docker: Error response from daemon: driver failed programming external connectivity`

**解决**:
```bash
# 停止Docker服务
sudo systemctl stop docker

# 启动Docker服务
sudo systemctl start docker

# 重新运行容器
docker run ...
```

### 问题3: 打印机无法访问

**错误**: `Unable to connect to CUPS server`

**解决**:
1. 检查USB连接
2. 配置设备权限
3. 在CUPS中添加打印机

```bash
# 检查USB设备
lsusb | grep HP

# 配置udev规则
sudo nano /etc/udev/rules.d/99-usb-printer.rules

# 添加规则（替换为实际VendorID和ProductID）
# SUBSYSTEM=="usb", ATTR{idVendor}=="03f0", ATTR{idProduct}=="7d04", MODE="0666"

# 重新加载规则
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### 问题4: 端口被占用

**错误**: `Bind for 0.0.0.0:5000 failed: port is already allocated`

**解决**:
```bash
# 查找占用端口的进程
sudo lsof -i :5000

# 或使用其他端口
docker run -p 5001:5000 ...
```

---

## 📊 文件结构

部署后的目录结构：

```
/opt/print-service/
├── uploads/          # 上传文件存储
│   ├── *.pdf
│   └── previews/     # 预览图片
├── logs/             # 应用日志
│   └── app.log
└── docker-compose.yml # Compose配置（可选）
```

---

## 📞 获取帮助

如果遇到问题：

1. 查看Docker日志：`docker logs remote-print`
2. 检查系统日志：`journalctl -xe`
3. 查看CUPS状态：`sudo systemctl status cups`
4. 提交 [GitHub Issue](https://github.com/your-username/printer_server/issues)
