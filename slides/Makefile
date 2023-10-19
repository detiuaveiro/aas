# lists of all output files that can be made
ALL_PDF := $(patsubst %.md,%.pdf,$(wildcard *.md))
ALL_PDF := $(filter-out README.pdf, $(ALL_PDF))

# makes everything that can be made
# default is pdf
all: $(ALL_PDF)
pdf: $(ALL_PDF)

%.pdf: %.md style.tex
	pandoc -t beamer -s --bibliography=references.bib --pdf-engine=lualatex --include-in-header=style.tex -o $@ $<

clean:
	rm -rf *.pdf

.PHONY: all clean pdf
