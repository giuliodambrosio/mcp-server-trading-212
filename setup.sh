#!/usr/bin/env bash

# MCP Server for 212 Trading - interactive setup script
# - Installs dependencies
# - Optionally creates/updates .env interactively
# - Optionally updates Claude Desktop MCP config idempotently

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

USE_UV=false
PYTHON_CMD="python3"
PYTHON_VERSION=""
NON_INTERACTIVE=false
SKIP_INSTALL=false
SKIP_VALIDATION=false
UPDATE_CLAUDE_CONFIG_MODE="ask"  # ask|auto|skip
CLAUDE_CONFIG_DIR="${HOME}/Library/Application Support/Claude"

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

redact_value() {
    local value="$1"
    local len=${#value}
    if [ "$len" -le 4 ]; then
        echo "****"
        return
    fi
    local prefix="${value:0:2}"
    local suffix="${value: -2}"
    echo "${prefix}***${suffix}"
}

print_redacted_env_file() {
    local file="$1"
    if [ ! -f "$file" ]; then
        return
    fi
    while IFS= read -r line || [ -n "$line" ]; do
        if [[ "$line" != *=* ]]; then
            echo "$line"
            continue
        fi
        local key="${line%%=*}"
        local value="${line#*=}"
        case "$key" in
            212_API_KEY_SECRET|212_API_KEY_ID|212_*_API_KEY_ID|212_*_API_KEY_SECRET)
                echo "${key}=$(redact_value "$value")"
                ;;
            *)
                echo "$line"
                ;;
        esac
    done < "$file"
}

usage() {
    cat <<USAGE
Usage: ./setup.sh [options]

Options:
  --claude-config-dir <path>     Override Claude config directory (default: ~/Library/Application Support/Claude)
  --update-claude-config <mode>  One of: ask, auto, skip (default: ask)
  --non-interactive              Do not prompt; keep existing .env and proceed with defaults
  --skip-install                 Skip dependency installation step
  --skip-validation              Skip runtime import validation
  --help                         Show this help

Examples:
  ./setup.sh
  ./setup.sh --update-claude-config auto
  ./setup.sh --claude-config-dir /tmp/claude-test --update-claude-config auto --non-interactive
USAGE
}

parse_args() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --claude-config-dir)
                shift
                if [ $# -eq 0 ]; then
                    print_error "Missing value for --claude-config-dir"
                    exit 1
                fi
                CLAUDE_CONFIG_DIR="$1"
                ;;
            --update-claude-config)
                shift
                if [ $# -eq 0 ]; then
                    print_error "Missing value for --update-claude-config"
                    exit 1
                fi
                case "$1" in
                    ask|auto|skip) UPDATE_CLAUDE_CONFIG_MODE="$1" ;;
                    *)
                        print_error "Invalid --update-claude-config value: $1"
                        exit 1
                        ;;
                esac
                ;;
            --non-interactive)
                NON_INTERACTIVE=true
                ;;
            --skip-install)
                SKIP_INSTALL=true
                ;;
            --skip-validation)
                SKIP_VALIDATION=true
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                print_error "Unknown argument: $1"
                usage
                exit 1
                ;;
        esac
        shift
    done
}

require_non_empty() {
    local value="$1"
    local label="$2"
    if [ -z "$value" ]; then
        print_error "$label cannot be empty"
        exit 1
    fi
}

get_env_value() {
    local key="$1"
    local file="$2"
    if [ -f "$file" ]; then
        local line
        line=$(grep -E "^${key}=" "$file" 2>/dev/null | tail -n 1 || true)
        if [ -n "$line" ]; then
            echo "${line#*=}"
            return 0
        fi
    fi
    echo ""
}

