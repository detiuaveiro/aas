# lists of all output files that can be made
ALL_PDF = $(patsubst %.tex,%.pdf,$(wildcard *.tex))

# makes everything that can be made
# default is pdf
all : $(ALL_PDF)
pdf : $(ALL_PDF)

%.pdf: aux/% tmp/% %.tex
	latexmk -xelatex $*.tex > tmp/$*/out || (less +G tmp/$*/out && exit 1)
# compile using XeLaTex
# redirects the shell output of latexmk to tmp
# if latexmk were to fail, show the tail of said output for debugging purposes
	mv `ls $*.* | grep -v '\.tex\|\.pdf\|\.dvi\|\.ps'` aux/$*
# -mv $*Notes.bib aux/$*
# moves everything but the .tex and .pdf to aux (or eventually .dvi or .ps)

tmp :
	mkdir -p tmp

aux :
	mkdir -p aux

tmp/%: tmp
	mkdir -p tmp/$*

aux/%: aux
	mkdir -p aux/$*

clean:
	rm -rf aux
	rm -rf tmp
	latexmk -c

.PHONY: all clean pdf 
