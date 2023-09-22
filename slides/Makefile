# lists of all output files that can be made
ALL_PDF = $(patsubst %.tex,%.pdf,$(wildcard *.tex))

# makes everything that can be made
# default is pdf
all : $(ALL_PDF)
pdf : $(ALL_PDF)

%.pdf: aux %.tex
	latexmk -xelatex -silent -jobname=aux/$* $*.tex 
	mv aux/$*.pdf $*.pdf

aux :
	mkdir -p aux

clean:
	rm -rf aux
	latexmk -C

.PHONY: all clean pdf
