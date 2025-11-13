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

prompt_confirm() {
  local prompt_msg=${1:-"确认继续吗?"}
  local default_choice=${2:-"y"}
  local suffix="[y/N]"
  if [[ "${default_choice}" =~ ^([Yy])$ ]]; then
    suffix="[Y/n]"
  fi
  read -r -p "${prompt_msg} ${suffix} " response || true
  response=${response:-${default_choice}}
  [[ "${response}" =~ ^([Yy])$ ]]
}

on_error() {
  local exit_code=$?
  local line_no=${1:-unknown}
  log_error "安装过程在第 ${line_no} 行失败（退出码 ${exit_code}）。"
  log_error "请查看日志文件了解详情：${LOG_FILE:-未创建}" >&2
  exit ${exit_code}
}

trap 'on_error "$LINENO"' ERR

show_help() {
  cat <<EOF
用法: bash install.sh [选项]

ca-pdf 一键安装脚本 - 自托管 PDF 电子签章平台

选项:
  -h, --help              显示此帮助信息
  -v, --version          显示版本信息
  --skip-install          跳过初始安装向导（稍后手动运行 capdf install）
  --home DIR              自定义安装路径（默认: /opt/ca-pdf）
  --channel CHANNEL       指定 Git 分支（默认: main）
  --repo OWNER/REPO       指定 Git 仓库（默认: QAQ-AWA/ca-pdf）

环境变量:
  CAPDF_HOME              自定义安装路径
  CAPDF_CHANNEL          Git 分支名称（main/dev/其他）
  CAPDF_REMOTE_REPO      Git 仓库（格式: OWNER/REPO）
  CAPDF_SKIP_INSTALL     设为 1 跳过初始安装向导
  http_proxy/https_proxy  网络代理配置（如需要）

系统要求:
  操作系统: Linux（Ubuntu/Debian/CentOS/Rocky/AlmaLinux/openSUSE/Arch）
  内存: 至少 2GB RAM
  磁盘: 至少 5GB 可用空间
  网络: 需要访问 GitHub 和 Docker Hub
  权限: root 或具有 sudo 权限的用户

安装步骤:
  1. 系统预检查（资源、网络）
  2. 安装依赖（curl、git、jq、openssl、Docker）
  3. 克隆项目代码
  4. 创建管理命令 capdf
  5. 运行安装向导（交互式配置）

安装示例:
  # 基础安装（推荐）
  bash <(curl -fsSL https://raw.githubusercontent.com/QAQ-AWA/ca-pdf/main/scripts/install.sh)

  # 自定义安装路径
  CAPDF_HOME=/srv/ca-pdf bash <(curl -fsSL https://raw.githubusercontent.com/QAQ-AWA/ca-pdf/main/scripts/install.sh)

  # 从开发分支安装
  CAPDF_CHANNEL=dev bash <(curl -fsSL https://raw.githubusercontent.com/QAQ-AWA/ca-pdf/main/scripts/install.sh)

  # 仅安装脚本，稍后手动配置
  CAPDF_SKIP_INSTALL=1 bash <(curl -fsSL https://raw.githubusercontent.com/QAQ-AWA/ca-pdf/main/scripts/install.sh)

  # 国内用户配置代理
  export https_proxy=http://proxy.example.com:port
  bash <(curl -fsSL https://raw.githubusercontent.com/QAQ-AWA/ca-pdf/main/scripts/install.sh)

故障排查:
  如安装失败，请执行以下命令收集日志：
    capdf doctor           # 系统诊断
    capdf export-logs      # 导出诊断日志

  常见问题：
    1. 网络连接失败 -> 检查网络和 GitHub 访问，配置代理
    2. Docker 安装失败 -> 手动安装 Docker（https://docs.docker.com/engine/install/）
    3. 权限不足 -> 使用 sudo 或 root 用户运行
    4. 端口占用 -> 释放 80/443 端口

帮助与反馈:
  文档: https://github.com/QAQ-AWA/ca-pdf
  Issues: https://github.com/QAQ-AWA/ca-pdf/issues
  邮箱: 7780102@qq.com

EOF
}

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
 CAPDF_SKIP_INSTALL=${CAPDF_SKIP_INSTALL:-0}

 LAUNCHER_PATH="/usr/local/bin/capdf"
 LEGACY_LAUNCHER_PATH="/usr/local/bin/ca-pdf"
 PKG_MANAGER=""
 UPDATED_INDEX=0

ensure_directories() {
   ${SUDO} mkdir -p "${SCRIPTS_DIR}" "${LOG_DIR}" "${BACKUP_DIR}"
   ${SUDO} touch "${LOG_FILE}" || {
     log_error "无法创建日志文件 ${LOG_FILE}"
     return 1
   }
   ${SUDO} chmod 755 "${INSTALL_ROOT}" "${SCRIPTS_DIR}" "${LOG_DIR}" "${BACKUP_DIR}" 2>/dev/null || true
   ${SUDO} chmod 644 "${LOG_FILE}" 2>/dev/null || true
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
       DEBIAN_FRONTEND=noninteractive ${SUDO} apt-get install -y "${packages[@]}"
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
     return 0
   fi
   log_step "安装依赖 ${package_name}"
   update_package_index
   install_packages "${package_name}" || {
     log_error "无法安装 ${package_name}，请检查网络连接或包名是否正确。"
     return 1
   }
   if ! command -v "${cmd}" >/dev/null 2>&1; then
     log_error "安装完成但命令 ${cmd} 仍不可用。"
     return 1
   fi
   return 0
 }

install_docker() {
   if command -v docker >/dev/null 2>&1; then
     return 0
   fi
   log_step "安装 Docker"
   if command -v curl >/dev/null 2>&1; then
     curl -fsSL https://get.docker.com | ${SUDO} sh || {
       log_warn "Docker 脚本安装失败，尝试使用包管理器安装"
     }
   fi

   if ! command -v docker >/dev/null 2>&1; then
     log_step "使用包管理器安装 Docker"
     update_package_index
     case "${PKG_MANAGER}" in
       apt)
         install_packages docker.io || log_warn "docker.io 包安装失败"
         ;;
       dnf|yum)
         install_packages docker || log_warn "docker 包安装失败"
         ;;
       zypper)
         install_packages docker || log_warn "docker 包安装失败"
         ;;
       pacman)
         install_packages docker || log_warn "docker 包安装失败"
         ;;
     esac
   fi

   if ! command -v docker >/dev/null 2>&1; then
     log_error "Docker 安装失败，请检查网络或手动按照 https://docs.docker.com/engine/install/ 安装。"
     return 1
   fi
   return 0
 }