check_python() {
    print_status "Checking Python version..."

    local required_version="3.14"

    if command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD="python3"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed. Please install Python ${required_version}+ and retry."
        exit 1
    fi

    PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [ "$(printf '%s\n' "$required_version" "$PYTHON_VERSION" | sort -V | head -n1)" != "$required_version" ]; then
        print_error "Python ${required_version}+ is required, but found ${PYTHON_VERSION}"
        exit 1
    fi

    print_success "Python ${PYTHON_VERSION} found"
}

check_uv() {
    print_status "Checking for uv package manager..."

    if command -v uv >/dev/null 2>&1; then
        USE_UV=true
        print_success "uv found"
    else
        USE_UV=false
        print_warning "uv not found. Install: https://docs.astral.sh/uv/getting-started/installation/"
        print_status "Falling back to pip"
    fi
}

install_dependencies() {
    if [ "$SKIP_INSTALL" = true ]; then
        print_warning "Skipping dependency installation (--skip-install)"
        return
    fi

    print_status "Installing dependencies..."

    if [ "$USE_UV" = true ]; then
        uv sync
        print_success "Dependencies installed with uv"
    else
        "$PYTHON_CMD" -m pip install --upgrade pip
        "$PYTHON_CMD" -m pip install -e .
        print_success "Dependencies installed with pip"
    fi
}

normalize_accounts_csv() {
    local raw="$1"
    local normalized=""
    local seen_isa=false
    local seen_invest=false
    local token=""

    IFS=',' read -r -a parts <<< "$raw"
    for part in "${parts[@]}"; do
        token="${part#"${part%%[![:space:]]*}"}"
        token="${token%"${token##*[![:space:]]}"}"
        if [ -z "$token" ]; then
            continue
        fi
        token="$(echo "$token" | tr '[:upper:]' '[:lower:]')"
        case "$token" in
            isa)
                if [ "$seen_isa" = false ]; then
                    normalized="${normalized:+${normalized},}isa"
                    seen_isa=true
                fi
                ;;
            invest)
                if [ "$seen_invest" = false ]; then
                    normalized="${normalized:+${normalized},}invest"
                    seen_invest=true
                fi
                ;;
            *)
                print_error "Unsupported account alias '${token}'. Supported values: isa, invest"
                return 1
                ;;
        esac
    done

    if [ -z "$normalized" ]; then
        print_error "At least one account must be selected (isa and/or invest)."
        return 1
    fi

    echo "$normalized"
}

account_selected() {
    local accounts_csv="$1"
    local account="$2"
    [[ ",${accounts_csv}," == *",${account},"* ]]
}

