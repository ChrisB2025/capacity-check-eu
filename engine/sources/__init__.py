"""One module per data source, each with download, parse and validate functions.

Every source writes a parquet file to ``data/processed/``, a row to
``docs/data-register.md`` and a line to ``data/checksums.txt``.
Implemented in Phase 1.
"""
