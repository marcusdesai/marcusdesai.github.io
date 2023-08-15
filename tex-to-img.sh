#!/usr/bin/env bash

INPUT="$1"
NAME="$(basename "$INPUT" ".tex")"
IMG_OUT=$(echo "$INPUT" | sed 's/latex/content\/images/g' | sed 's/.tex/.jpeg/g')
TEX_OUT_DIR="out"

# clear out each time we run to avoid unneeded output buildup
[ ! -d "${TEX_OUT_DIR}" ] || rm "${TEX_OUT_DIR}/"*

pdflatex \
  -quiet \
  -file-line-error \
  -interaction=nonstopmode \
  -synctex=1 \
  -output-format=pdf \
  -output-directory=/Users/marcusdesai/projects/marcusdesai.github.io/out "$INPUT"

# From imageMagick
convert -density 300 "$TEX_OUT_DIR/$NAME.pdf" -quality 100 -flatten "$IMG_OUT"
