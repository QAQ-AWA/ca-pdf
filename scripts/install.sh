#!/usr/bin/env bash
set -Eeuo pipefail

if [[ -z "${BASH_VERSION:-}" || "${BASH_VERSINFO[0]}" -lt 4 ]]; then
  echo "[错误] 安装器需要 Bash 4.0 及以上版本" >&2
  exit 1
fi

umask 022

if [[ -t 1 ]]; then
  BOLD="\033[1m"
  GREEN="\033[32m"
  RED="\033[31m"
  YELLOW="\033[33m"
  BLUE="\033[34m"
  RESET="\033[0m"
else
  BOLD=""
  GREEN=""
  RED=""
  YELLOW=""
  BLUE=""
  RESET=""
fi

log_step() {
  printf "%b==> %s%b\n" "${BOLD}${BLUE}" "$1" "${RESET}"
}

log_info() {
  printf "%bℹ%b %s\n" "${BLUE}" "${RESET}" "$1"
}

log_warn() {
  printf "%b⚠%b %s\n" "${YELLOW}" "${RESET}" "$1"
}

log_error() {
  printf "%b✖%b %s\n" "${RED}" "${RESET}" "$1"
}

log_success() {
  printf "%b✔%b %s\n" "${GREEN}" "${RESET}" "$1"
}

on_error() {
  local exit_code=$?
  local line_no=${1:-unknown}
  log_error "安装过程在第 ${line_no} 行失败（退出码 ${exit_code}）。"
  log_error "请查看日志文件了解详情：${LOG_FILE:-未创建}" >&2
  exit ${exit_code}
}

trap 'on_error "$LINENO"' ERR

if [[ ${EUID} -ne 0 ]]; then
  if command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
  else
    log_error "当前用户非 root，且系统未安装 sudo，请切换到 root 用户后重新执行。"
    exit 1
  fi
else
  SUDO=""
fi

INSTALL_USER=$(id -un)
INSTALL_GROUP=$(id -gn)
INSTALL_ROOT=${CAPDF_HOME:-/opt/ca-pdf}
CAPDF_REMOTE_REPO=${CAPDF_REMOTE_REPO:-QAQ-AWA/ca-pdf}
CAPDF_CHANNEL=${CAPDF_CHANNEL:-main}
RAW_BASE_URL="https://raw.githubusercontent.com/${CAPDF_REMOTE_REPO}/${CAPDF_CHANNEL}"
SCRIPTS_DIR="${INSTALL_ROOT}/scripts"
LOG_DIR="${INSTALL_ROOT}/logs"
BACKUP_DIR="${INSTALL_ROOT}/backups"
LOG_FILE="${LOG_DIR}/installer-$(date +%Y%m%d).log"
LAUNCHER_PATH="/usr/local/bin/capdf"
LEGACY_LAUNCHER_PATH="/usr/local/bin/ca-pdf"
PKG_MANAGER=""
UPDATED_INDEX=0

ensure_directories() {
  ${SUDO} mkdir -p "${SCRIPTS_DIR}" "${LOG_DIR}" "${BACKUP_DIR}"
  ${SUDO} touch "${LOG_FILE}"
  ${SUDO} chown "${INSTALL_USER}:${INSTALL_GROUP}" "${INSTALL_ROOT}" "${SCRIPTS_DIR}" "${LOG_DIR}" "${BACKUP_DIR}" "${LOG_FILE}" >/dev/null 2>&1 || true
}

detect_package_manager() {
  if command -v apt-get >/dev/null 2>&1; then
    PKG_MANAGER="apt"
  elif command -v dnf >/dev/null 2>&1; then
    PKG_MANAGER="dnf"
  elif command -v yum >/dev/null 2>&1; then
    PKG_MANAGER="yum"
  elif command -v zypper >/dev/null 2>&1; then
    PKG_MANAGER="zypper"
  elif command -v pacman >/dev/null 2>&1; then
    PKG_MANAGER="pacman"
  else
    PKG_MANAGER=""
  fi

  if [[ -z "${PKG_MANAGER}" ]]; then
    log_warn "未能识别当前发行版的包管理器。"
    log_warn "请手动安装以下依赖后重新运行脚本：curl、git、jq、openssl、tar、docker、docker compose。"
    exit 1
  fi
}

