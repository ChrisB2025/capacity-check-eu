# Data register

Every dataset the engine uses, one row per downloaded file. Rows are written by `engine/sources/*` when a file is fetched (Phase 1 onward), never by hand. Eurostat keeps only the latest version of each dataset, so a file missing from this register may be unobtainable later.

| Column | Meaning |
| :--- | :--- |
| key | Source key in `engine/sources/catalogue.py` |
| publisher | Publishing body |
| dataset | Dataset code or title as the publisher gives it |
| edition | Publisher's edition, release or last-update stamp |
| url | Exact URL fetched |
| downloaded | Download date and time, UTC |
| file | File name in `data/raw/`, as `<dataset>_<edition>_<date>.<ext>` |
| sha256 | Checksum, also in `data/checksums.txt` |
| licence | Reuse terms, confirmed against the publisher's page |
| flags | Estimated, provisional or confidential observations the publisher marks |

## Register

| key | publisher | dataset | edition | url | downloaded | file | sha256 | licence | flags |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
