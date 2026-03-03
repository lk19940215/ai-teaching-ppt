#!/bin/bash
# ============================================================
# Claude Auto Loop 前置配置
#
# 用法: bash claude-auto-loop/setup.sh
#
# 模块结构:
#   主流程 main()           - 交互选择 + 调用提供商写入
#   配置写入 write_*        - write_config_header, append_config_common
#   提供商 write_*_config   - Claude/GLM/阿里云百炼/DeepSeek/自定义
#   MCP configure_mcp_tools - Playwright + CLAUDE_DEBUG
#
# 配置保存到 config.env，run.sh 加载。含 API Key，已 gitignore。
# DeepSeek 参考: https://api-docs.deepseek.com/zh-cn/guides/anthropic_api
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$SCRIPT_DIR/config.env"

# ============ 共享环境引导 ============
source "$SCRIPT_DIR/_env.sh"

# ============ 颜色输出 ============
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }

# ============ 主流程 ============
main() {
    echo ""
    echo "============================================"
    echo "  Claude Auto Loop 前置配置"
    echo "============================================"
    echo ""
    echo "  第一步: 模型提供商配置"
    echo "  第二步: MCP 工具 + 调试输出（可选）"
    echo ""

    # 检测已有配置
    if [ -f "$CONFIG_FILE" ]; then
        log_warn "检测到已有配置文件: $CONFIG_FILE"
        source "$CONFIG_FILE"
        echo "  当前模型提供商: ${MODEL_PROVIDER:-未知}"
        echo "  当前 BASE_URL: ${ANTHROPIC_BASE_URL:-默认}"
        echo "  Playwright MCP: ${MCP_PLAYWRIGHT:-未配置}"
        echo ""
        read -p "是否重新配置？(y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "保留现有配置，退出"
            exit 0
        fi
        echo ""
    fi

    # 选择提供商
    echo "请选择模型提供商:"
    echo ""
    echo "  1) Claude 官方"
    echo -e "  2) GLM Coding Plan (智谱/Z.AI)      ${BLUE}https://open.bigmodel.cn${NC}"
    echo -e "  3) 阿里云 Coding Plan (百炼)         ${BLUE}https://bailian.console.aliyun.com${NC}"
    echo -e "  4) DeepSeek                          ${BLUE}https://platform.deepseek.com${NC}"
    echo "  5) 自定义 (Anthropic 兼容)"
    echo ""

    local choice
    while true; do
        read -p "选择 [1-5]: " choice
        case $choice in
            1|2|3|4|5) break ;;
            *) echo "请输入 1-5" ;;
        esac
    done

    echo ""

    case $choice in
        1)
            write_claude_config
            ;;
        2)
            # GLM Coding Plan: 子选择平台 → 选模型 → 输入 Key
            local glm_platform glm_provider glm_base_url glm_api_url
            glm_platform=$(read_glm_platform | tr -d '\n')
            if [ "$glm_platform" = "bigmodel" ]; then
                glm_provider="glm-bigmodel"
                glm_base_url="https://open.bigmodel.cn/api/anthropic"
                glm_api_url="https://open.bigmodel.cn/usercenter/proj-mgmt/apikeys"
            else
                glm_provider="glm-zai"
                glm_base_url="https://api.z.ai/api/anthropic"
                glm_api_url="https://z.ai/manage-apikey/apikey-list"
            fi
            local glm_model
            glm_model=$(read_glm_model | tr -d '\n')
            local api_key
            api_key=$(read_api_key "$glm_provider" "$glm_api_url" "$([ "${MODEL_PROVIDER:-}" = "$glm_provider" ] && echo "${ANTHROPIC_API_KEY:-}")" | tr -d '\n')
            write_glm_config "$glm_provider" "$glm_base_url" "$api_key" "$glm_model"
            ;;
        3)
            # 阿里云 Coding Plan (百炼)
            local aliyun_base_url
            aliyun_base_url=$(read_aliyun_region | tr -d '\n')
            local api_key
            api_key=$(read_api_key "阿里云百炼" "https://bailian.console.aliyun.com/?tab=model#/api-key" "$([ "${MODEL_PROVIDER:-}" = "aliyun-coding" ] && echo "${ANTHROPIC_API_KEY:-}")" | tr -d '\n')
            write_aliyun_config "$aliyun_base_url" "$api_key"
            ;;
        4)
            local api_key
            api_key=$(read_api_key "DeepSeek" "https://platform.deepseek.com/api_keys" "$([ "${MODEL_PROVIDER:-}" = "deepseek" ] && echo "${ANTHROPIC_API_KEY:-}")" | tr -d '\n')
            local ds_model
            ds_model=$(read_deepseek_model | tr -d '\n')
            write_deepseek_config "$api_key" "$ds_model"
            ;;
        5)
            local base_url api_key
            local default_url=""
            [ "${MODEL_PROVIDER:-}" = "custom" ] && [ -n "${ANTHROPIC_BASE_URL:-}" ] && default_url="$ANTHROPIC_BASE_URL"
            echo "请输入 Anthropic 兼容的 BASE_URL${default_url:+（回车保留: $default_url）}:"
            read -p "  URL: " base_url
            base_url="${base_url:-$default_url}"
            echo ""
            api_key=$(read_api_key "自定义平台" "" "$([ "${MODEL_PROVIDER:-}" = "custom" ] && echo "${ANTHROPIC_API_KEY:-}")" | tr -d '\n')
            write_custom_config "$base_url" "$api_key"
            ;;
    esac

    # === 第二步：MCP 工具配置 ===
    echo ""
    echo "============================================"
    echo "  MCP 工具配置（可选）"
    echo "============================================"
    echo ""

    configure_mcp_tools

    # 确保 config.env 不被提交到 git
    ensure_gitignore

    echo ""
    log_ok "配置完成！"
    echo ""
    echo "  配置文件: $CONFIG_FILE"
    echo "  使用方式: bash claude-auto-loop/run.sh \"你的需求\""
    echo "  详细需求: cp claude-auto-loop/docs/requirements.example.md requirements.md && vim requirements.md"
    echo "  重新配置: bash claude-auto-loop/setup.sh"
    echo ""
}

