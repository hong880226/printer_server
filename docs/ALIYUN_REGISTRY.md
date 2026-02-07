# 阿里云容器镜像服务配置指南

本指南将帮助你配置阿里云容器镜像服务（ACR），用于存储和分发Docker镜像。

## 📋 目录

- [1. 创建阿里云容器镜像服务](#1-创建阿里云容器镜像服务)
- [2. 配置访问凭证](#2-配置访问凭证)
- [3. 配置GitHub Secrets](#3-配置-github-secrets)
- [4. 推送和拉取镜像](#4-推送和拉取镜像)
- [5. 常见问题](#5-常见问题)

---

## 1. 创建阿里云容器镜像服务

### 步骤 1: 登录阿里云控制台

1. 访问 [阿里云容器镜像服务](https://cr.console.aliyun.com)
2. 使用你的阿里云账号登录

### 步骤 2: 创建容器镜像服务实例

1. 点击「创建实例」或「创建企业版」
2. 填写配置信息：

| 配置项 | 推荐值 | 说明 |
|--------|--------|------|
| 地域 | 选择离你最近的区域 | 如 `华东1（杭州）` |
| 实例类型 | 企业版/个人版 | 企业版功能更全，个人版免费 |
| 实例名称 | `print-service-repo` | 自定义名称 |
| 地域 | `cn-hangzhou` | 区域代码 |

3. 点击「立即创建」

### 步骤 3: 创建命名空间

1. 在实例管理页面，点击「命名空间」
2. 点击「创建命名空间」
3. 填写信息：
   - 命名空间名称：如 `myspace`（小写字母+数字）
4. 点击「确定」

### 步骤 4: 创建镜像仓库

1. 点击「镜像仓库」
2. 点击「创建镜像仓库」
3. 填写信息：

| 配置项 | 值 |
|--------|-----|
| 仓库名称 | `remote-print-service` |
| 仓库类型 | 公开或私有 |
| 代码源 | 不使用代码源（手动构建） |

4. 点击「下一步」，然后「创建」

---

## 2. 配置访问凭证

### 获取登录凭证

#### 方式一：使用默认管理账号

1. 在实例管理页面，点击「访问凭证」
2. 点击「获取登录命令」
3. 记录以下信息：
   - Registry地址：如 `registry.cn-hangzhou.aliyuncs.com`
   - 用户名：如 `myspace@123456`
   - 固定密码或临时密码

#### 方式二：创建RAM子账号（推荐用于CI/CD）

1. 访问 [RAM控制台](https://ram.console.aliyun.com)
2. 点击「用户管理」-「创建用户」
3. 配置用户：
   - 用户名：`github-actions-reader`
   - 编程访问：启用
4. 点击「确定」，记录AccessKey ID和Secret
5. 返回RAM控制台，点击「授权策略管理」
6. 创建自定义授权策略：

```json
{
  "Version": "1",
  "Statement": [
    {
      "Action": [
        "cr:GetRepository",
        "cr:ListRepository",
        "cr:PullRepository",
        "cr:PushRepository",
        "cr:DeleteRepository",
        "cr:GetRepositoryTag",
        "cr:ListRepositoryTag",
        "cr:DeleteRepositoryTag",
        "cr:ModifyRepositoryTag",
        "cr:GetArtifact",
        "cr:ListArtifact",
        "cr:DeleteArtifact",
        "cr:PullArtifact",
        "cr:PushArtifact"
      ],
      "Resource": [
        "acs:cr:*:*:instance/*/repository/*",
        "acs:cr:*:*:instance/*/artifact/*"
      ],
      "Effect": "Allow"
    }
  ]
}
```

7. 将此策略授权给 `github-actions-reader` 用户

---

## 3. 配置 GitHub Secrets

在你的GitHub仓库中，依次进入：

**Settings → Secrets and variables → Actions**

添加以下Secrets：

| Secret Name | Value | 说明 |
|-------------|-------|------|
| `ALIYUN_REGISTRY_PASSWORD` | 容器镜像服务密码 | 从访问凭证获取 |
| `ALIYUN_REGISTRY_USERNAME` | 镜像仓库用户名 | 格式: `命名空间@云账号ID` |
| `ALIYUN_REPOSITORY_NAME` | 镜像仓库名称 | 如 `remote-print-service` |

### 获取云账号ID

1. 访问 [阿里云控制台](https://home.console.aliyun.com)
2. 点击右上角头像
3. 点击「安全设置」
4. 查看「账号ID」

---

## 4. 推送和拉取镜像

### 手动推送镜像

```bash
# 登录阿里云镜像仓库
docker login registry.cn-hangzhou.aliyuncs.com -u 命名空间@云账号ID -p 密码

# 重命名镜像
docker tag remote-print-service:latest registry.cn-hangzhou.aliyuncs.com/命名空间/remote-print-service:latest

# 推送镜像
docker push registry.cn-hangzhou.aliyuncs.com/命名空间/remote-print-service:latest
```

### 手动拉取镜像

```bash
# 登录阿里云镜像仓库
docker login registry.cn-hangzhou.aliyuncs.com -u 命名空间@云账号ID -p 密码

# 拉取镜像
docker pull registry.cn-hangzhou.aliyuncs.com/命名空间/remote-print-service:latest
```

### 在Debian服务器上使用

```bash
# 登录
docker login registry.cn-hangzhou.aliyuncs.com -u 命名空间@云账号ID -p 密码

# 拉取并运行
docker run -d \
  --name remote-print \
  -p 5000:5000 \
  -p 631:631 \
  -v /path/to/uploads:/app/uploads \
  registry.cn-hangzhou.aliyuncs.com/命名空间/remote-print-service:latest
```

---

## 5. 常见问题

### Q1: 推送失败，权限不足

**错误**: `denied: requested access to the resource is denied`

**解决**:
1. 检查用户名格式是否正确：`命名空间@云账号ID`
2. 确认密码是否正确（如果是临时密码，需要重新获取）
3. 确认命名空间和仓库名称是否匹配

### Q2: 镜像拉取失败，网络超时

**错误**: `Error response from daemon: Get https://registry.cn-hangzhou.aliyuncs.com/v2/...: dial tcp: lookup registry.cn-hangzhou.aliyuncs.com: no such host`

**解决**:
1. 检查网络连接
2. 确认域名拼写
3. 尝试使用IP直接访问（临时解决方案）

### Q3: GitHub Actions构建失败

**错误**: `error getting credentials - see https://github.com/docker/login-action#known-registries`

**解决**:
1. 确认所有Secrets已正确配置
2. 检查仓库名称是否符合规范（小写字母、数字、连字符）
3. 查看Actions日志获取详细错误信息

### Q4: 多架构镜像构建失败

**错误**: `failed to solve: failed to do request: Handshake i/o timeout`

**解决**:
1. 这是GitHub Actions构建多架构镜像时的常见网络问题
2. 可以改用单一ARM64架构构建
3. 或者使用国内构建节点（需要配置）

### Q5: 如何查看镜像版本

在阿里云容器镜像服务控制台：
1. 进入你的实例
2. 点击「镜像仓库」
3. 选择你的仓库
4. 查看「镜像版本」标签页

---

## 📚 相关链接

- [阿里云容器镜像服务文档](https://help.aliyun.com/document_detail/60799.html)
- [Docker Buildx文档](https://docs.docker.com/build/buildx/)
- [GitHub Actions文档](https://docs.github.com/en/actions)
