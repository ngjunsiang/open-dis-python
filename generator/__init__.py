"""Clean-slate DIS 7 code generator for open-dis-python.

Architecture (ruled 2026-10-14, .references/decisions.md): XML → typed IR
→ semantic resolution → static explicit-body emission (pure-Python,
stdlib-only) → black post-pass → verify gates. The corrected spec lives in
submodules/open-dis-spec-xml/xml/ (mirror of open-dis-spec-xml); the target-output reference is
the dis7-ng exemplar (commit 5a22702).

Stdlib-only by ruling so the generator stays vendorable in both
open-dis-python and open-dis-spec-xml; black is a dev-time post-pass, not
a runtime dependency.
"""

__version__ = "0.1.0"
