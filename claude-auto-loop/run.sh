#!/bin/bash
# ============================================================
# Claude Auto Loop Harness (通用版)
#
# 用法:
#   首次运行（详细需求）: 创建 requirements.md 后运行 bash claude-auto-loop/run.sh
#   首次运行（快捷模式）: bash claude-auto-loop/run.sh "你的需求描述"
#   继续运行:             bash claude-auto-loop/run.sh
#   观测模式:             bash claude-auto-loop/run.sh --view
#   限制 session 数:      bash claude-auto-loop/run.sh --max 10
#   控制暂停频率:         bash claude-auto-loop/run.sh --max 10 --pause 3
#
# 参数:
#   --view           交互式观测模式，实时显示 Agent 决策过程
#   --max N          最大 session 数（默认 50）
#   --pause N        每 N 个 session 暂停确认（默认 5）
#
# 执行顺序：
#   1. 加载 config.env（若存在，由 setup.sh 生成）
#   2. check_prerequisites：检查 claude/python3/CLAUDE.md/validate.sh，确保 git 仓库存在
#   3. 首次：run_scan（Agent 扫描 → 生成 profile/init.sh/tasks.json）
#   4. 循环：run_coding_session → validate.sh（失败则 git 回滚 + 重试）
#   5. 所有任务 done 时退出
#
# 关键技术：
#   - 2>&1 | tee：实时终端输出 + 日志记录（学习 auto-coding-agent-demo 模式）
#   - --append-system-prompt-file：将 CLAUDE.md 注入 system prompt，保证 Agent 协议加载
#   - --allowedTools：显式工具白名单，限制 Agent 可用工具范围
#   - --permission-mode bypassPermissions：允许 Agent 无需确认即可创建/编辑文件
#   - PreToolUse hook：首次工具调用时写入 .phase，进度提示从「思考中」切至「AI 编码中」
#
# 本脚本不含任何项目特定信息。
# 项目信息由 Agent 扫描后存入 project_profile.json。
# ============================================================

set -euo pipefail

# ============ 配置（可通过 CLI 参数覆盖） ============
MAX_SESSIONS=50          # 最大会话数（--max N 覆盖）
THINKING_PID=""          # 思考中提示的 PID，供 trap 终止用
MAX_RETRY=3              # 每个任务最大重试次数
PAUSE_EVERY=5            # 每 N 个会话暂停确认（--pause N 覆盖）
ALLOWED_TOOLS="Read,Edit,Write,Bash,Glob,Grep"  # Agent 可用工具白名单

# ============ 路径与默认值 ============
# CLAUDE_EXTRA_FLAGS 在 main() 中根据 config.env 的 CLAUDE_DEBUG 设置；此处预先初始化避免 set -u 下 unbound variable
# CLAUDE_MODEL_FLAGS 在 main() 中当使用 DeepSeek 时设为 --model，覆盖 settings 防止误用 reasoner
CLAUDE_EXTRA_FLAGS=()
CLAUDE_MODEL_FLAGS=()
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TASKS_FILE="$SCRIPT_DIR/tasks.json"
PROGRESS_FILE="$SCRIPT_DIR/progress.txt"
SESSION_RESULT="$SCRIPT_DIR/session_result.json"
PROFILE="$SCRIPT_DIR/project_profile.json"
REQUIREMENTS_HASH_FILE="$SCRIPT_DIR/requirements_hash.current"
CLAUDE_MD="$SCRIPT_DIR/CLAUDE.md"
SCAN_PROTOCOL_MD="$SCRIPT_DIR/SCAN_PROTOCOL.md"
VALIDATE_SH="$SCRIPT_DIR/validate.sh"
PHASE_FILE="$SCRIPT_DIR/.phase"
PHASE_STEP_FILE="$SCRIPT_DIR/.phase_step"
ACTIVITY_LOG="$SCRIPT_DIR/.activity_log"

