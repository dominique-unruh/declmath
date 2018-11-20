PERL5LIB = $(abspath LaTeXML/blib/lib/)
export PERL5LIB
TEXINPUTS = .//:
export TEXINPUTS

.DELETE_ON_ERROR :

link_stex :
	find sTeX/sty/core -name '*.sty' -exec ln -sf {} \;

xml :
	LaTeXML/bin/latexmlc --profile stex --destination test.xml test.tex

pdf :
	pdflatex test.tex

build_latexml :
	git submodule update --checkout --init --recommend-shallow LaTeXML
	cd LaTeXML && perl Makefile.PL
	make -C LaTeXML
	#make -C LaTeXML test

build_latexml_stex : build_latexml
	git submodule update --checkout --init --recommend-shallow LaTeXML-Plugin-sTeX
	cd LaTeXML-Plugin-sTeX && perl Makefile.PL
	make -C LaTeXML-Plugin-sTeX
	#PERL5LIB=../LaTeXML/blib/lib/ make -C LaTeXML-Plugin-sTeX test