ensure_docker_service() {
   if ! command -v systemctl >/dev/null 2>&1; then
     log_warn "当前环境未检测到 systemd，需确保 Docker 服务已手动启动。"
     return 0
   fi
   if ! systemctl is-active docker >/dev/null 2>&1; then
     log_step "启动 Docker 服务"
     ${SUDO} systemctl enable docker >/dev/null 2>&1 || {
       log_warn "无法启用 Docker 自启动"
     }
     ${SUDO} systemctl start docker || {
       log_error "无法启动 Docker 服务"
       return 1
     }
   fi
   log_success "Docker 服务运行中"
   return 0
 }

ensure_compose_plugin() {
   if docker compose version >/dev/null 2>&1; then
     log_info "Docker Compose V2 已安装"
     return 0
   fi
   if command -v docker-compose >/dev/null 2>&1; then
     log_warn "检测到 Docker Compose V1，推荐升级到 Docker Compose V2。"
     return 0
   fi
   log_step "安装 Docker Compose 插件"
   case "${PKG_MANAGER}" in
     apt)
       update_package_index
       install_packages docker-compose-plugin || log_warn "docker-compose-plugin 包安装失败"
       ;;
     dnf|yum)
       update_package_index
       install_packages docker-compose-plugin || log_warn "docker-compose-plugin 包安装失败"
       ;;
     zypper)
       update_package_index
       install_packages docker-compose || log_warn "docker-compose 包安装失败"
       ;;
     pacman)
       update_package_index
       install_packages docker-compose || log_warn "docker-compose 包安装失败"
       ;;
     *)
       log_warn "未知包管理器，请手动安装 Docker Compose V2。"
       ;;
   esac

   if ! docker compose version >/dev/null 2>&1 && ! command -v docker-compose >/dev/null 2>&1; then
     log_warn "未能自动安装 Docker Compose，可访问 https://docs.docker.com/compose/install/ 手动安装。"
     return 1
   fi
   return 0
 }