# ============ 读取 API Key ============
# 用法: read_api_key "平台名称" "获取入口URL" ["已有Key用于自动填充"]
# 重新配置且选择相同提供商时，传入已有 Key，用户回车即保留
read_api_key() {
    local platform="$1"
    local api_url="${2:-}"
    local default_key="${3:-}"
    if [ -n "$default_key" ]; then
        echo "保留当前 API Key 请直接回车，或输入新 Key:" >&2
    else
        echo "请输入 $platform 的 API Key:" >&2
    fi
    if [ -n "$api_url" ]; then
        echo -e "  ${BLUE}获取入口: $api_url${NC}" >&2
        echo "" >&2
    fi
    local key
    read -p "  API Key: " key
    if [ -z "$key" ]; then
        if [ -n "$default_key" ]; then
            echo "$default_key"
            return
        fi
        echo "API Key 不能为空" >&2
        exit 1
    fi
    echo "$key"
}

# ============ 配置写入（模块化） ============
# 参考 DeepSeek 官方文档: https://api-docs.deepseek.com/zh-cn/guides/anthropic_api

write_config_header() {
    local provider="$1"
    local desc="${2:-}"
    # 重新配置时备份旧 config，避免覆盖丢失
    if [ -f "$CONFIG_FILE" ]; then
        local backup="${CONFIG_FILE}.bak.$(date +%Y%m%d%H%M%S)"
        cp "$CONFIG_FILE" "$backup"
        log_info "已备份旧配置到: $backup"
    fi
    cat > "$CONFIG_FILE" << EOF
# Claude Auto Loop 模型配置
# 由 setup.sh 生成，请勿提交到 git（包含 API Key）
#
# 提供商: $provider
${desc:+# $desc
}
EOF
}

append_config_common() {
    local timeout_ms="${1:-3000000}"
    echo "API_TIMEOUT_MS=$timeout_ms" >> "$CONFIG_FILE"
    echo "MCP_TOOL_TIMEOUT=30000" >> "$CONFIG_FILE"
}

# --- 提供商: Claude 官方 ---
write_claude_config() {
    write_config_header "Claude 官方" "使用默认 Claude API，无需额外环境变量"
    echo "MODEL_PROVIDER=claude" >> "$CONFIG_FILE"
    append_config_common 3000000
    log_ok "已配置为 Claude 官方模型"
}

