#!/usr/bin/env bash

set -euo pipefail

REPO_OWNER="lmaertin"
REPO_NAME="python-pooldose"
REPO_REF="${POOLDOSE_REPO_REF:-main}"
ARCHIVE_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/archive/refs/heads/${REPO_REF}.zip"

OS_NAME="$(uname -s)"
case "${OS_NAME}" in
    Darwin)
        DEFAULT_INSTALL_ROOT="${HOME}/Library/Application Support/python-pooldose"
        DEFAULT_LAUNCHER_PATH="${HOME}/Desktop/PoolDose.command"
        ;;
    Linux)
        DEFAULT_INSTALL_ROOT="${HOME}/.local/share/python-pooldose"
        DEFAULT_LAUNCHER_PATH="${HOME}/Desktop/PoolDose.sh"
        ;;
    *)
        echo "Unsupported operating system: ${OS_NAME}" >&2
        exit 1
        ;;
esac

INSTALL_ROOT="${POOLDOSE_INSTALL_ROOT:-${DEFAULT_INSTALL_ROOT}}"
SOURCE_DIR="${INSTALL_ROOT}/source"
VENV_DIR="${INSTALL_ROOT}/.venv"
LAUNCHER_PATH="${POOLDOSE_LAUNCHER_PATH:-${DEFAULT_LAUNCHER_PATH}}"

require_command() {
    local command_name="$1"
    if ! command -v "$command_name" >/dev/null 2>&1; then
        echo "Missing required command: ${command_name}" >&2
        exit 1
    fi
}

cleanup() {
    if [[ -n "${WORK_DIR:-}" && -d "${WORK_DIR}" ]]; then
        rm -rf "${WORK_DIR}"
    fi
}

create_launcher() {
    mkdir -p "$(dirname "${LAUNCHER_PATH}")"

    {
        printf '#!/usr/bin/env bash\n\n'
        printf 'set -u\n\n'
        printf 'INSTALL_ROOT=%q\n' "${INSTALL_ROOT}"
        printf 'VENV_DIR=%q\n\n' "${VENV_DIR}"
        cat <<'EOF'
if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
    echo "python-pooldose is not installed yet."
    echo "Please run the installer script again."
    read -r -p "Press Enter to close..." reply
    exit 1
fi

trim_quotes() {
    local value="$1"
    value="${value#\"}"
    value="${value%\"}"
    value="${value#\'}"
    value="${value%\'}"
    printf '%s' "${value}"
}

pause_if_requested() {
    if [[ "${POOLDOSE_NO_PAUSE:-0}" != "1" ]]; then
        read -r -p "Press Enter to close..." reply
    fi
}

to_lower() {
    printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

run_cli() {
    "${VENV_DIR}/bin/python" -m pooldose "$@"
}

if [[ "$#" -gt 0 ]]; then
    run_cli "$@"
    exit_code="$?"
    exit "${exit_code}"
fi

echo "python-pooldose launcher"
echo
echo "1) Connect to a device"
echo "2) Analyze a device"
echo "3) Use a mock JSON file"
echo "4) Show help"
echo
read -r -p "Choose an option [1-4]: " choice

case "${choice}" in
    1|2)
        read -r -p "Device IP address or hostname [kommspot]: " host
        if [[ -z "${host}" ]]; then
            host="kommspot"
        fi

        args=(--host "${host}")

        read -r -p "Use HTTPS? [y/N]: " ssl_reply
        ssl_reply_lc="$(to_lower "${ssl_reply}")"
        if [[ "${ssl_reply_lc}" == "y" || "${ssl_reply_lc}" == "yes" ]]; then
            args+=(--ssl)
        fi

        read -r -p "Custom port (optional): " port
        if [[ -n "${port}" ]]; then
            args+=(--port "${port}")
        fi

        if [[ "${choice}" == "2" ]]; then
            read -r -p "Include hidden widgets? [y/N]: " all_widgets
            all_widgets_lc="$(to_lower "${all_widgets}")"
            if [[ "${all_widgets_lc}" == "y" || "${all_widgets_lc}" == "yes" ]]; then
                args+=(--analyze-all)
            else
                args+=(--analyze)
            fi
        fi

        run_cli "${args[@]}"
        exit_code="$?"
        pause_if_requested
        exit "${exit_code}"
        ;;
    3)
        read -r -p "Path to mock JSON file: " mock_path
        mock_path="$(trim_quotes "${mock_path}")"
        if [[ -z "${mock_path}" ]]; then
            echo "A JSON file path is required."
            pause_if_requested
            exit 1
        fi

        run_cli --mock "${mock_path}"
        exit_code="$?"
        pause_if_requested
        exit "${exit_code}"
        ;;
    4)
        run_cli --help
        exit_code="$?"
        pause_if_requested
        exit "${exit_code}"
        ;;
    *)
        echo "Unknown option: ${choice}"
        pause_if_requested
        exit 1
        ;;
esac
EOF
    } > "${LAUNCHER_PATH}"

    chmod +x "${LAUNCHER_PATH}"
}

main() {
    require_command curl
    require_command unzip
    require_command python3

    WORK_DIR="$(mktemp -d)"
    trap cleanup EXIT

    ARCHIVE_PATH="${WORK_DIR}/source.zip"

    echo "Downloading latest source from GitHub..."
    curl -fsSL "${ARCHIVE_URL}" -o "${ARCHIVE_PATH}"

    echo "Preparing installation directories..."
    mkdir -p "${INSTALL_ROOT}"
    rm -rf "${SOURCE_DIR}"

    echo "Extracting source archive..."
    unzip -q "${ARCHIVE_PATH}" -d "${WORK_DIR}"
    EXTRACTED_DIR="${WORK_DIR}/${REPO_NAME}-${REPO_REF}"
    mv "${EXTRACTED_DIR}" "${SOURCE_DIR}"

    echo "Creating virtual environment..."
    python3 -m venv "${VENV_DIR}"

    echo "Installing python-pooldose..."
    "${VENV_DIR}/bin/python" -m pip install --upgrade pip setuptools wheel
    "${VENV_DIR}/bin/python" -m pip install --upgrade "${SOURCE_DIR}"

    echo "Creating launcher..."
    create_launcher

    echo
    echo "Installation completed."
    echo "Source: ${SOURCE_DIR}"
    echo "Launcher: ${LAUNCHER_PATH}"
    echo
    echo "Network access hint:"
    if [[ "${OS_NAME}" == "Darwin" ]]; then
        echo "  If macOS asks for Local Network access for Terminal/iTerm/Python, click Allow."
    else
        echo "  If Linux firewall rules are active, allow local network access for Terminal/Python."
    fi
    echo
    echo "You can now double-click the launcher in Finder or run:"
    echo "  ${LAUNCHER_PATH}"
}

main "$@"