# ============ 颜色输出 ============
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 进度提示：通过 Claude Code PreToolUse hook 检测工具调用，精准切换「思考中」→「AI 编码中」
# .phase 由 hooks/phase-signal.py 在首次 PreToolUse 时写入 "coding"
# .phase_step 为根据工具调用推断的 6 步流程当前步骤（如 "4-增量实现"）
start_thinking_indicator() {
    echo "thinking" > "$PHASE_FILE" 2>/dev/null || true
    rm -f "$PHASE_STEP_FILE" "$ACTIVITY_LOG" 2>/dev/null || true
    ( while true; do
        sleep 15
        phase="thinking"
        [ -f "$PHASE_FILE" ] && phase=$(cat "$PHASE_FILE" 2>/dev/null | head -1) || true
        step_label=""
        [ -f "$PHASE_STEP_FILE" ] && step_label=$(cat "$PHASE_STEP_FILE" 2>/dev/null | head -1) || true
        activity=""
        if [ -f "$ACTIVITY_LOG" ]; then
            last_line=$(tail -1 "$ACTIVITY_LOG" 2>/dev/null)
            if [ -n "$last_line" ]; then
                activity=$(echo "$last_line" | cut -d'|' -f2,3 | tr '|' ' ')
            fi
        fi
        if [ "$phase" = "coding" ]; then
          if [ -n "$step_label" ] && [ -n "$activity" ]; then
            echo -e "${GREEN}[INFO]${NC}  AI 编码中 · 步骤${step_label} · ${activity} $(date '+%H:%M:%S')" >&2
          elif [ -n "$step_label" ]; then
            echo -e "${GREEN}[INFO]${NC}  AI 编码中 · 步骤${step_label} $(date '+%H:%M:%S')" >&2
          else
            echo -e "${GREEN}[INFO]${NC}  AI 编码中... $(date '+%H:%M:%S')" >&2
          fi
        else
          echo -e "${BLUE}[INFO]${NC}  思考中... $(date '+%H:%M:%S')" >&2
        fi
      done ) &
    THINKING_PID=$!
}
stop_thinking_indicator() {
    [ -n "$THINKING_PID" ] && kill $THINKING_PID 2>/dev/null && wait $THINKING_PID 2>/dev/null
    THINKING_PID=""
    # 会话结束，清理临时状态文件避免下次误读旧状态
    rm -f "$PHASE_STEP_FILE" "$ACTIVITY_LOG" 2>/dev/null || true
}

# ============ 前置检查 ============
check_prerequisites() {
    if ! command -v claude &> /dev/null; then
        log_error "请先安装 Claude Code: npm install -g @anthropic-ai/claude-code"
        exit 1
    fi

    if ! command -v python3 &> /dev/null; then
        log_error "需要 python3 来解析 JSON 文件"
        exit 1
    fi

    if [ ! -f "$CLAUDE_MD" ]; then
        log_error "CLAUDE.md 不存在: $CLAUDE_MD"
        exit 1
    fi

    if [ ! -f "$SCAN_PROTOCOL_MD" ]; then
        log_error "SCAN_PROTOCOL.md 不存在: $SCAN_PROTOCOL_MD"
        exit 1
    fi

    if [ ! -f "$VALIDATE_SH" ]; then
        log_error "validate.sh 不存在: $VALIDATE_SH"
        exit 1
    fi

    # 检测模型配置
    if [ ! -f "$SCRIPT_DIR/config.env" ]; then
        log_warn "未找到模型配置文件"
        log_warn "如需使用 GLM 4.7 等替代模型降低成本，请先运行:"
        log_warn "  bash claude-auto-loop/setup.sh"
        log_info "本次将使用默认 Claude 模型继续"
    fi

    # 提示 Cursor 用户复制规则文件
    if [ -d "$PROJECT_ROOT/.cursor" ] && [ ! -f "$PROJECT_ROOT/.cursor/rules/claude-auto-loop.mdc" ]; then
        if [ -f "$SCRIPT_DIR/cursor.mdc" ]; then
            log_warn "检测到 .cursor/ 目录但未安装 Cursor 规则文件"
            log_warn "如需 Cursor IDE 支持，请执行:"
            log_warn "  mkdir -p .cursor/rules && cp claude-auto-loop/cursor.mdc .cursor/rules/claude-auto-loop.mdc"
        fi
    fi

    # 确保 git 仓库存在
    cd "$PROJECT_ROOT"
    if [ ! -d .git ]; then
        log_info "初始化 git 仓库..."
        git init
        git add -A
        git commit -m "init: 项目初始化" --allow-empty
    fi
}

# ============ 辅助函数 ============

get_head() {
    cd "$PROJECT_ROOT"
    git rev-parse HEAD 2>/dev/null || echo "none"
}

# 计算 requirements.md 的 SHA256 hash，供需求同步条件触发使用
# 若文件不存在返回空字符串
get_requirements_hash() {
    local req_file="$PROJECT_ROOT/requirements.md"
    if [ -f "$req_file" ]; then
        if command -v shasum &> /dev/null; then
            shasum -a 256 < "$req_file" | awk '{print $1}'
        elif command -v sha256sum &> /dev/null; then
            sha256sum < "$req_file" | awk '{print $1}'
        else
            echo ""
        fi
    else
        echo ""
    fi
}

