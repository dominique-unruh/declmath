FROM ubuntu:16.04
RUN apt update
RUN apt install -y texlive-full
RUN apt install -y build-essential git cpanminus trang libxml-libxslt-perl

RUN apt install -y libparse-recdescent-perl libio-string-perl
RUN apt install -y libarchive-zip-perl
RUN apt install -y libjson-xs-perl

# LaTeXML
#RUN git clone https://github.com/brucemiller/LaTeXML.git
#WORKDIR LaTeXML
#RUN cpanm -n .

# sTeX plugin
RUN git clone https://github.com/KWARC/LaTeXML-Plugin-sTeX.git
WORKDIR LaTeXML-Plugin-sTeX
RUN cpanm -n .

RUN rm -rf /usr/share/texlive/texmf-dist/tex/latex/stex

#RUN dpkg -S  /usr/share/texlive/texmf-dist/tex/latex/stex/cmath/cmath.sty.ltxml
#RUN XXX

# Experiment
COPY . /declmath
WORKDIR /declmath
#RUN make build_latexml_stex
#RUN make xml
RUN latexmlc --profile stex test.tex