check_network() {
   log_step "检查网络连接"
   
   if command -v ping >/dev/null 2>&1; then
     if ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1 || ping -c 1 -W 2 1.1.1.1 >/dev/null 2>&1; then
       log_success "基础网络连接正常"
     else
       log_warn "无法连接到外部网络，请检查网络配置"
     fi
   fi
   
   if [[ -n "${http_proxy:-}${https_proxy:-}${HTTP_PROXY:-}${HTTPS_PROXY:-}" ]]; then
     log_info "检测到代理配置："
     [[ -n "${http_proxy:-}${HTTP_PROXY:-}" ]] && log_info "  HTTP_PROXY=${http_proxy:-${HTTP_PROXY}}"
     [[ -n "${https_proxy:-}${HTTPS_PROXY:-}" ]] && log_info "  HTTPS_PROXY=${https_proxy:-${HTTPS_PROXY}}"
   fi
   
   local retry_count=0
   local max_retries=3
   while (( retry_count < max_retries )); do
     if curl -fsSL --connect-timeout 10 --max-time 30 --retry 2 --retry-delay 2 "${RAW_BASE_URL}/scripts/deploy.sh" >/dev/null 2>&1; then
       log_success "GitHub 连接正常"
       return 0
     fi
     retry_count=$((retry_count + 1))
     if (( retry_count < max_retries )); then
       log_warn "连接 GitHub 失败（尝试 ${retry_count}/${max_retries}），3秒后重试..."
       sleep 3
     fi
   done
   
   log_error "无法从 ${RAW_BASE_URL} 获取安装资源。"
   log_info "故障排查："
   log_info "  1. 检查网络连接: ping 8.8.8.8"
   log_info "  2. 检查 DNS 解析: nslookup github.com"
   log_info "  3. 检查 GitHub 访问: curl -I https://github.com"
   log_info "  4. 如在国内，可能需要配置代理："
   log_info "     export https_proxy=http://proxy.example.com:port"
   log_info "  5. 或使用国内镜像站（如有）"
   exit 1
 }

 download_asset() {
   local remote_path="$1"
   local target_path="$2"
   local target_dir
   target_dir=$(dirname "${target_path}")
   mkdir -p "${target_dir}" || {
     log_error "无法创建目录 ${target_dir}"
     return 1
   }
   log_info "下载 ${remote_path}"
   
   local retry_count=0
   local max_retries=3
   while (( retry_count < max_retries )); do
     if curl -fsSL --connect-timeout 10 --max-time 60 --retry 2 --retry-delay 2 "${RAW_BASE_URL}/${remote_path}" -o "${target_path}.tmp"; then
       if mv "${target_path}.tmp" "${target_path}"; then
         log_success "已下载 ${remote_path}"
         return 0
       else
         log_error "无法保存文件到 ${target_path}"
         rm -f "${target_path}.tmp"
         return 1
       fi
     fi
     retry_count=$((retry_count + 1))
     if (( retry_count < max_retries )); then
       log_warn "下载失败（尝试 ${retry_count}/${max_retries}），3秒后重试..."
       sleep 3
     fi
   done
   
   log_error "无法下载 ${remote_path}（已重试 ${max_retries} 次）"
   rm -f "${target_path}.tmp"
   return 1
 }

check_system_resources() {
  log_step "检查系统资源"
  local warnings=0
  
  if command -v free >/dev/null 2>&1; then
    local mem_total mem_available
    mem_total=$(free -m | awk '/^Mem:/ {print $2}')
    mem_available=$(free -m | awk '/^Mem:/ {print $7}')
    if [[ -n "${mem_total}" ]]; then
      log_info "总内存: ${mem_total}MB"
      if (( mem_total < 1800 )); then
        log_warn "内存不足 2GB（当前 ${mem_total}MB），可能影响性能"
        warnings=$((warnings + 1))
      else
        log_success "内存充足: ${mem_total}MB"
      fi
    fi
  else
    log_warn "无法检测内存容量（缺少 free 命令）"
  fi
  
  if command -v df >/dev/null 2>&1; then
    local disk_avail
    disk_avail=$(df -Pm "${INSTALL_ROOT}" 2>/dev/null | awk 'NR==2 {print $4}')
    if [[ -n "${disk_avail}" ]]; then
      log_info "可用磁盘空间: ${disk_avail}MB"
      if (( disk_avail < 5120 )); then
        log_warn "磁盘空间不足 5GB（当前 ${disk_avail}MB），可能导致安装失败"
        warnings=$((warnings + 1))
      else
        log_success "磁盘空间充足: ${disk_avail}MB"
      fi
    fi
  else
    log_warn "无法检测磁盘空间（缺少 df 命令）"
  fi
  
  if command -v nproc >/dev/null 2>&1; then
    local cpu_cores
    cpu_cores=$(nproc)
    log_info "CPU 核心数: ${cpu_cores}"
    if (( cpu_cores < 2 )); then
      log_warn "CPU 核心数较少（${cpu_cores}），推荐至少 2 核"
      warnings=$((warnings + 1))
    else
      log_success "CPU 核心数: ${cpu_cores}"
    fi
  fi
  
  if (( warnings > 0 )); then
    log_warn "检测到 ${warnings} 个资源警告，但安装将继续"
    if ! prompt_confirm "系统资源可能不足，是否继续安装？" "y"; then
      log_info "已取消安装"
      exit 0
    fi
  fi
  
  return 0
}