read_glm_platform() {
    echo "请选择 GLM 平台:" >&2
    echo "" >&2
    echo "  1) 智谱开放平台 (open.bigmodel.cn) - 国内直连" >&2
    echo "  2) Z.AI (api.z.ai) - 海外节点" >&2
    echo "" >&2
    local plat_choice
    while true; do
        read -p "选择 [1-2，默认 1]: " plat_choice
        plat_choice="${plat_choice:-1}"
        case $plat_choice in
            1) echo "bigmodel"; break ;;
            2) echo "zai"; break ;;
            *) echo "请输入 1 或 2" >&2 ;;
        esac
    done
}

read_glm_model() {
    echo "请选择 GLM 模型版本:" >&2
    echo "" >&2
    echo "  1) GLM 4.7  - 旗舰模型，推理与代码能力强" >&2
    echo "  2) GLM 5    - 最新模型（2026），能力更强" >&2
    echo "" >&2
    local model_choice
    while true; do
        read -p "选择 [1-2，默认 1]: " model_choice
        model_choice="${model_choice:-1}"
        case $model_choice in
            1) echo "glm-4.7"; break ;;
            2) echo "glm-5"; break ;;
            *) echo "请输入 1 或 2" >&2 ;;
        esac
    done
}

read_aliyun_region() {
    echo "请选择阿里云百炼区域:" >&2
    echo "" >&2
    echo "  1) 国内版 (coding.dashscope.aliyuncs.com)" >&2
    echo "  2) 国际版 (coding-intl.dashscope.aliyuncs.com)" >&2
    echo "" >&2
    local region_choice
    while true; do
        read -p "选择 [1-2，默认 1]: " region_choice
        region_choice="${region_choice:-1}"
        case $region_choice in
            1) echo "https://coding.dashscope.aliyuncs.com/apps/anthropic"; break ;;
            2) echo "https://coding-intl.dashscope.aliyuncs.com/apps/anthropic"; break ;;
            *) echo "请输入 1 或 2" >&2 ;;
        esac
    done
}

read_deepseek_model() {
    echo "请选择 DeepSeek 模型:" >&2
    echo "" >&2
    echo "  1) deepseek-chat     - 通用对话 (V3)，速度快成本低 [推荐日常使用]" >&2
    echo "  2) deepseek-reasoner - 纯推理模式 (R1)，全链路使用 R1，成本最高 [适合攻坚]" >&2
    echo "  3) deepseek-hybrid   - 混合模式 (R1 + V3)，规划用 R1，执行用 V3 [性价比之选]" >&2
    echo "" >&2
    local model_choice
    while true; do
        read -p "选择 [1-3，默认 1]: " model_choice
        model_choice="${model_choice:-1}"
        case $model_choice in
            1) echo "deepseek-chat"; break ;;
            2) echo "deepseek-reasoner"; break ;;
            3) echo "deepseek-hybrid"; break ;;
            *) echo "请输入 1, 2 或 3" >&2 ;;
        esac
    done
}

# --- 提供商: GLM (智谱 / Z.AI) ---
write_glm_config() {
    local provider="${1:-glm-bigmodel}"
    local base_url="${2:-}"
    local api_key="${3:-}"
    local model="${4:-glm-4.7}"

    write_config_header "GLM ($provider)" "模型: $model"
    {
        echo "MODEL_PROVIDER=$provider"
        echo "ANTHROPIC_MODEL=$model"
        echo "ANTHROPIC_BASE_URL=$base_url"
        echo "ANTHROPIC_API_KEY=$api_key"
    } >> "$CONFIG_FILE"
    append_config_common 3000000
    log_ok "已配置为 GLM 模型 (${provider}, ${model})"
    log_info "BASE_URL: $base_url"
}