prompt_env_configuration() {
    local env_file=".env"
    local existing_accounts=""
    local existing_default_account=""
    local existing_isa_key_id=""
    local existing_isa_key_secret=""
    local existing_isa_live_url=""
    local existing_invest_key_id=""
    local existing_invest_key_secret=""
    local existing_invest_live_url=""

    existing_accounts=$(get_env_value "212_ACCOUNTS" "$env_file")
    existing_default_account=$(get_env_value "212_DEFAULT_ACCOUNT" "$env_file")

    # Backfill ISA defaults from legacy single-account keys when present.
    existing_isa_key_id=$(get_env_value "212_ISA_API_KEY_ID" "$env_file")
    if [ -z "$existing_isa_key_id" ]; then
        existing_isa_key_id=$(get_env_value "212_API_KEY_ID" "$env_file")
    fi

    existing_isa_key_secret=$(get_env_value "212_ISA_API_KEY_SECRET" "$env_file")
    if [ -z "$existing_isa_key_secret" ]; then
        existing_isa_key_secret=$(get_env_value "212_API_KEY_SECRET" "$env_file")
    fi

    existing_isa_live_url=$(get_env_value "212_ISA_API_BASE_LIVE_URL" "$env_file")
    if [ -z "$existing_isa_live_url" ]; then
        existing_isa_live_url=$(get_env_value "212_API_BASE_LIVE_URL" "$env_file")
    fi

    existing_invest_key_id=$(get_env_value "212_INVEST_API_KEY_ID" "$env_file")
    existing_invest_key_secret=$(get_env_value "212_INVEST_API_KEY_SECRET" "$env_file")
    existing_invest_live_url=$(get_env_value "212_INVEST_API_BASE_LIVE_URL" "$env_file")

    print_status "Configuring .env file"
    echo "Create your Trading 212 API key here:"
    echo "https://helpcentre.trading212.com/hc/en-us/articles/14584770928157-Trading-212-API-key"
    echo ""

    if [ "$NON_INTERACTIVE" = true ] || [ ! -t 0 ]; then
        print_warning "Non-interactive mode: skipping .env prompts"
        if [ ! -f "$env_file" ] && [ -f ".env.template" ]; then
            cp .env.template "$env_file"
            print_warning "Created .env from template. Fill credentials manually."
        fi
        return
    fi

    local overwrite_choice="y"
    if [ -f "$env_file" ]; then
        echo "Current .env values (redacted):"
        print_redacted_env_file "$env_file"
        echo ""
        read -r -p "A .env file already exists. Overwrite it interactively? [y/N]: " overwrite_choice
        overwrite_choice=${overwrite_choice:-N}
    fi

    if [[ ! "$overwrite_choice" =~ ^[Yy]$ ]]; then
        print_status "Keeping existing .env"
        return
    fi

    local accounts_csv="${existing_accounts:-isa,invest}"
    local input_accounts=""
    read -r -p "212_ACCOUNTS [${accounts_csv}] (allowed: isa,invest): " input_accounts
    accounts_csv=$(normalize_accounts_csv "${input_accounts:-$accounts_csv}") || exit 1

    local default_account="${existing_default_account}"
    if [ -z "$default_account" ] || ! account_selected "$accounts_csv" "$default_account"; then
        default_account="${accounts_csv%%,*}"
    fi
    local input_default_account=""
    read -r -p "212_DEFAULT_ACCOUNT [${default_account}]: " input_default_account
    default_account="$(echo "${input_default_account:-$default_account}" | tr '[:upper:]' '[:lower:]')"
    if ! account_selected "$accounts_csv" "$default_account"; then
        print_error "212_DEFAULT_ACCOUNT must be one of 212_ACCOUNTS."
        exit 1
    fi

    local isa_key_id="${existing_isa_key_id}"
    local isa_key_secret="${existing_isa_key_secret}"
    local isa_live_url="${existing_isa_live_url:-https://live.trading212.com/api/v0/}"

    local invest_key_id="${existing_invest_key_id}"
    local invest_key_secret="${existing_invest_key_secret}"
    local invest_live_url="${existing_invest_live_url:-https://live.trading212.com/api/v0/}"

    if account_selected "$accounts_csv" "isa"; then
        echo ""
        echo "Configure ISA account credentials:"
        read -r -p "212_ISA_API_KEY_ID [${isa_key_id:-required}]: " input_isa_key_id
        isa_key_id=${input_isa_key_id:-$isa_key_id}
        require_non_empty "$isa_key_id" "212_ISA_API_KEY_ID"

        if [ -n "$isa_key_secret" ]; then
            read -r -s -p "212_ISA_API_KEY_SECRET [press Enter to keep current]: " input_isa_key_secret
            echo ""
            isa_key_secret=${input_isa_key_secret:-$isa_key_secret}
        else
            read -r -s -p "212_ISA_API_KEY_SECRET [required]: " input_isa_key_secret
            echo ""
            isa_key_secret="$input_isa_key_secret"
        fi
        require_non_empty "$isa_key_secret" "212_ISA_API_KEY_SECRET"

        read -r -p "212_ISA_API_BASE_LIVE_URL [${isa_live_url}]: " input_isa_live_url
        isa_live_url=${input_isa_live_url:-$isa_live_url}
        require_non_empty "$isa_live_url" "212_ISA_API_BASE_LIVE_URL"
    fi

    if account_selected "$accounts_csv" "invest"; then
        echo ""
        echo "Configure Invest account credentials:"
        read -r -p "212_INVEST_API_KEY_ID [${invest_key_id:-required}]: " input_invest_key_id
        invest_key_id=${input_invest_key_id:-$invest_key_id}
        require_non_empty "$invest_key_id" "212_INVEST_API_KEY_ID"

        if [ -n "$invest_key_secret" ]; then
            read -r -s -p "212_INVEST_API_KEY_SECRET [press Enter to keep current]: " input_invest_key_secret
            echo ""
            invest_key_secret=${input_invest_key_secret:-$invest_key_secret}
        else
            read -r -s -p "212_INVEST_API_KEY_SECRET [required]: " input_invest_key_secret
            echo ""
            invest_key_secret="$input_invest_key_secret"
        fi
        require_non_empty "$invest_key_secret" "212_INVEST_API_KEY_SECRET"

        read -r -p "212_INVEST_API_BASE_LIVE_URL [${invest_live_url}]: " input_invest_live_url
        invest_live_url=${input_invest_live_url:-$invest_live_url}
        require_non_empty "$invest_live_url" "212_INVEST_API_BASE_LIVE_URL"
    fi

    echo ""
    echo "New .env values to be written (redacted):"
    echo "212_ACCOUNTS=${accounts_csv}"
    echo "212_DEFAULT_ACCOUNT=${default_account}"
    if account_selected "$accounts_csv" "isa"; then
        echo "212_ISA_API_KEY_ID=$(redact_value "$isa_key_id")"
        echo "212_ISA_API_KEY_SECRET=$(redact_value "$isa_key_secret")"
        echo "212_ISA_API_BASE_LIVE_URL=${isa_live_url}"
    fi
    if account_selected "$accounts_csv" "invest"; then
        echo "212_INVEST_API_KEY_ID=$(redact_value "$invest_key_id")"
        echo "212_INVEST_API_KEY_SECRET=$(redact_value "$invest_key_secret")"
        echo "212_INVEST_API_BASE_LIVE_URL=${invest_live_url}"
    fi
    echo ""

    local write_choice="Y"
    read -r -p "Write these values to .env? [Y/n]: " write_choice
    write_choice=${write_choice:-Y}
    if [[ ! "$write_choice" =~ ^[Yy]$ ]]; then
        print_warning "Skipped writing .env"
        return
    fi

    {
        echo "212_ACCOUNTS=${accounts_csv}"
        echo "212_DEFAULT_ACCOUNT=${default_account}"
        echo ""
        if account_selected "$accounts_csv" "isa"; then
            echo "212_ISA_API_KEY_ID=${isa_key_id}"
            echo "212_ISA_API_KEY_SECRET=${isa_key_secret}"
            echo "212_ISA_API_BASE_LIVE_URL=${isa_live_url}"
            echo ""
        fi
        if account_selected "$accounts_csv" "invest"; then
            echo "212_INVEST_API_KEY_ID=${invest_key_id}"
            echo "212_INVEST_API_KEY_SECRET=${invest_key_secret}"
            echo "212_INVEST_API_BASE_LIVE_URL=${invest_live_url}"
        fi
    } > "$env_file"

    chmod 600 "$env_file" || true
    print_success "Wrote ${env_file}"
}