verify_project_structure() {
  log_step "验证项目结构"
  local required_dirs=("backend" "frontend")
  local required_files=("docker-compose.yml" "backend/Dockerfile" "frontend/Dockerfile")
  local missing=0
  
  for dir in "${required_dirs[@]}"; do
    if [[ ! -d "${INSTALL_ROOT}/${dir}" ]]; then
      log_error "缺少必需目录: ${dir}"
      missing=$((missing + 1))
    fi
  done
  
  for file in "${required_files[@]}"; do
    if [[ ! -f "${INSTALL_ROOT}/${file}" ]]; then
      log_error "缺少必需文件: ${file}"
      missing=$((missing + 1))
    fi
  done
  
  if (( missing > 0 )); then
    log_error "项目结构不完整，缺少 ${missing} 个必需文件/目录"
    log_info "这可能是因为："
    log_info "  1. Git 克隆不完整"
    log_info "  2. 分支不正确"
    log_info "  3. 网络传输中断"
    log_info "建议重新运行安装脚本"
    return 1
  fi
  
  log_success "项目结构验证通过"
  return 0
}

clone_project_code() {
  log_step "同步项目代码"

  local git_url="https://github.com/${CAPDF_REMOTE_REPO}.git"
  local temp_dir

  if [[ -d "${INSTALL_ROOT}/.git" ]]; then
    log_info "检测到现有 Git 仓库"
    if prompt_confirm "是否更新到 ${CAPDF_CHANNEL} 分支的最新代码？" "y"; then
      log_info "获取最新代码..."
      pushd "${INSTALL_ROOT}" >/dev/null || return 1
      if ! git fetch --depth 1 origin "${CAPDF_CHANNEL}" 2>&1 | tee -a "${LOG_FILE}"; then
        log_warn "拉取最新代码失败，保留当前版本"
        popd >/dev/null || true
        return 0
      fi
      if ! git checkout "${CAPDF_CHANNEL}" 2>&1 | tee -a "${LOG_FILE}"; then
        log_warn "无法切换到分支 ${CAPDF_CHANNEL}，保留当前版本"
        popd >/dev/null || true
        return 0
      fi
      if ! git reset --hard "origin/${CAPDF_CHANNEL}" 2>&1 | tee -a "${LOG_FILE}"; then
        log_warn "代码重置失败，保留当前版本"
        popd >/dev/null || true
        return 0
      fi
      popd >/dev/null || true
      log_success "项目代码已更新"
    else
      log_info "保留当前项目代码"
    fi
    return 0
  fi

  if [[ -d "${INSTALL_ROOT}/backend" || -d "${INSTALL_ROOT}/frontend" ]]; then
    log_warn "检测到现有项目目录但无 Git 仓库"
    if prompt_confirm "是否覆盖为 ${CAPDF_CHANNEL} 分支的最新代码？" "y"; then
      rm -rf "${INSTALL_ROOT}/backend" "${INSTALL_ROOT}/frontend"
    else
      log_info "保留现有代码"
      return 0
    fi
  fi

  temp_dir=$(mktemp -d) || {
    log_error "无法创建临时目录"
    return 1
  }

  log_info "从 ${git_url} 克隆分支 ${CAPDF_CHANNEL}"
  if ! git clone --depth 1 --branch "${CAPDF_CHANNEL}" "${git_url}" "${temp_dir}/repo" 2>&1 | tee -a "${LOG_FILE}"; then
    log_error "代码克隆失败，请检查网络或分支名称"
    rm -rf "${temp_dir}"
    return 1
  fi

  log_info "同步仓库内容到 ${INSTALL_ROOT}"
  cp -a "${temp_dir}/repo/." "${INSTALL_ROOT}/" || {
    log_error "复制项目文件失败"
    rm -rf "${temp_dir}"
    return 1
  }

  rm -rf "${temp_dir}"
  log_success "项目代码已准备就绪"
  return 0
}

