#!/usr/bin/env bash
# Usage: detect_gpu.sh [-h]
# Prints the compose profile that matches this machine, one word on stdout (reasons go to stderr):
#   cuda13  NVIDIA Ampere..Blackwell (compute capability >= 8.0) with a driver that has CUDA 13 (>= 580)
#   cuda    NVIDIA Pascal..Ada (6.0 <= compute capability < 10) or Ampere/Ada with an older driver (CUDA 12)
#   vulkan  AMD, Intel and any other GPU with a Vulkan driver (Linux: /dev/dri/renderD*)
#   cpu     no usable GPU (macOS, Windows/WSL2 without NVIDIA, VMs)
# Override with `make llama-up PROFILE=<profile>` or LLAMA_PROFILE=<profile>.
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
	sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'
	exit 0
fi
[[ $# -eq 0 ]] || { echo "usage: $0 [-h]" >&2; exit 2; }

say() { echo "detect_gpu: $*" >&2; }

if [[ -n "${LLAMA_PROFILE:-}" ]]; then
	say "LLAMA_PROFILE=$LLAMA_PROFILE"
	echo "$LLAMA_PROFILE"
	exit 0
fi

if command -v nvidia-smi >/dev/null 2>&1; then
	if line=$(nvidia-smi --query-gpu=name,compute_cap,driver_version --format=csv,noheader 2>/dev/null | head -n1) && [[ -n "$line" ]]; then
		IFS=',' read -r name cc driver <<<"$line"
		name=${name# }
		cc=${cc# }
		driver=${driver# }
		major=${cc%%.*}
		minor=${cc#*.}
		drv=${driver%%.*}
		say "NVIDIA $name, compute capability $cc, driver $driver"
		if ! docker info --format '{{json .Runtimes}}' 2>/dev/null | grep -q nvidia; then
			say "warning: Docker has no 'nvidia' runtime: install the NVIDIA Container Toolkit (nvidia-ctk runtime configure --runtime=docker)"
		fi
		if ((major >= 8)) && ((drv >= 580)); then
			echo cuda13
		elif ((major >= 6)) && ((major < 10)); then
			((major >= 8)) && say "driver $driver is older than 580: using the CUDA 12 image"
			echo cuda
		elif ((major >= 10)); then
			say "Blackwell needs driver >= 580 (CUDA 13): update the driver, falling back to Vulkan"
			echo vulkan
		else
			say "compute capability $major.$minor is older than Pascal: falling back to Vulkan"
			echo vulkan
		fi
		exit 0
	fi
fi

if compgen -G "/dev/dri/renderD*" >/dev/null; then
	say "Vulkan-capable render node found: $(ls /dev/dri/renderD* | head -n1)"
	echo vulkan
else
	say "no GPU found: CPU only"
	echo cpu
fi