test_installation() {
    if [ "$SKIP_VALIDATION" = true ]; then
        print_warning "Skipping runtime validation (--skip-validation)"
        return
    fi

    print_status "Validating installation..."

    if [ ! -f "main.py" ]; then
        print_error "main.py not found"
        exit 1
    fi

    if [ "$USE_UV" = true ]; then
        if uv run python -c "import mcp, httpx, dotenv" >/dev/null 2>&1; then
            print_success "Runtime imports are valid via uv"
        else
            print_error "Import check failed via uv runtime"
            exit 1
        fi
    else
        if "$PYTHON_CMD" -c "import mcp, httpx, dotenv" >/dev/null 2>&1; then
            print_success "Runtime imports are valid"
        else
            print_error "Import check failed in current Python environment"
            exit 1
        fi
    fi
}

print_desired_claude_entry() {
    local cwd
    cwd="$(pwd)"

    if [ "$USE_UV" = true ]; then
        cat <<JSON
{
  "command": "uv",
  "args": [
    "--directory",
    "${cwd}",
    "run",
    "main.py"
  ]
}
JSON
    else
        local env_accounts env_default
        local env_isa_key_id env_isa_key_secret env_isa_live_url
        local env_invest_key_id env_invest_key_secret env_invest_live_url
        env_accounts=$(get_env_value "212_ACCOUNTS" ".env")
        env_default=$(get_env_value "212_DEFAULT_ACCOUNT" ".env")
        env_isa_key_id=$(get_env_value "212_ISA_API_KEY_ID" ".env")
        env_isa_key_secret=$(get_env_value "212_ISA_API_KEY_SECRET" ".env")
        env_isa_live_url=$(get_env_value "212_ISA_API_BASE_LIVE_URL" ".env")
        env_invest_key_id=$(get_env_value "212_INVEST_API_KEY_ID" ".env")
        env_invest_key_secret=$(get_env_value "212_INVEST_API_KEY_SECRET" ".env")
        env_invest_live_url=$(get_env_value "212_INVEST_API_BASE_LIVE_URL" ".env")

        cat <<JSON
{
  "command": "${PYTHON_CMD}",
  "args": ["${cwd}/main.py"],
  "env": {
    "212_ACCOUNTS": "${env_accounts:-isa,invest}",
    "212_DEFAULT_ACCOUNT": "${env_default:-isa}",
    "212_ISA_API_KEY_ID": "${env_isa_key_id:-your_isa_api_key_id}",
    "212_ISA_API_KEY_SECRET": "${env_isa_key_secret:-your_isa_api_secret}",
    "212_ISA_API_BASE_LIVE_URL": "${env_isa_live_url:-https://live.trading212.com/api/v0/}",
    "212_INVEST_API_KEY_ID": "${env_invest_key_id:-your_invest_api_key_id}",
    "212_INVEST_API_KEY_SECRET": "${env_invest_key_secret:-your_invest_api_secret}",
    "212_INVEST_API_BASE_LIVE_URL": "${env_invest_live_url:-https://live.trading212.com/api/v0/}"
  }
}
JSON
    fi
}

