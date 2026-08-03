# etfirst 网络问题诊断与修复指南

> **版本**: v1.0 | **更新**: 2026-08-03
> **适用**: 沙箱/代理环境下 etfirst CLI 连接失败时

---

## 一、问题症状

运行 etfirst 时出现：

```
✗ Cannot reach etfapp backend at https://etfapp.euler.southernfund.com:13000
  Caused by SSLError(SSLEOFError(8, '[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol'))
```

或

```
Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='172.16.10.254', port=7897): Failed to establish a new connection: [Errno 111] Connection refused"))
```

## 二、根因

沙箱环境的**代理服务失效**。系统设置了 `HTTPS_PROXY=http://172.16.10.254:7897`，但该代理端口已关闭。所有走代理的请求（包括 etfirst、WebSearch、WebFetch）都会失败。

**关键事实**: 绕过代理后，网络本身完全正常（DNS、网关、直连外网均可用）。

## 三、诊断步骤

```bash
# 1. 检查代理环境变量
env | grep -i proxy

# 2. 测试代理端口是否可用
timeout 3 bash -c 'cat < /dev/null > /dev/tcp/172.16.10.254/7897' && echo "代理可用" || echo "代理不可用"

# 3. 测试绕过代理直连外网
curl -s -o /dev/null -w "直连HTTP: %{http_code}\n" --noproxy '*' --connect-timeout 5 https://www.baidu.com

# 4. 测试绕过代理连 etfirst
curl -sk -o /dev/null -w "etfirst HTTP: %{http_code}\n" --noproxy '*' --connect-timeout 8 \
  -H "User-Agent: Mozilla/5.0" \
  https://etfapp.euler.southernfund.com:13000/etfapp/retail/auth/cli-login
```

**判定**:
- 代理端口不可连 + 直连外网 200 → 代理失效，需绕过
- etfirst 返回 403 → 需要带 User-Agent（缺 UA 时后端拒绝）
- etfirst 返回 200 且 `{"code":"A0100"}` → HTTP 层已通（参数错误是正常响应）

## 四、修复方案（绕过代理运行 etfirst）

### 方案 A：单次命令清空代理

```bash
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY \
  etfirst auth login --api-key "YOUR_KEY"

env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY \
  etfirst --json otc-detail all --product-code 024418 --date-range 250
```

### 方案 B：定义别名（推荐）

```bash
alias etfirst='env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY etfirst'
```

### 方案 C：永久移除代理配置（仅沙箱）

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
```

## 五、验证

```bash
# 登录
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY \
  etfirst auth login --api-key "YOUR_KEY"

# 测试数据
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY \
  etfirst --json index-base list-etf --type 2 --page-size 3

# 应返回 {"code":"00000","message":"success"}
```

## 六、注意事项

1. **代理可能自动恢复**：如果代理服务重启，`etfirst` 又能走代理了。两者都可时优先走代理（更稳定）。
2. **不要同时开代理和绕过**：混用会导致连接不稳定。
3. **User-Agent 关键**：etfirst 后端对无 UA 的请求返回 403，Python requests 默认会带 UA，所以 etfirst 本身无此问题；但用 curl 测试时需手动加 `-H "User-Agent: Mozilla/5.0"`。
4. **TLS 间歇故障**：即使网络正常，etfirst 后端偶尔出现 `SSLEOFError`（服务端 TLS 抖动），重试 2-3 次即可恢复。

## 七、快速一键脚本

保存为 `scripts/etfirst_fix.sh`:

```bash
#!/bin/bash
# etfirst 网络修复 + 调用封装
# 用法: ./etfirst_fix.sh <etfirst参数...>

# 检测代理是否可用
if timeout 3 bash -c 'cat < /dev/null > /dev/tcp/172.16.10.254/7897' 2>/dev/null; then
    # 代理可用，正常调用
    etfirst "$@"
else
    # 代理不可用，绕过
    env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY etfirst "$@"
fi
```

```bash
chmod +x scripts/etfirst_fix.sh
./etfirst_fix.sh --json otc-detail all --product-code 024418 --date-range 250
```