all_tasks_done() {
    python3 -c "
import json, sys
try:
    with open('$TASKS_FILE') as f:
        data = json.load(f)
    features = data.get('features', [])
    if not features:
        print('true')
        sys.exit(0)
    all_done = all(f.get('status') == 'done' for f in features)
    print('true' if all_done else 'false')
except Exception:
    print('false')
" 2>/dev/null
}

get_task_stats() {
    python3 -c "
import json
try:
    with open('$TASKS_FILE') as f:
        data = json.load(f)
    features = data.get('features', [])
    total = len(features)
    done = sum(1 for f in features if f.get('status') == 'done')
    failed = sum(1 for f in features if f.get('status') == 'failed')
    in_prog = sum(1 for f in features if f.get('status') == 'in_progress')
    testing = sum(1 for f in features if f.get('status') == 'testing')
    pending = sum(1 for f in features if f.get('status') == 'pending')
    print(f'{done}/{total} done, {in_prog} in_progress, {testing} testing, {failed} failed, {pending} pending')
except Exception as e:
    print(f'无法读取: {e}')
" 2>/dev/null
}

# 检测项目根目录是否有代码文件（判断新旧项目）
has_code_files() {
    cd "$PROJECT_ROOT"
    # 检查常见的代码/项目标志文件
    local markers=(
        "package.json" "pyproject.toml" "requirements.txt" "setup.py"
        "Cargo.toml" "go.mod" "pom.xml" "build.gradle"
        "Makefile" "Dockerfile" "docker-compose.yml"
        "README.md" "main.py" "app.py" "index.js" "index.ts"
    )
    for marker in "${markers[@]}"; do
        if [ -f "$marker" ]; then
            return 0
        fi
    done
    # 检查是否有源代码目录
    for dir in src lib app backend frontend web server client; do
        if [ -d "$dir" ]; then
            return 0
        fi
    done
    return 1
}

rollback_to() {
    local target_head="${1:-}"
    local validate_log="${2:-}"  # New parameter: path to validation log

    [ -z "$target_head" ] && { log_error "rollback_to 需要 target_head 参数"; return 1; }
    log_warn "回滚到 $target_head ..."
    cd "$PROJECT_ROOT"
    git reset --hard "$target_head"
    log_ok "回滚完成"

    # 记录失败到 progress.txt
    local error_reason="harness 校验失败"
    if [ -n "$validate_log" ] && [ -f "$validate_log" ]; then
        # Extract error from log (look for INVALID or ERROR)
        local extracted
        extracted=$(grep -E "INVALID:|ERROR" "$validate_log" | head -1 | sed 's/.*INVALID://;s/.*ERROR//' | sed 's/^[[:space:]]*//')
        if [ -n "$extracted" ]; then
            error_reason="校验失败: $extracted"
        fi
    fi

    local timestamp
    timestamp=$(date "+%Y-%m-%d %H:%M")
    if [ -f "$PROGRESS_FILE" ]; then
        echo "" >> "$PROGRESS_FILE"
        echo "=== FAILED SESSION | $timestamp ===" >> "$PROGRESS_FILE"
        echo "- 结果：$error_reason，已自动回滚" >> "$PROGRESS_FILE"
        echo "- 回滚到: $target_head" >> "$PROGRESS_FILE"
    fi
}

# ============ 初始化阶段 ============

