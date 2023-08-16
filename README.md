# My Blog

Notes for myself, and for you, whoever you are.

## FAQ

**Q**: How can I serve locally with hot reloading?\
**A**: `./run.sh serve` in repo root (hardcoded: `http://localhost:8000`)

**Q**: How can I test against other specific browsers or mobile?\
**A**: Add the desired argument: `./run.sh serve [firefox|chrome|mobile]`

**Q**: How can I clean the output dir before serving?\
**A**: `./run.sh clean-serve` (or `serve-clean`, order doesn't matter)

**Q**: How are highlighting styles generated?\
**A**: Using `Pygments`, see [here][pygments] for docs and builtin styles.

**Q**: How can I generate syntax highlighting styles?\
**A**: `pygmentize -S <STYLE> -f html -a .highlight > themes/simple/static/css/highlight.cs` in repo root.

**Q**: How can I generate images from `.tex` files?\
**A**: `./tex-to-img.sh path/to/latex/file.tex` in repo root

[pygments]: https://pygments.org
