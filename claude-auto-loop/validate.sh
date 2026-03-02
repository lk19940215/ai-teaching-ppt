#!/bin/bash
# ============================================================
# Session 校验脚本 (独立于 run.sh，两种模式共用)
#
# 用法:
#   CLI 模式:    run.sh 内部自动调用
#   Cursor 模式: 用户手动执行 bash claude-auto-loop/validate.sh
#   带 HEAD 参数: bash claude-auto-loop/validate.sh <head_before>
#
# 校验内容:
#   1. session_result.json 是否存在且合法
#   2. git 是否有新提交（需传入 head_before 参数）
#   3. 健康检查（从 project_profile.json 读取 URL）
#   4. 自定义钩子（validate.d/*.sh，可插拔扩展）
#
# 退出码:
#   0 = 全部通过
#   1 = session_result.json 校验失败（致命，需回滚）
#   2 = 非致命警告（git 无提交 / 健康检查未通过）
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SESSION_RESULT="$SCRIPT_DIR/session_result.json"
PROFILE="$SCRIPT_DIR/project_profile.json"

# ============ 颜色输出 ============
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[VALIDATE]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[PASS]${NC}     $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}     $1"; }
log_error() { echo -e "${RED}[FAIL]${NC}     $1"; }

# ============ 参数 ============
HEAD_BEFORE="${1:-}"

# 追踪整体结果
FATAL_FAILURE=false
HAS_WARNINGS=false

# ============================================================
# 校验 1: session_result.json
# ============================================================
validate_session_result() {
    log_info "校验 session_result.json ..."

    if [ ! -f "$SESSION_RESULT" ]; then
        log_error "Agent 未生成 session_result.json"
        FATAL_FAILURE=true
        return
    fi

    local validation
    validation=$(python3 -c "
import json, sys
try:
    with open('$SESSION_RESULT') as f:
        data = json.load(f)

    # 必须字段
    required = ['session_result', 'status_after']
    missing = [k for k in required if k not in data]
    if missing:
        print(f'INVALID:缺少字段 {missing}')
        sys.exit(0)

    # 可选字段警告
    if 'task_id' not in data:
        print('WARNING:缺少 task_id (建议包含)')

    result = data['session_result']
    if result not in ('success', 'failed'):
        print(f'INVALID:session_result 必须是 success 或 failed，实际是 {result}')
        sys.exit(0)

    status = data['status_after']
    valid_statuses = ('pending', 'in_progress', 'testing', 'done', 'failed')
    if status not in valid_statuses:
        print(f'INVALID:status_after 不合法: {status}')
        sys.exit(0)

    print(f'VALID:{result}')
except json.JSONDecodeError:
    print('INVALID:JSON 格式错误')
except Exception as e:
    print(f'INVALID:{e}')
" 2>/dev/null)

    if [[ "$validation" == VALID:* ]]; then
        local result="${validation#VALID:}"
        if [ "$result" = "success" ]; then
            log_ok "session_result.json 合法 (success)"
        else
            log_warn "session_result.json 合法，但 Agent 报告失败 (failed)"
            # Agent 自己说失败也算"正常产出"，不需要回滚
        fi
    elif [[ "$validation" == WARNING:* ]]; then
        local warn_msg="${validation#WARNING:}"
        log_warn "session_result.json 警告: $warn_msg"
        HAS_WARNINGS=true
    else
        local reason="${validation#INVALID:}"
        log_error "session_result.json 校验失败: $reason"
        FATAL_FAILURE=true
    fi
}

# ============================================================
# 校验 2: git 提交检查
# ============================================================
check_git_progress() {
    if [ -z "$HEAD_BEFORE" ]; then
        log_info "未提供 head_before 参数，跳过 git 检查"
        return
    fi

    log_info "校验 git 提交 ..."

    cd "$PROJECT_ROOT"
    local head_after
    head_after=$(git rev-parse HEAD 2>/dev/null || echo "none")

    if [ "$HEAD_BEFORE" = "$head_after" ]; then
        log_warn "本次会话没有新的 git 提交"
        HAS_WARNINGS=true
    else
        local commit_msg
        commit_msg=$(git log --oneline -1)
        log_ok "检测到新提交: $commit_msg"
    fi
}

# ============================================================
# 校验 3: 健康检查 (从 project_profile.json 读取 URL)
# ============================================================
run_health_checks() {
    log_info "健康检查 ..."

    # 如果 project_profile.json 不存在，跳过
    if [ ! -f "$PROFILE" ]; then
        log_info "project_profile.json 不存在，跳过健康检查"
        return
    fi

    # 从 profile 中提取 health_check URLs
    local urls
    urls=$(python3 -c "
import json
try:
    with open('$PROFILE') as f:
        data = json.load(f)
    services = data.get('services', [])
    for svc in services:
        url = svc.get('health_check', '')
        name = svc.get('name', 'unknown')
        if url:
            print(f'{name}|{url}')
except Exception:
    pass
" 2>/dev/null)

    if [ -z "$urls" ]; then
        log_info "profile 中没有定义 health_check，跳过"
        return
    fi

    # 逐个检查
    while IFS='|' read -r name url; do
        if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
            log_ok "$name 健康检查通过: $url"
        else
            log_warn "$name 健康检查未通过: $url (非致命)"
            HAS_WARNINGS=true
        fi
    done <<< "$urls"
}

# ============================================================
# 校验 4: 自定义钩子 (validate.d/*.sh)
# ============================================================
run_custom_hooks() {
    local hooks_dir="$SCRIPT_DIR/validate.d"

    if [ ! -d "$hooks_dir" ]; then
        return
    fi

    # 检查是否有 .sh 文件
    local has_hooks=false
    for hook in "$hooks_dir"/*.sh; do
        if [ -f "$hook" ]; then
            has_hooks=true
            break
        fi
    done

    if [ "$has_hooks" = false ]; then
        return
    fi

    log_info "运行自定义校验钩子 ..."

    for hook in "$hooks_dir"/*.sh; do
        [ -f "$hook" ] || continue
        local hook_name
        hook_name=$(basename "$hook")
        log_info "  运行: $hook_name"

        set +e
        bash "$hook" "$HEAD_BEFORE" 2>&1
        local hook_exit=$?
        set -e

        if [ $hook_exit -eq 0 ]; then
            log_ok "  $hook_name 通过"
        elif [ $hook_exit -eq 1 ]; then
            log_error "  $hook_name 失败 (致命)"
            FATAL_FAILURE=true
        else
            log_warn "  $hook_name 警告 (非致命)"
            HAS_WARNINGS=true
        fi
    done
}

# ============================================================
# 主流程
# ============================================================
main() {
    echo ""
    log_info "========== 开始校验 =========="

    validate_session_result
    check_git_progress
    run_health_checks
    run_custom_hooks

    echo ""
    if [ "$FATAL_FAILURE" = true ]; then
        log_error "========== 校验失败 (致命) =========="
        exit 1
    elif [ "$HAS_WARNINGS" = true ]; then
        log_warn "========== 校验通过 (有警告) =========="
        exit 0  # 警告不阻断
    else
        log_ok "========== 校验全部通过 =========="
        exit 0
    fi
}

main