# 步骤 1: 项目扫描（生成 project_profile.json + init.sh）
run_scan() {
    local requirement="${1:-}"

    if has_code_files; then
        log_info "检测到已有代码 → 旧项目模式（扫描现有项目）"
        local project_type="existing"
    else
        log_info "未检测到代码文件 → 新项目模式（从零创建）"
        local project_type="new"
    fi

    echo ""
    log_info "正在调用 Claude Code 执行项目扫描..."
    log_info "首次 API 响应可能需要 1-2 分钟，PreToolUse hook 将在首次工具调用时切换为「AI 编码中」"
    echo "--------------------------------------------"
    start_thinking_indicator

    local scan_prompt="你是项目初始化 Agent。

项目类型: $project_type
用户需求: $requirement

按照「项目扫描协议」执行：扫描项目、生成 profile 和 init.sh、分解任务到 tasks.json。
完成后写入 session_result.json 并 git commit。"

    # 扫描 session 需要 CLAUDE.md（通用协议）+ SCAN_PROTOCOL.md（扫描专用）
    # 拼接为临时文件注入 system prompt
    local combined_prompt
    combined_prompt=$(mktemp)
    cat "$CLAUDE_MD" "$SCAN_PROTOCOL_MD" > "$combined_prompt"

    # 2>&1 | tee 实时终端输出 + 日志记录（前台管道，Ctrl+C 自动终止）
    set +e
    claude "${CLAUDE_MODEL_FLAGS[@]}" "${CLAUDE_EXTRA_FLAGS[@]}" \
        --permission-mode bypassPermissions \
        --settings "$SCRIPT_DIR/hooks-settings.json" \
        --append-system-prompt-file "$combined_prompt" \
        -p "$scan_prompt" \
        2>&1 | tee "$LOG_DIR/scan_$(date +%s).log"
    local scan_exit=${PIPESTATUS[0]}
    set -e
    rm -f "$combined_prompt"
    stop_thinking_indicator

    echo "--------------------------------------------"
    # 验证关键文件是否生成
    local success=true
    if [ ! -f "$PROFILE" ]; then
        log_error "project_profile.json 未生成"
        success=false
    fi
    if [ ! -f "$TASKS_FILE" ]; then
        log_error "tasks.json 未生成"
        success=false
    fi
    if [ ! -f "$SCRIPT_DIR/init.sh" ]; then
        log_warn "init.sh 未生成（Agent 可能判断无需启动服务）"
    else
        chmod +x "$SCRIPT_DIR/init.sh"
    fi

    if [ "$success" = false ]; then
        log_error "初始化失败：关键文件未生成"
        return 1
    fi

    log_ok "初始化完成"
    local stats
    stats=$(get_task_stats)
    log_info "任务统计: $stats"
}

# ============ 构建 MCP 工具提示 ============
build_mcp_hint() {
    local hint=""
    if [ "${MCP_PLAYWRIGHT:-false}" = "true" ]; then
        hint="你有 Playwright MCP 可用，可以用 browser_navigate、browser_snapshot、browser_click 等工具做 Web 端到端测试。对于前端功能，优先使用 Playwright MCP 进行浏览器验证。"
    fi
    echo "$hint"
}

