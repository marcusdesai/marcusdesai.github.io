# My Blog

Notes for myself, and for you, whoever you are.

### FAQ

**Q**: How can I serve locally with hot reloading?\
**A**: `make devserver` in repo root (default: `localhost:8000`)

**Q**: How are highlighting styles generated?\
**A**: Using `Pygments`, see [here][pygments] for docs and builtin styles.

**Q**: How can I generate syntax highlighting styles?\
**A**: `pygmentize -S <STYLE> -f html -a .highlight > themes/test/static/css/highlight.cs` in repo root.

[pygments]: https://pygments.org
