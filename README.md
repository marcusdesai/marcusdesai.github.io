# My Blog

Notes for myself, and for you, whoever you are.

### FAQ

**Q**: How can I serve locally with hot reloading?\
**A**: `./run serve` in repo root (hardcoded: `http://localhost:8000`)

**Q**: How are highlighting styles generated?\
**A**: Using `Pygments`, see [here][pygments] for docs and builtin styles.

**Q**: How can I generate syntax highlighting styles?\
**A**: `pygmentize -S <STYLE> -f html -a .highlight > themes/simple/static/css/highlight.cs` in repo root.

[pygments]: https://pygments.org
