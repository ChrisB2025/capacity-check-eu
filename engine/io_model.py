"""Step 2. Leontief analysis on the Eurostat FIGARO inter-country tables.

Builds the Leontief inverse once per data edition and caches it in
``data/processed/``; a run is then a matrix multiplication. Returns the
output required from each of 64 industries in each of 49 economies, split
into home, rest of EU and outside EU.
Implemented in Phase 2.
"""
