# latexmk configuration for the One Quant Book series (pdfLaTeX only).
$pdf_mode = 1;
$out_dir = 'build';
@default_files = (
    'one_quant_book_01_markets_1.tex',
    'one_quant_book_02_markets_2.tex',
    'one_quant_book_03_markets_3.tex',
    'one_quant_book_04_methods.tex',
    'one_quant_book_05_derivatives.tex',
    'one_quant_book_06_rates_credit_risk.tex',
    'one_quant_book_07_research.tex',
    'one_quant_book_08_strategies_1.tex',
    'one_quant_book_09_strategies_2.tex',
    'one_quant_book_10_microstructure.tex',
    'one_quant_book_11_hft.tex',
    'one_quant_book_12_ml.tex',
    'one_quant_book_13_low_latency.tex',
);
# Many TikZ/pgfplots figures exceed pdfTeX's default main memory.
$pdflatex = 'pdflatex -cnf-line=main_memory=12000000 -cnf-line=extra_mem_top=6000000 -cnf-line=extra_mem_bot=6000000 -interaction=nonstopmode -halt-on-error %O %S';
$makeindex = 'makeindex %O -o %D %S';