# --- 提供商: 阿里云百炼 Coding Plan ---
# 参考: https://help.aliyun.com/zh/model-studio/coding-plan
write_aliyun_config() {
    local base_url="$1"
    local api_key="$2"

    write_config_header "阿里云 Coding Plan (百炼)" "Opus: glm-5 | Sonnet/Haiku: qwen3-coder-plus | Fallback: qwen3.5-plus"
    {
        echo "MODEL_PROVIDER=aliyun-coding"
        echo "ANTHROPIC_BASE_URL=$base_url"
        echo "ANTHROPIC_API_KEY=$api_key"
        echo ""
        echo "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1"
        echo "# Planner (规划/推理) → glm-5"
        echo "ANTHROPIC_DEFAULT_OPUS_MODEL=glm-5"
        echo "# Executor (写代码/编辑/工具调用) → qwen3-coder-plus"
        echo "ANTHROPIC_DEFAULT_SONNET_MODEL=qwen3-coder-plus"
        echo "ANTHROPIC_DEFAULT_HAIKU_MODEL=qwen3-coder-plus"
        echo "ANTHROPIC_SMALL_FAST_MODEL=qwen3-coder-plus"
        echo "# Fallback (通用) → qwen3.5-plus"
        echo "ANTHROPIC_MODEL=qwen3.5-plus"
    } >> "$CONFIG_FILE"
    append_config_common 3000000
    log_ok "已配置为阿里云 Coding Plan (百炼)"
    log_info "BASE_URL: $base_url"
    log_info "模型映射: Opus=glm-5 / Sonnet+Haiku=qwen3-coder-plus / Fallback=qwen3.5-plus"
}

# --- 提供商: DeepSeek ---
# 参考: https://api-docs.deepseek.com/zh-cn/guides/anthropic_api
write_deepseek_config() {
    local api_key="$1"
    local model="deepseek-chat"
    if [ "$#" -ge 2 ] && [ -n "${2+x}" ]; then
        model="$2"
    fi

    write_config_header "DeepSeek" "模型: ${model} | API_TIMEOUT_MS=600000 防止长输出超时（10分钟）"
    {
        echo "MODEL_PROVIDER=deepseek"
        echo "ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic"
        echo "ANTHROPIC_API_KEY=$api_key"
        echo "ANTHROPIC_AUTH_TOKEN=$api_key"
        echo ""
        echo "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1"
        
        if [[ "${model}" == "deepseek-chat" ]]; then
            echo "# [DeepSeek Chat 降本策略 (默认)]"
            echo "# 为了防止 Claude Code 客户端发送 'thinking' 参数（导致 DeepSeek 按 Reasoner 计费），"
            echo "# 我们保留 deepseek-chat 作为配置名，但在 run.sh 中会启用 Haiku Shim 运行时劫持。"
            echo "# 原因：必须让 Claude Code 认为自己在用 Haiku 才能 100% 禁用 Thinking。"
            echo "# 最终效果：使用 V3 模型，但零 Reasoner 费用。"
            echo "ANTHROPIC_MODEL=deepseek-chat"
            echo "ANTHROPIC_SMALL_FAST_MODEL=deepseek-chat"
            echo "ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-chat"
            echo "ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-chat"
            echo "ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-chat"
        elif [[ "${model}" == "deepseek-reasoner" ]]; then
            echo "# [DeepSeek Pure Reasoner 模式]"
            echo "# 全链路使用 DeepSeek R1 推理模型，成本最高，推理能力最强"
            echo "ANTHROPIC_MODEL=deepseek-reasoner"
            echo "ANTHROPIC_SMALL_FAST_MODEL=deepseek-reasoner"
            echo "ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-reasoner"
            echo "ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-reasoner"
            echo "ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-reasoner"
        elif [[ "${model}" == "deepseek-hybrid" ]]; then
            echo "# [DeepSeek Hybrid 混合模式]"
            echo "# 大脑 (Opus/Main) 使用 R1 进行复杂规划"
            echo "# 手脚 (Sonnet/Haiku) 使用 V3 (via Haiku Shim) 进行快速执行"
            echo "# 平衡了推理能力与执行成本"
            echo "ANTHROPIC_MODEL=deepseek-reasoner"
            echo "ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-reasoner"
            echo "ANTHROPIC_SMALL_FAST_MODEL=deepseek-chat"
            echo "ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-chat"
            echo "ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-chat"
        fi
    } >> "$CONFIG_FILE"
    append_config_common 600000
    log_ok "已配置为 DeepSeek (${model}，Anthropic 兼容，按官方文档）"
    log_info "BASE_URL: https://api.deepseek.com/anthropic"
}

# --- 提供商: 自定义 ---
write_custom_config() {
    local base_url="$1"
    local api_key="$2"

    write_config_header "自定义"
    {
        echo "MODEL_PROVIDER=custom"
        echo "ANTHROPIC_BASE_URL=$base_url"
        echo "ANTHROPIC_API_KEY=$api_key"
    } >> "$CONFIG_FILE"
    append_config_common 3000000
    log_ok "已配置为自定义模型"
    log_info "BASE_URL: $base_url"
}

