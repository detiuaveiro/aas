# Makefile
SHELL := /bin/bash
.PHONY: all clean venv llama-models llama-up llama-down llama-check
.DEFAULT_GOAL := all

# Python environment: a clean venv. When pkg-config finds OpenBLAS and a C/C++ compiler
# is present, NumPy is compiled from source against it and tuned to this CPU
# (Debian/Ubuntu/WSL: build-essential pkg-config libopenblas-dev; macOS: brew install
# openblas pkg-config). Otherwise, or if that build fails, the prebuilt NumPy wheel
# (which bundles its own OpenBLAS) is used. NUMPY_SOURCE=yes forces the source build
# (no fallback), NUMPY_SOURCE=no forces the wheel.
VENV ?= venv
PYTHON ?= python3
NUMPY_SOURCE ?= auto
NUMPY_FLAGS := -Csetup-args=-Dblas=openblas -Csetup-args=-Dlapack=openblas -Csetup-args=-Dcpu-baseline=native

venv:
	@$(PYTHON) -m venv $(VENV) || { echo "venv creation failed (Debian/Ubuntu/WSL: sudo apt install python3-venv)"; exit 1; }
	$(VENV)/bin/pip install -q --upgrade pip
	@req="$$(grep -oE '"numpy[^"]*"' pyproject.toml | tr -d '"')"; \
	if [ "$(NUMPY_SOURCE)" = auto ] && command -v brew >/dev/null 2>&1; then \
		export PKG_CONFIG_PATH="$$(brew --prefix openblas 2>/dev/null)/lib/pkgconfig$${PKG_CONFIG_PATH:+:$$PKG_CONFIG_PATH}"; \
	fi; \
	build=no; \
	case "$(NUMPY_SOURCE)" in \
		yes) build=yes ;; \
		auto) if command -v pkg-config >/dev/null 2>&1 && pkg-config --exists openblas \
			&& command -v cc >/dev/null 2>&1 && command -v c++ >/dev/null 2>&1; then build=yes; \
			else echo "OpenBLAS, pkg-config or a compiler not found: using the prebuilt NumPy wheel"; fi ;; \
	esac; \
	if [ "$$build" = yes ]; then \
		echo "Building NumPy against the system OpenBLAS (a few minutes)"; \
		$(VENV)/bin/pip install --no-binary numpy $(NUMPY_FLAGS) "$$req" || { \
			[ "$(NUMPY_SOURCE)" = yes ] && exit 1; \
			echo "NumPy source build failed: falling back to the prebuilt wheel"; \
			$(VENV)/bin/pip install "$$req"; }; \
	else \
		$(VENV)/bin/pip install "$$req"; \
	fi
	@$(VENV)/bin/pip install .; rc=$$?; rm -rf build aas.egg-info; exit $$rc
	$(VENV)/bin/python -c "import numpy as np; b = np.show_config(mode='dicts')['Build Dependencies']['blas']; print('NumPy', np.__version__, 'BLAS:', b['name'], b['version'], b.get('lib directory', ''))"


# llama.cpp servers for the spam labs (see notebooks/01-spam/llama/README.md). PROFILE = gpu (Vulkan, default) | cpu | "gpu chat".
LLAMA_DIR := notebooks/01-spam/llama
PROFILE ?= gpu
llama-models:
	$(VENV)/bin/python $(LLAMA_DIR)/download_model.py
	$(VENV)/bin/python $(LLAMA_DIR)/download_model.py --repo second-state/All-MiniLM-L6-v2-Embedding-GGUF --quant f16
llama-up:
	cd $(LLAMA_DIR) && docker compose $(foreach p,$(PROFILE),--profile $(p)) up -d
llama-down:
	cd $(LLAMA_DIR) && docker compose --profile gpu --profile cpu --profile chat down
llama-check:
	$(VENV)/bin/python $(LLAMA_DIR)/check_embed.py
	$(VENV)/bin/python $(LLAMA_DIR)/check_embed.py --mini

all clean:
	@term_cols=$$(tput cols 2>/dev/null || echo 80); \
	total=$$(find . -mindepth 2 -name "Makefile" ! -path "*/venv/*" ! -path "*/volumes/*" ! -path "*/.git/*" | wc -l); \
	if [ "$$total" -eq 0 ]; then echo "No Makefiles found."; exit 0; fi; \
	current=0; \
	echo "Build started at $$(date)" > build.log; \
	tput civis || true; \
	find . -mindepth 2 -name "Makefile" ! -path "*/venv/*" ! -path "*/volumes/*" ! -path "*/.git/*" -print0 2>/dev/null | while IFS= read -r -d '' mkfile; do \
		dir=$$(dirname "$$mkfile"); \
		current=$$((current + 1)); \
		percent=$$((current * 100 / total)); \
		text_len=$$(( 11 + $${#current} + $${#total} + $${#dir} )); \
		width=$$(( term_cols - text_len )); \
		if [ $$width -lt 10 ]; then width=10; fi; \
		filled=$$((percent * width / 100)); \
		empty=$$((width - filled)); \
		if [ $$filled -gt 0 ]; then bar_filled=$$(printf "%$${filled}s" "" | tr " " "#"); else bar_filled=""; fi; \
		if [ $$empty -gt 0 ]; then bar_empty=$$(printf "%$${empty}s" "" | tr " " " "); else bar_empty=""; fi; \
		printf "\r%3d%%|%s%s| %d/%d [%s]\033[K" "$$percent" "$$bar_filled" "$$bar_empty" "$$current" "$$total" "$$dir"; \
		if ! $(MAKE) -s -C "$$dir" $@ >> build.log 2>&1; then \
			printf "\nError processing %s. See build.log\n" "$$dir"; \
		fi; \
	done; \
	echo ""; \
	tput cnorm || true; \
	echo "Done."
	@if [ "$@" = clean ]; then rm -rf build aas.egg-info; fi