install_capdf_files() {
  log_step "下载管理脚本"
  download_asset "scripts/deploy.sh" "${SCRIPTS_DIR}/deploy.sh" || {
    log_error "deploy.sh 下载失败，安装无法继续"
    return 1
  }
  chmod +x "${SCRIPTS_DIR}/deploy.sh" || log_warn "无法设置 deploy.sh 为可执行"

  download_asset "scripts/install.sh" "${SCRIPTS_DIR}/install.sh" || {
    log_warn "install.sh 下载失败，跳过"
  }
  if [[ -f "${SCRIPTS_DIR}/install.sh" ]]; then
    chmod +x "${SCRIPTS_DIR}/install.sh" || log_warn "无法设置 install.sh 为可执行"
  fi

  log_step "同步模版文件"
  download_asset ".env.example" "${INSTALL_ROOT}/.env.example" || {
    log_warn ".env.example 下载失败"
  }
  download_asset ".env.docker.example" "${INSTALL_ROOT}/.env.docker.example" || {
    log_warn ".env.docker.example 下载失败"
  }
  download_asset "docker-compose.yml" "${INSTALL_ROOT}/docker-compose.example.yml" || {
    log_warn "docker-compose.yml 下载失败"
  }
  log_success "脚本文件已安装"
  return 0
}

create_launcher() {
   log_step "创建 capdf 命令"
   local launcher_tmp
   launcher_tmp=$(mktemp) || {
     log_error "无法创建临时文件"
     return 1
   }
   cat >"${launcher_tmp}" << 'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
export CAPDF_HOME="CAPDF_HOME_VAL"
export CAPDF_CHANNEL="CAPDF_CHANNEL_VAL"
export CAPDF_REMOTE_REPO="CAPDF_REMOTE_REPO_VAL"
exec "SCRIPTS_DIR_VAL/deploy.sh" "$@"
EOF
   sed -i "s|CAPDF_HOME_VAL|${INSTALL_ROOT}|g" "${launcher_tmp}"
   sed -i "s|CAPDF_CHANNEL_VAL|${CAPDF_CHANNEL}|g" "${launcher_tmp}"
   sed -i "s|CAPDF_REMOTE_REPO_VAL|${CAPDF_REMOTE_REPO}|g" "${launcher_tmp}"
   sed -i "s|SCRIPTS_DIR_VAL|${SCRIPTS_DIR}|g" "${launcher_tmp}"
   
   ${SUDO} mv "${launcher_tmp}" "${LAUNCHER_PATH}" || {
     log_error "无法创建启动脚本"
     rm -f "${launcher_tmp}"
     return 1
   }
   ${SUDO} chmod +x "${LAUNCHER_PATH}" || {
     log_error "无法设置启动脚本为可执行"
     return 1
   }
   if [[ -e "${LEGACY_LAUNCHER_PATH}" && ! -L "${LEGACY_LAUNCHER_PATH}" ]]; then
     ${SUDO} rm -f "${LEGACY_LAUNCHER_PATH}" || log_warn "无法删除旧启动脚本"
   fi
   if [[ ! -L "${LEGACY_LAUNCHER_PATH}" ]]; then
     ${SUDO} ln -sf "${LAUNCHER_PATH}" "${LEGACY_LAUNCHER_PATH}" || {
       log_warn "无法创建兼容性符号链接"
     }
   fi
   log_success "启动脚本已创建"
   return 0
 }

 ensure_user_in_docker_group() {
   if id -nG "${INSTALL_USER}" | grep -qw docker; then
     log_success "当前用户已在 docker 用户组中"
     return 0
   fi
   log_warn "当前用户 ${INSTALL_USER} 未加入 docker 用户组，后续可能需要 sudo 才能管理容器。"
   log_info "推荐操作："
   if [[ ${EUID} -ne 0 ]]; then
     printf "  %s sudo usermod -aG docker %s%s\n" "${BOLD}" "${INSTALL_USER}" "${RESET}"
   else
     printf "  %s usermod -aG docker %s%s\n" "${BOLD}" "${INSTALL_USER}" "${RESET}"
   fi
   log_info "执行完命令后，请重新登录或运行："
   printf "  %s newgrp docker%s\n" "${BOLD}" "${RESET}"
   return 0
 }