update_claude_config() {
    if [ "$UPDATE_CLAUDE_CONFIG_MODE" = "skip" ]; then
        print_warning "Skipping Claude config update (--update-claude-config skip)"
        return
    fi

    local config_dir="$CLAUDE_CONFIG_DIR"
    local config_file="${config_dir}/claude_desktop_config.json"
    local cwd
    cwd="$(pwd)"

    mkdir -p "$config_dir"

    print_status "Preparing Claude config update at: ${config_file}"

    if [ "$UPDATE_CLAUDE_CONFIG_MODE" = "ask" ] && [ "$NON_INTERACTIVE" = false ] && [ -t 0 ]; then
        echo "Planned entry for mcpServers.212-trading:"
        print_desired_claude_entry
        echo ""
        read -r -p "Update Claude config now? [Y/n]: " update_choice
        update_choice=${update_choice:-Y}
        if [[ ! "$update_choice" =~ ^[Yy]$ ]]; then
            print_warning "Skipped Claude config update"
            return
        fi
    fi

    local result
    result=$(CONFIG_FILE="$config_file" CWD="$cwd" USE_UV="$USE_UV" PYTHON_CMD="$PYTHON_CMD" python3 - <<'PY'
import json
import os
from pathlib import Path


def read_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()
    return data


config_file = Path(os.environ["CONFIG_FILE"])
cwd = os.environ["CWD"]
use_uv = os.environ.get("USE_UV", "false").lower() == "true"
py_cmd = os.environ.get("PYTHON_CMD", "python3")
env_data = read_env(Path(".env"))

if config_file.exists():
    try:
        root = json.loads(config_file.read_text(encoding="utf-8"))
        if not isinstance(root, dict):
            root = {}
    except Exception:
        root = {}
else:
    root = {}

mcp_servers = root.get("mcpServers")
if not isinstance(mcp_servers, dict):
    mcp_servers = {}

if use_uv:
    desired = {
        "command": "uv",
        "args": ["--directory", cwd, "run", "main.py"],
    }
else:
    desired = {
        "command": py_cmd,
        "args": [f"{cwd}/main.py"],
        "env": {
            "212_ACCOUNTS": env_data.get("212_ACCOUNTS", "isa,invest"),
            "212_DEFAULT_ACCOUNT": env_data.get("212_DEFAULT_ACCOUNT", "isa"),
            "212_ISA_API_KEY_ID": env_data.get("212_ISA_API_KEY_ID", "your_isa_api_key_id"),
            "212_ISA_API_KEY_SECRET": env_data.get("212_ISA_API_KEY_SECRET", "your_isa_api_secret"),
            "212_ISA_API_BASE_LIVE_URL": env_data.get("212_ISA_API_BASE_LIVE_URL", "https://live.trading212.com/api/v0/"),
            "212_INVEST_API_KEY_ID": env_data.get("212_INVEST_API_KEY_ID", "your_invest_api_key_id"),
            "212_INVEST_API_KEY_SECRET": env_data.get("212_INVEST_API_KEY_SECRET", "your_invest_api_secret"),
            "212_INVEST_API_BASE_LIVE_URL": env_data.get("212_INVEST_API_BASE_LIVE_URL", "https://live.trading212.com/api/v0/"),
        },
    }

existing = mcp_servers.get("212-trading")
if existing == desired:
    print("UNCHANGED")
else:
    status = "UPDATED" if existing is not None else "CREATED"
    mcp_servers["212-trading"] = desired
    root["mcpServers"] = mcp_servers
    config_file.write_text(json.dumps(root, indent=2) + "\n", encoding="utf-8")
    print(status)
PY
)

    case "$result" in
        UNCHANGED)
            print_success "Claude config already up to date (idempotent)"
            ;;
        CREATED)
            print_success "Claude config updated (added mcpServers.212-trading)"
            ;;
        UPDATED)
            print_success "Claude config updated (refreshed mcpServers.212-trading)"
            ;;
        *)
            print_warning "Claude config update result: ${result}"
            ;;
    esac
}

show_next_steps() {
    local cwd
    cwd="$(pwd)"

    echo ""
    echo "Setup completed successfully"
    echo ""
    echo "Next steps:"
    echo "1. Confirm .env values are correct."
    echo "2. Restart Claude Desktop."
    echo "3. Test by asking: Show me my account balance"
    echo ""
    echo "Claude config file used: ${CLAUDE_CONFIG_DIR}/claude_desktop_config.json"
    echo ""
    echo "Reference links:"
    echo "- Trading 212 API key help: https://helpcentre.trading212.com/hc/en-us/articles/14584770928157-Trading-212-API-key"
    echo "- uv installation: https://docs.astral.sh/uv/getting-started/installation/"
    echo ""
    echo "Current recommended MCP entry for 212-trading:"
    print_desired_claude_entry
}

main() {
    parse_args "$@"

    echo "Setting up MCP Server for 212 Trading"
    echo "=========================================="
    echo "  MCP Server for 212 Trading Setup"
    echo "=========================================="
    echo ""

    check_python
    check_uv
    install_dependencies
    prompt_env_configuration
    test_installation
    update_claude_config
    show_next_steps
}

main "$@"