# ============ 编码会话 ============
run_coding_session() {
    local session_num="${1:-1}"

    rm -f "$SESSION_RESULT"

    # 为需求同步条件触发：在会话开始前写入当前 requirements.md 的 hash
    # Agent 通过比较此文件与 sync_state.json 决定是否执行需求 diff
    local req_hash
    req_hash=$(get_requirements_hash 2>/dev/null || true)
    if [ -n "$req_hash" ]; then
        echo "$req_hash" > "$REQUIREMENTS_HASH_FILE"
    else
        rm -f "$REQUIREMENTS_HASH_FILE"
    fi

    echo ""
    log_info "正在调用 Claude Code (Session $session_num)..."
    log_info "PreToolUse hook 检测工具调用，首次调用时自动切换为「AI 编码中」"
    echo "--------------------------------------------"
    start_thinking_indicator

    # 构建可选的 MCP 工具提示
    local mcp_hint=""
    mcp_hint=$(build_mcp_hint 2>/dev/null || true)

    # 构建失败重试上下文（Step 4: 注入上次失败原因）
    local retry_context=""
    if [ "$consecutive_failures" -gt 0 ] && [ -f "$LOG_DIR/validate_session_$((session_num - 1)).log" ]; then
        local fail_reason
        fail_reason=$(grep -E "FAIL|INVALID|ERROR" "$LOG_DIR/validate_session_$((session_num - 1)).log" | head -3)
        retry_context="
注意：上次会话校验失败，原因：$fail_reason。请避免同样的问题。"
    fi

    # 构建 tests.json 感知提示（选择性回归测试）
    local test_hint=""
    if [ -f "$SCRIPT_DIR/tests.json" ]; then
        local test_count
        test_count=$(python3 -c "
import json
try:
    with open('$SCRIPT_DIR/tests.json') as f:
        data = json.load(f)
    print(len(data.get('test_cases', [])))
except Exception:
    print('0')
" 2>/dev/null)
        if [ "${test_count:-0}" -gt 0 ]; then
            test_hint="tests.json 已有 ${test_count} 个测试用例，Step 5 时按测试协议执行选择性回归。"
        fi
    fi

    # CLAUDE.md 已通过 --append-system-prompt-file 注入 system prompt，inline prompt 只含 session 变量
    local coding_prompt="Session ${session_num}。执行 6 步流程。
效率要求：先规划后编码，完成全部编码后再统一测试，禁止编码-测试反复跳转。后端任务用 curl 验证，不启动浏览器。小任务可合并执行。
${mcp_hint:+前端/全栈任务可用: $mcp_hint
}${test_hint:+测试: $test_hint
}完成后写入 session_result.json。${retry_context}"

    set +e
    local session_log="$LOG_DIR/session_${session_num}_$(date +%s).log"
    claude "${CLAUDE_MODEL_FLAGS[@]}" "${CLAUDE_EXTRA_FLAGS[@]}" \
        --permission-mode bypassPermissions \
        --settings "$SCRIPT_DIR/hooks-settings.json" \
        --append-system-prompt-file "$CLAUDE_MD" \
        --verbose \
        --allowedTools "$ALLOWED_TOOLS" \
        -p "$coding_prompt" \
        2>&1 | tee "$session_log"
    local claude_exit=${PIPESTATUS[0]}
    stop_thinking_indicator
    echo "--------------------------------------------"
    set -e

    if [ "${claude_exit:-0}" -ne 0 ]; then
        log_warn "Claude Code 退出码: $claude_exit (查看日志: $session_log)"
    fi

    return "${claude_exit:-0}"
}

# ============ 观测模式（交互式单次 session） ============
run_view_session() {
    local requirement="${1:-}"

    local system_prompt_content
    local initial_prompt

    if [ ! -f "$PROFILE" ] || [ ! -f "$TASKS_FILE" ]; then
        system_prompt_content="$(cat "$CLAUDE_MD" "$SCAN_PROTOCOL_MD")"
        local project_type="new"
        has_code_files && project_type="existing"
        initial_prompt="你是项目初始化 Agent。项目类型: $project_type。用户需求: $requirement。按照「项目扫描协议」执行。"
    else
        system_prompt_content="$(cat "$CLAUDE_MD")"
        local mcp_hint=""
        mcp_hint=$(build_mcp_hint 2>/dev/null || true)
        local view_test_hint=""
        if [ -f "$SCRIPT_DIR/tests.json" ]; then
            local tc
            tc=$(python3 -c "import json; print(len(json.load(open('$SCRIPT_DIR/tests.json')).get('test_cases',[])))" 2>/dev/null || echo 0)
            [ "${tc:-0}" -gt 0 ] && view_test_hint=" tests.json 已有 ${tc} 个测试用例。"
        fi
        initial_prompt="执行 6 步流程，完成下一个任务。${mcp_hint:+ 可用工具: $mcp_hint}${view_test_hint}"
    fi

    claude "${CLAUDE_MODEL_FLAGS[@]}" "${CLAUDE_EXTRA_FLAGS[@]}" \
        --permission-mode bypassPermissions \
        --settings "$SCRIPT_DIR/hooks-settings.json" \
        --append-system-prompt "$system_prompt_content" \
        "$initial_prompt"
}

# ============ 主流程 ============
main() {
    echo ""
    # ============ 解析 CLI 参数 ============
    local view_mode=false
    while [[ "${1:-}" == --* ]]; do
        case "$1" in
            --view)  view_mode=true; shift ;;
            --max)   MAX_SESSIONS="${2:?--max 需要参数}"; shift 2 ;;
            --pause) PAUSE_EVERY="${2:?--pause 需要参数}"; shift 2 ;;
            *)       log_error "未知参数: $1"; exit 1 ;;
        esac
    done

    echo "============================================"
    echo "  Claude Auto Loop${view_mode:+ (观测模式)}"
    echo "============================================"
    echo ""

    # ============ 日志配置 ============
    LOG_DIR="$SCRIPT_DIR/logs"
    mkdir -p "$LOG_DIR"
    
    # ... (rest of main function)

    # 信号处理：Ctrl+C / kill 时优雅退出
    # 前台管道模式下 Ctrl+C 自动 SIGINT claude+tee，只需清理 THINKING_PID
    trap 'if [ -n "$THINKING_PID" ]; then kill $THINKING_PID 2>/dev/null; wait $THINKING_PID 2>/dev/null; fi; echo ""; log_warn "收到中断信号，正在安全退出..."; log_info "下次运行 bash claude-auto-loop/run.sh 即可恢复"; exit 130' INT TERM

    # 加载模型配置（如果存在）；CLAUDE_EXTRA_FLAGS 已在脚本开头初始化
    if [ -f "$SCRIPT_DIR/config.env" ]; then
        source "$SCRIPT_DIR/config.env"
        # 仅导出非空变量，避免覆盖已有环境
        [ -n "${ANTHROPIC_BASE_URL:-}" ] && export ANTHROPIC_BASE_URL
        [ -n "${ANTHROPIC_API_KEY:-}" ] && export ANTHROPIC_API_KEY
        [ -n "${ANTHROPIC_AUTH_TOKEN:-}" ] && export ANTHROPIC_AUTH_TOKEN
        # GLM 旧配置可能无 ANTHROPIC_MODEL，默认 glm-4.7
        if [ -n "${ANTHROPIC_BASE_URL:-}" ] && { [[ "${ANTHROPIC_BASE_URL}" == *"bigmodel.cn"* ]] || [[ "${ANTHROPIC_BASE_URL}" == *"z.ai"* ]]; }; then
            [ -z "${ANTHROPIC_MODEL:-}" ] && ANTHROPIC_MODEL=glm-4.7
        fi
        [ -n "${ANTHROPIC_MODEL:-}" ] && export ANTHROPIC_MODEL
        [ -n "${API_TIMEOUT_MS:-}" ] && export API_TIMEOUT_MS
        [ -n "${MCP_TOOL_TIMEOUT:-}" ] && export MCP_TOOL_TIMEOUT
        [ -n "${ANTHROPIC_SMALL_FAST_MODEL:-}" ] && export ANTHROPIC_SMALL_FAST_MODEL
        [ -n "${CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC:-}" ] && export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC
        [ -n "${CLAUDE_CODE_EFFORT_LEVEL:-}" ] && export CLAUDE_CODE_EFFORT_LEVEL
        
        # DeepSeek 智能映射策略：
        # 如果 config.env 中配置了 deepseek-chat，我们在运行时将其强制替换为 claude-3-haiku-20240307
        # 这样做的好处是：
        # 1. 配置文件 clean (deepseek-chat)，用户易读
        # 2. 运行时 effective (haiku shim)，确保禁用 thinking
        if [ -n "${ANTHROPIC_BASE_URL:-}" ] && [[ "${ANTHROPIC_BASE_URL}" == *deepseek* ]]; then
            # 仅针对 Chat 模式进行劫持
            if [[ "${ANTHROPIC_MODEL:-}" == "deepseek-chat" ]]; then
                export ANTHROPIC_MODEL="claude-3-haiku-20240307"
                # 覆盖所有内部别名，彻底封死 Thinking 路径
                export ANTHROPIC_DEFAULT_OPUS_MODEL="claude-3-haiku-20240307"
                export ANTHROPIC_DEFAULT_SONNET_MODEL="claude-3-haiku-20240307"
                export ANTHROPIC_DEFAULT_HAIKU_MODEL="claude-3-haiku-20240307"
                export ANTHROPIC_SMALL_FAST_MODEL="claude-3-haiku-20240307"
                # 仍保留 budget=0 作为双重保险
                export ANTHROPIC_THINKING_BUDGET=0
            fi
        fi

        # 确保别名变量被 export，否则 claude 子进程无法读取，会回退到默认 Opus (开启 Thinking)
        [ -n "${ANTHROPIC_DEFAULT_OPUS_MODEL:-}" ] && export ANTHROPIC_DEFAULT_OPUS_MODEL
        [ -n "${ANTHROPIC_DEFAULT_SONNET_MODEL:-}" ] && export ANTHROPIC_DEFAULT_SONNET_MODEL
        [ -n "${ANTHROPIC_DEFAULT_HAIKU_MODEL:-}" ] && export ANTHROPIC_DEFAULT_HAIKU_MODEL
        
        [ -n "${ANTHROPIC_THINKING_BUDGET:-}" ] && export ANTHROPIC_THINKING_BUDGET
        log_ok "模型配置已加载: ${MODEL_PROVIDER:-unknown}${ANTHROPIC_MODEL:+ ($ANTHROPIC_MODEL)}"
        # deepseek-reasoner 成本提醒
        if [[ "${ANTHROPIC_MODEL:-}" == *reasoner* ]] && { [[ "${ANTHROPIC_BASE_URL:-}" == *deepseek* ]] || [ "${MODEL_PROVIDER:-}" = "deepseek" ]; }; then
            log_warn "deepseek-reasoner 价格约为 deepseek-chat 的 2 倍，改 config.env 中 ANTHROPIC_MODEL=deepseek-chat 可降低成本"
        fi
        # CLAUDE_DEBUG 可随时在 config.env 中修改，无需重跑 setup
        # 取值: verbose | mcp | api,mcp | api,hooks 等，空则不追加
        if [ -n "${CLAUDE_DEBUG:-}" ]; then
            if [ "$CLAUDE_DEBUG" = "verbose" ]; then
                CLAUDE_EXTRA_FLAGS=(--verbose)
            else
                CLAUDE_EXTRA_FLAGS=(--debug "$CLAUDE_DEBUG")
            fi
            log_info "Claude 调试: ${CLAUDE_EXTRA_FLAGS[*]}"
        else
            CLAUDE_EXTRA_FLAGS=()
        fi
        
        # 第三方提供商显式传 --model 覆盖 settings
        if [ -n "${ANTHROPIC_BASE_URL:-}" ] && [ -n "${ANTHROPIC_MODEL:-}" ]; then
            if [[ "${ANTHROPIC_BASE_URL}" == *deepseek* ]] || [[ "${ANTHROPIC_BASE_URL}" == *dashscope* ]]; then
                CLAUDE_MODEL_FLAGS=(--model "$ANTHROPIC_MODEL")
            else
                CLAUDE_MODEL_FLAGS=()
            fi
        else
            CLAUDE_MODEL_FLAGS=()
        fi
    else
        CLAUDE_EXTRA_FLAGS=()
        CLAUDE_MODEL_FLAGS=()
    fi

    check_prerequisites

    # 根据 MCP 配置扩展 ALLOWED_TOOLS 白名单
    [ "${MCP_PLAYWRIGHT:-false}" = "true" ] && ALLOWED_TOOLS="$ALLOWED_TOOLS,mcp__playwright__*"

    # ---------- 读取需求（优先 requirements.md，其次 CLI 参数） ----------
    local requirement=""
    local req_file="$PROJECT_ROOT/requirements.md"
    if [ -f "$req_file" ]; then
        requirement=$(cat "$req_file")
        log_ok "已读取需求文件: requirements.md"
    else
        requirement="${1:-}"
    fi

    # ---------- 观测模式：交互式单次 session，然后退出 ----------
    if [ "$view_mode" = true ]; then
        log_info "观测模式：交互式运行，实时显示工具调用和决策过程"
        log_info "退出：Ctrl+C 或输入 /exit"
        echo "--------------------------------------------"
        run_view_session "$requirement"
        exit 0
    fi

    # ---------- 初始化阶段（带重试） ----------
    # 判断顺序: profile → tasks → 需要初始化
    if [ ! -f "$PROFILE" ] || [ ! -f "$TASKS_FILE" ]; then
        if [ -z "$requirement" ]; then
            log_error "首次运行需要提供需求描述"
            echo ""
            echo "用法（二选一）:"
            echo "  方式 1: 在项目根目录创建 requirements.md（推荐，可写详细需求）"
            echo "          cp claude-auto-loop/requirements.example.md requirements.md"
            echo "          vim requirements.md"
            echo "          bash claude-auto-loop/run.sh"
            echo ""
            echo "  方式 2: 直接传入一句话需求"
            echo "          bash claude-auto-loop/run.sh \"你的需求描述\""
            exit 1
        fi

        local init_attempt=0
        local init_max=3
        while [ $init_attempt -lt $init_max ]; do
            init_attempt=$((init_attempt + 1))
            log_info "初始化尝试 $init_attempt / $init_max ..."

            set +e
            run_scan "$requirement"
            local scan_exit=$?
            set -e

            if [ -f "$PROFILE" ] && [ -f "$TASKS_FILE" ]; then
                break  # 关键文件已生成，初始化成功
            fi

            if [ $init_attempt -lt $init_max ]; then
                log_warn "初始化未完成，将重试..."
            fi
        done

        # 重试完仍然失败才退出
        if [ ! -f "$PROFILE" ] || [ ! -f "$TASKS_FILE" ]; then
            log_error "初始化失败：已重试 $init_max 次，关键文件仍未生成"
            echo ""
            echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
            echo -e "${YELLOW}  若出现 \"Credit balance is too low\"，说明 Claude API 额度不足${NC}"
            echo -e "${YELLOW}  可运行 setup.sh 切换到 GLM 4.7 等替代模型：${NC}"
            echo ""
            echo -e "  ${GREEN}bash claude-auto-loop/setup.sh${NC}"
            echo ""
            echo -e "${YELLOW}  完成后重新运行 run.sh 即可${NC}"
            echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
            echo ""
            log_info "请检查 Agent 输出，手动排查问题后重新运行"
            exit 1
        fi
    else
        log_ok "检测到已有 project_profile.json + tasks.json，跳过初始化"
        local stats
        stats=$(get_task_stats)
        log_info "当前进度: $stats"
    fi

    # ---------- 编码循环 ----------
    log_info "开始编码循环 (最多 $MAX_SESSIONS 个会话) ..."
    echo ""

    local session=0
    local consecutive_failures=0

    while [ $session -lt $MAX_SESSIONS ]; do
        session=$((session + 1))

        echo ""
        echo "--------------------------------------------"
        log_info "Session $session / $MAX_SESSIONS"
        echo "--------------------------------------------"

        # 检查是否所有任务已完成
        if [ "$(all_tasks_done)" = "true" ]; then
            echo ""
            log_ok "所有任务已完成！"
            local stats
            stats=$(get_task_stats)
            log_info "最终统计: $stats"
            break
        fi

        # 显示当前进度
        local stats
        stats=$(get_task_stats)
        log_info "进度: $stats"

        # 记录 session 前的 HEAD
        local head_before
        head_before=$(get_head)

        # ---------- 执行编码会话 ----------
        run_coding_session "$session"

        # ---------- Harness 校验 (调用 validate.sh) ----------
        log_info "开始 harness 校验 ..."

        set +e
        local validate_log="$LOG_DIR/validate_session_${session}.log"
        bash "$VALIDATE_SH" "$head_before" > "$validate_log" 2>&1
        local validate_exit=$?
        cat "$validate_log"  # 输出到控制台供用户查看
        set -e

        # ---------- 根据校验结果决定 ----------
        if [ $validate_exit -eq 0 ]; then
            log_ok "Session $session 校验通过"
            
            # 自动推送 (Auto Push)
            # 仅当存在 remote 时尝试推送，忽略错误不中断循环
            if git remote | grep -q .; then
                log_info "正在推送代码..."
                if git push; then
                    log_ok "推送成功"
                else
                    log_warn "推送失败 (请检查网络或权限)，继续执行..."
                fi
            fi

            consecutive_failures=0
            rm -f "$SESSION_RESULT"
        else
            # validate_exit=1 表示致命失败，需要回滚
            consecutive_failures=$((consecutive_failures + 1))
            log_error "Session $session 校验失败 (连续失败: $consecutive_failures/$MAX_RETRY)"

            rollback_to "$head_before" "$validate_log"

            if [ $consecutive_failures -ge $MAX_RETRY ]; then
                log_error "连续失败 $MAX_RETRY 次，跳过当前任务"

                # 标记当前 in_progress 任务为 failed
                python3 -c "