run_initial_install() {
   if [[ "${CAPDF_SKIP_INSTALL:-0}" == "1" ]]; then
     log_info "已跳过自动部署，可稍后运行 capdf install。"
     return 0
   fi
   log_step "启动 ca-pdf 安装向导"
   if [[ ! -f "${SCRIPTS_DIR}/deploy.sh" ]]; then
     log_error "deploy.sh 不存在，无法启动安装向导"
     return 1
   fi
   "${SCRIPTS_DIR}/deploy.sh" install || {
     log_error "安装向导执行失败"
     return 1
   }
   return 0
 }

parse_args() {
   while [[ $# -gt 0 ]]; do
     case "$1" in
       -h|--help)
         show_help
         exit 0
         ;;
       -v|--version)
         log_info "ca-pdf 安装脚本 v1.0"
         exit 0
         ;;
       --skip-install)
         CAPDF_SKIP_INSTALL=1
         shift
         ;;
       --home)
         INSTALL_ROOT="$2"
         shift 2
         ;;
       --channel)
         CAPDF_CHANNEL="$2"
         shift 2
         ;;
       --repo)
         CAPDF_REMOTE_REPO="$2"
         shift 2
         ;;
       *)
         log_error "未知选项: $1"
         log_info "使用 -h 或 --help 查看帮助"
         exit 1
         ;;
     esac
   done
}

initialize_paths() {
   RAW_BASE_URL="https://raw.githubusercontent.com/${CAPDF_REMOTE_REPO}/${CAPDF_CHANNEL}"
   SCRIPTS_DIR="${INSTALL_ROOT}/scripts"
   LOG_DIR="${INSTALL_ROOT}/logs"
   BACKUP_DIR="${INSTALL_ROOT}/backups"
   LOG_FILE="${LOG_DIR}/installer-$(date +%Y%m%d).log"
}

main() {
    parse_args "$@"
    initialize_paths

    ensure_directories || {
      log_error "无法初始化安装目录"
      exit 1
    }

    if [[ -w "${LOG_FILE}" ]]; then
      exec > >(tee -a "${LOG_FILE}") 2>&1
      log_info "日志输出到 ${LOG_FILE}"
    else
      log_warn "无法写入日志文件 ${LOG_FILE}，日志输出到标准输出"
    fi

    log_step "========== ca-pdf 一键安装脚本 =========="
    log_info "安装路径: ${INSTALL_ROOT}"
    log_info "分支: ${CAPDF_CHANNEL}"
    log_info "仓库: ${CAPDF_REMOTE_REPO}"
    log_step "=========================================="

    log_step "系统预检查"
    check_system_resources || exit 1

    log_step "初始化安装器"
    detect_package_manager || exit 1

    ensure_command curl || exit 1
    check_network || exit 1
    ensure_command git || exit 1
    ensure_command jq || exit 1
    ensure_command openssl || exit 1
    ensure_command tar || exit 1
    ensure_command gzip || exit 1

    install_docker || exit 1
    ensure_docker_service || exit 1
    ensure_compose_plugin || {
      log_warn "Docker Compose 可能安装失败，但安装继续"
    }
    ensure_user_in_docker_group

    clone_project_code || exit 1
    verify_project_structure || exit 1

    install_capdf_files || exit 1
    create_launcher || exit 1

    log_success "========== 安装完成 =========="
    log_success "管理脚本已安装至 ${INSTALL_ROOT}"
    log_info "启动脚本路径: ${LAUNCHER_PATH}"
    log_info ""
    log_info "现在可以通过以下命令进入菜单化运维界面："
    printf "  %s capdf%s\n" "${BOLD}" "${RESET}"
    log_info ""

    run_initial_install || {
      log_warn "初始安装步骤未完成，稍后可运行 capdf install 继续"
    }

    log_success "====== 安装流程结束 ======"
    log_info "使用帮助: capdf --help"
    log_info "GitHub: https://github.com/QAQ-AWA/ca-pdf"
    log_info "反馈邮箱: 7780102@qq.com"
}

main "$@"
