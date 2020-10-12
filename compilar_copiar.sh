git checkout "$1" --force
rm main.pdf
rm *aux
rm *lof
rm *log
rm *toc
rm *idx
rm *bbl
rm *blg
rm *ilg
rm *ind
rm *lol

xelatex main.tex -shell-escape -interaction=nonstopmode >> ../log.txt
makeindex main.tex
bibtex main
echo "Compiling - 2"
xelatex main.tex -shell-escape -interaction=nonstopmode >> /dev/null
echo "Compiling - 3"
xelatex main.tex -shell-escape -interaction=nonstopmode >> /dev/null
echo "Compiling - 4"
xelatex main.tex -shell-escape -interaction=nonstopmode >> /dev/null
cp main.pdf "../$1.pdf"
git checkout "$1" --force
echo "****************************************************"
sleep 1
