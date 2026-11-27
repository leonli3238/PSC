#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p figures build/fig_tmp

for name in fig1_trust_boundary fig2_pipeline fig3_diagnostic_repair; do
    pdflatex -interaction=nonstopmode -output-directory=build/fig_tmp "figures/src/${name}.tex" >/dev/null
    cp "build/fig_tmp/${name}.pdf" "figures/${name}.pdf"
    gs -dSAFER -dBATCH -dNOPAUSE -sDEVICE=png16m -r300 \
       -sOutputFile="figures/${name}.png" "figures/${name}.pdf" >/dev/null
done

rm -rf build/fig_tmp
ls -lh figures/*.pdf figures/*.png
