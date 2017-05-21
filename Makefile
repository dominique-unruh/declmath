
default : test.xhtml

test.xml : test.tex test.sty.ltxml declmath.sty.ltxml

%.html : %.xml
	latexmlpost --javascript=LaTeXML-maybeMathjax.js --format=html5 --destination=$@ --cmml $<

%.xhtml : %.xml
	latexmlpost --javascript=LaTeXML-maybeMathjax.js --format=xhtml --destination=$@ --cmml $<

%.xml : %.tex
	latexml $< --strict --destination=$@