# ============ MCP 工具配置 ============
configure_mcp_tools() {
    echo "是否安装 Playwright MCP（浏览器自动化测试）？"
    echo ""
    echo "  Playwright MCP 由微软官方维护 (github.com/microsoft/playwright-mcp)"
    echo "  提供 browser_click、browser_snapshot 等 25+ 浏览器自动化工具"
    echo "  适用于有 Web 前端的项目，Agent 可用它做端到端测试"
    echo ""
    echo "  1) 是 - 安装 Playwright MCP（项目有 Web 前端）"
    echo "  2) 否 - 跳过（纯后端 / CLI 项目，不需要浏览器测试）"
    echo ""

    local mcp_choice
    while true; do
        read -p "选择 [1-2]: " mcp_choice
        case $mcp_choice in
            1|2) break ;;
            *) echo "请输入 1 或 2" ;;
        esac
    done

    if [ "$mcp_choice" = "1" ]; then
        # 将 MCP 配置追加到 config.env
        echo "" >> "$CONFIG_FILE"
        echo "# MCP 工具配置" >> "$CONFIG_FILE"
        echo "MCP_PLAYWRIGHT=true" >> "$CONFIG_FILE"

        # 尝试为 Claude CLI 安装 Playwright MCP
        if command -v claude &> /dev/null; then
            log_info "为 Claude Code CLI 安装 Playwright MCP ..."
            if claude mcp add playwright npx @playwright/mcp@latest 2>/dev/null; then
                log_ok "Playwright MCP 已添加到 Claude Code"
            else
                log_warn "自动安装失败，请手动执行:"
                log_warn "  claude mcp add playwright npx @playwright/mcp@latest"
            fi
        else
            log_info "未检测到 claude CLI，跳过自动安装"
        fi

        echo ""
        log_info "如果你使用 Cursor IDE，还需要在 Cursor 中手动添加:"
        log_info "  Cursor Settings → MCP → Add new MCP Server"
        log_info "  Name: playwright"
        log_info "  Command: npx @playwright/mcp@latest"

        log_ok "Playwright MCP 配置完成"
    else
        # 记录未启用
        echo "" >> "$CONFIG_FILE"
        echo "# MCP 工具配置" >> "$CONFIG_FILE"
        echo "MCP_PLAYWRIGHT=false" >> "$CONFIG_FILE"

        log_info "已跳过 Playwright MCP 安装"
    fi

    # 第三步：Claude 调试输出
    echo ""
    echo "是否开启 Claude 调试输出（便于排查问题，输出较多）？"
    echo ""
    echo "  1) 否 - 静默（默认，推荐）"
    echo "  2) 是 - verbose（完整每轮输出）"
    echo "  3) 是 - mcp（MCP 调用，如 Playwright Click）"
    echo ""

    local debug_choice
    while true; do
        read -p "选择 [1-3，默认 1]: " debug_choice
        debug_choice="${debug_choice:-1}"
        case $debug_choice in
            1|2|3) break ;;
            *) echo "请输入 1-3" ;;
        esac
    done

    echo "" >> "$CONFIG_FILE"
    echo "# Claude 调试（config.env 中可随时修改）" >> "$CONFIG_FILE"
    case $debug_choice in
        2) echo "CLAUDE_DEBUG=verbose" >> "$CONFIG_FILE"; log_info "已启用 CLAUDE_DEBUG=verbose" ;;
        3) echo "CLAUDE_DEBUG=mcp" >> "$CONFIG_FILE"; log_info "已启用 CLAUDE_DEBUG=mcp" ;;
        *) echo "# CLAUDE_DEBUG=verbose  # 取消注释可开启" >> "$CONFIG_FILE" ;;
    esac
}

# ============ 确保 .gitignore 包含 config.env ============
ensure_gitignore() {
    local gitignore="$PROJECT_ROOT/.gitignore"

    # 检查 config.env 是否已在 .gitignore 中
    if [ -f "$gitignore" ]; then
        if grep -q "claude-auto-loop/config.env" "$gitignore" 2>/dev/null; then
            return  # 已存在，无需添加
        fi
    fi

    # 追加到 .gitignore
    echo "" >> "$gitignore"
    echo "# Claude Auto Loop 模型配置（含 API Key）" >> "$gitignore"
    echo "claude-auto-loop/config.env" >> "$gitignore"
    log_info "已将 config.env 添加到 .gitignore"
}

# ============ 入口 ============
main