update_package_index() {
  if [[ ${UPDATED_INDEX} -eq 1 ]]; then
    return
  fi
  case "${PKG_MANAGER}" in
    apt)
      ${SUDO} apt-get update -y
      ;;
    dnf)
      ${SUDO} dnf makecache -y
      ;;
    yum)
      ${SUDO} yum makecache -y
      ;;
    zypper)
      ${SUDO} zypper refresh
      ;;
    pacman)
      ${SUDO} pacman -Sy --noconfirm
      ;;
  esac
  UPDATED_INDEX=1
}

install_packages() {
  local packages=("$@")
  case "${PKG_MANAGER}" in
    apt)
      ${SUDO} DEBIAN_FRONTEND=noninteractive apt-get install -y "${packages[@]}"
      ;;
    dnf)
      ${SUDO} dnf install -y "${packages[@]}"
      ;;
    yum)
      ${SUDO} yum install -y "${packages[@]}"
      ;;
    zypper)
      ${SUDO} zypper install -y "${packages[@]}"
      ;;
    pacman)
      ${SUDO} pacman -S --noconfirm --needed "${packages[@]}"
      ;;
  esac
}

ensure_command() {
  local cmd="$1"
  local package_name=${2:-$1}
  if command -v "${cmd}" >/dev/null 2>&1; then
    return
  fi
  log_step "安装依赖 ${package_name}"
  update_package_index
  install_packages "${package_name}"
}

install_docker() {
  if command -v docker >/dev/null 2>&1; then
    return
  fi
  log_step "安装 Docker"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com | ${SUDO} sh
  else
    update_package_index
    case "${PKG_MANAGER}" in
      apt)
        install_packages docker.io
        ;;
      dnf|yum)
        install_packages docker
        ;;
      zypper)
        install_packages docker
        ;;
      pacman)
        install_packages docker
        ;;
    esac
  fi
  if ! command -v docker >/dev/null 2>&1; then
    log_error "Docker 安装失败，请检查网络或手动按照 https://docs.docker.com/engine/install/ 安装。"
    exit 1
  fi
}

ensure_docker_service() {
  if ! command -v systemctl >/dev/null 2>&1; then
    log_warn "当前环境未检测到 systemd，需确保 Docker 服务已手动启动。"
    return
  fi
  if ! systemctl is-active docker >/dev/null 2>&1; then
    log_info "启动 Docker 服务"
    ${SUDO} systemctl enable docker >/dev/null 2>&1 || true
    ${SUDO} systemctl start docker
  fi
}

ensure_compose_plugin() {
  if docker compose version >/dev/null 2>&1; then
    return
  fi
  if command -v docker-compose >/dev/null 2>&1; then
    log_warn "检测到 docker-compose V1，推荐升级到 Docker Compose V2。"
    return
  fi
  log_step "安装 Docker Compose 插件"
  case "${PKG_MANAGER}" in
    apt)
      update_package_index
      install_packages docker-compose-plugin
      ;;
    dnf|yum)
      update_package_index
      install_packages docker-compose-plugin
      ;;
    zypper)
      update_package_index
      install_packages docker-compose
      ;;
    pacman)
      update_package_index
      install_packages docker-compose
      ;;
    *)
      log_warn "请手动安装 Docker Compose V2。"
      ;;
  esac

  if ! docker compose version >/dev/null 2>&1; then
    log_warn "未能自动安装 Docker Compose V2，可访问 https://docs.docker.com/compose/install/ 手动安装。"
  fi
}

check_network() {
  if ! curl -fsSL --retry 3 --retry-delay 1 --retry-connrefused "${RAW_BASE_URL}/scripts/deploy.sh" >/dev/null 2>&1; then
    log_warn "无法从 ${RAW_BASE_URL} 获取安装资源。"
    log_warn "如果当前处于离线或代理环境，请配置好代理或手动下载脚本后重试。"
    exit 1
  fi
}

