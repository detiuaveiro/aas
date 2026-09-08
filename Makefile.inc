# Makefile.inc
# Configuration
CUR_DIR := $(shell basename $(CURDIR))
PARENT_DIR := $(shell basename $(dir $(CURDIR)))
SHM_DIR ?= /dev/shm/$(PARENT_DIR)-build
BUILD_PATH := $(SHM_DIR)/$(CUR_DIR)

# PDF Engine and Options
ENGINE ?= xelatex
PANDOC_FLAGS := -s --metadata-file=config.yml -d defaults.yml

# Get all markdown files, sorted alphabetically (01-intro.md, 02-ch1.md, etc.)
ALL_MD := $(sort $(filter-out README.md, $(wildcard *.md)))

# Determine target based on directory name
ifeq ($(findstring slides,$(CUR_DIR)),slides)
	PANDOC_DOC_FLAGS = -t beamer --slide-level=2
	TARGETS := $(patsubst %.md,%.pdf,$(ALL_MD))
else ifeq ($(findstring booklet,$(CUR_DIR)),booklet)
	PANDOC_DOC_FLAGS =
	# Build a single PDF named after the current directory
	TARGETS := $(CUR_DIR).pdf
else
	PANDOC_DOC_FLAGS =
	TARGETS := $(patsubst %.md,%.pdf,$(ALL_MD))
endif

.PHONY: all clean pdf

all: $(TARGETS)
pdf: $(TARGETS)

# 1:1 Compilation Rule (Standard & Slides)
%.pdf: %.md
	@mkdir -p $(BUILD_PATH)/$*
	@pandoc $(PANDOC_FLAGS) $(PANDOC_DOC_FLAGS) \
		--pdf-engine=latexmk \
		--pdf-engine-opt=-outdir=$(BUILD_PATH)/$* \
		--pdf-engine-opt=-pdflatex=$(ENGINE) \
		-o $(BUILD_PATH)/$*/$@ $<
	@cp $(BUILD_PATH)/$*/$@ $@

# N:1 Compilation Rule (Booklets)
$(CUR_DIR).pdf: $(ALL_MD)
	@if [ -z "$(ALL_MD)" ]; then \
		echo "Error: No .md files found in $(CUR_DIR) to build the booklet!"; \
		exit 1; \
	fi
	@mkdir -p $(BUILD_PATH)/booklet_build
	@pandoc $(PANDOC_FLAGS) $(PANDOC_DOC_FLAGS) \
		--pdf-engine=latexmk \
		--pdf-engine-opt=-outdir=$(BUILD_PATH)/booklet_build \
		--pdf-engine-opt=-pdflatex=$(ENGINE) \
		-o $(BUILD_PATH)/booklet_build/$@ $(ALL_MD)
	@cp $(BUILD_PATH)/booklet_build/$@ $@

clean:
	rm -rf *.pdf
	rm -rf $(BUILD_PATH)
