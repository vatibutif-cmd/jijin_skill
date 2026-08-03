#!/bin/bash
# etfirst 网络修复 + 调用封装
# 用法: ./etfirst_fix.sh <etfirst参数...>

# 检测代理是否可用
if timeout 3 bash -c 'cat < /dev/null > /dev/tcp/172.16.10.254/7897' 2>/dev/null; then
    echo "[fix] 代理可用，正常调用" >&2
    etfirst "$@"
else
    echo "[fix] 代理不可用，绕过代理调用" >&2
    env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY etfirst "$@"
fi
