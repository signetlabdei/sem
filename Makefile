all: gsoc.md
	pandoc gsoc.md -f markdown -t html -s -c css/style.css -o gsoc.html