download_asset() {
  local remote_path="$1"
  local target_path="$2"
  local target_dir
  target_dir=$(dirname "${target_path}")
  mkdir -p "${target_dir}"
  curl -fsSL --retry 3 --retry-delay 1 --retry-connrefused "${RAW_BASE_URL}/${remote_path}" -o "${target_path}.tmp"
  mv "${target_path}.tmp" "${target_path}"
}

install_capdf_files() {
  log_step "下载管理脚本"
  download_asset "scripts/deploy.sh" "${SCRIPTS_DIR}/deploy.sh"
  chmod +x "${SCRIPTS_DIR}/deploy.sh"

  download_asset "scripts/install.sh" "${SCRIPTS_DIR}/install.sh"
  chmod +x "${SCRIPTS_DIR}/install.sh"

  log_step "同步模版文件"
  download_asset ".env.example" "${INSTALL_ROOT}/.env.example"
  download_asset ".env.docker.example" "${INSTALL_ROOT}/.env.docker.example"
  download_asset "docker-compose.yml" "${INSTALL_ROOT}/docker-compose.example.yml"
  log_success "模板文件已更新"
}

create_launcher() {
  log_step "创建 capdf 命令"
  local launcher_tmp
  launcher_tmp=$(mktemp)
  cat >"${launcher_tmp}" <<EOF
#!/usr/bin/env bash
set -Eeuo pipefail
export CAPDF_HOME="${INSTALL_ROOT}"
export CAPDF_CHANNEL="${CAPDF_CHANNEL}"
export CAPDF_REMOTE_REPO="${CAPDF_REMOTE_REPO}"
exec "${SCRIPTS_DIR}/deploy.sh" "\$@"
EOF
  ${SUDO} mv "${launcher_tmp}" "${LAUNCHER_PATH}"
  ${SUDO} chmod +x "${LAUNCHER_PATH}"
  if [[ -e "${LEGACY_LAUNCHER_PATH}" && ! -L "${LEGACY_LAUNCHER_PATH}" ]]; then
    ${SUDO} rm -f "${LEGACY_LAUNCHER_PATH}"
  fi
  if [[ ! -L "${LEGACY_LAUNCHER_PATH}" ]]; then
    ${SUDO} ln -sf "${LAUNCHER_PATH}" "${LEGACY_LAUNCHER_PATH}"
  fi
}

ensure_user_in_docker_group() {
  if id -nG "${INSTALL_USER}" | grep -qw docker; then
    return
  fi
  log_warn "当前用户 ${INSTALL_USER} 未加入 docker 用户组，后续可能需要 sudo 才能管理容器。"
  log_warn "可执行以下命令后重新登录生效："
  printf "  %s sudo usermod -aG docker %s%s\n" "${BOLD}" "${INSTALL_USER}" "${RESET}"
  log_warn "执行完命令后，请重新登录或重新加载 shell。"
}

run_initial_install() {
  if [[ "${CAPDF_SKIP_INSTALL:-0}" == "1" ]]; then
    log_info "已跳过自动部署，可稍后运行 capdf install。"
    return
  fi
  log_step "启动 ca-pdf 安装向导"
  "${SCRIPTS_DIR}/deploy.sh" install
}

main() {
  ensure_directories
  exec > >(tee -a "${LOG_FILE}") 2>&1

  log_step "初始化安装器"
  detect_package_manager
  ensure_command curl
  check_network
  ensure_command git
  ensure_command jq
  ensure_command openssl
  ensure_command tar
  ensure_command gzip

  install_docker
  ensure_docker_service
  ensure_compose_plugin
  ensure_user_in_docker_group

  install_capdf_files
  create_launcher

  log_success "管理脚本已安装至 ${INSTALL_ROOT}"
  log_info "现在可以通过命令 ${BOLD}capdf${RESET} 进入菜单化运维界面。"

  run_initial_install
  log_success "安装流程结束，如需再次操作请运行 capdf。"
}

main "$@"
