echo "=== Downloading data... ==="
python download.py
echo "=== Processing data... ==="
node index.js
echo "=== Minifying HTML... ==="
$HOME/go/bin/minify index.html -o public/index.html
