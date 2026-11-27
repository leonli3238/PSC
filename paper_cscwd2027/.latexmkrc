$out_dir = 'build';
$pdf_mode = 1;
$pdflatex = 'pdflatex -interaction=nonstopmode -synctex=1 %O %S';

# main_zh.tex needs LuaLaTeX. The system lualatex symlink is broken
# (it points at a missing luahbtex), so use the local wrapper.
my $zh_root = 0;
foreach my $arg (@ARGV) {
    if ($arg =~ /(^|\/)main_zh(\.tex)?$/) { $zh_root = 1; }
}
if ($zh_root) {
    $pdf_mode = 4;
    $out_dir = '';
    $lualatex = 'bash scripts/lualatex-zh %O %S';
}