import json
try:
    with open('$TASKS_FILE', 'r') as f:
        data = json.load(f)
    for feat in data['features']:
        if feat.get('status') == 'in_progress':
            feat['status'] = 'failed'
            break
    with open('$TASKS_FILE', 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
except Exception:
    pass
" 2>/dev/null || true

                consecutive_failures=0
                log_warn "已将任务标记为 failed，继续下一个任务"
            fi
        fi

        # ---------- 定期暂停确认 ----------
        if [ $((session % PAUSE_EVERY)) -eq 0 ]; then
            echo ""
            local stats
            stats=$(get_task_stats)
            log_info "已完成 $session 个会话 | $stats"

            if [ -t 0 ]; then
                read -p "是否继续？(y/n) " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    log_info "手动停止"
                    break
                fi
            fi
        fi
    done

    # ---------- 最终报告 ----------
    echo ""
    echo "============================================"
    echo "  运行结束"
    echo "============================================"
    echo ""
    log_info "共执行 $session 个会话"
    local final_stats
    final_stats=$(get_task_stats)
    log_info "最终进度: $final_stats"
    echo ""

    if [ $session -ge $MAX_SESSIONS ]; then
        log_warn "已达到最大会话数 ($MAX_SESSIONS)，仍有未完成任务"
        log_info "继续运行: bash claude-auto-loop/run.sh"
    fi

    log_info "查看进度: cat $PROGRESS_FILE"
    log_info "查看任务: cat $TASKS_FILE"
    log_info "查看项目: cat $PROFILE"
}

# ============ 入口 ============
main "$@"
