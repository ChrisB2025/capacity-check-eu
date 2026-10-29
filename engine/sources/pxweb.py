"""PxWeb API (version 1) helpers, used by Statistics Sweden and Konjunkturinstitutet.

A query is a JSON body posted to the table URL; the response is JSON-stat 2.0.
The unedited response is the raw file.
"""

from __future__ import annotations

import itertools
import json

import pandas as pd

from engine.sources._common import RawFile, SourceError, download, http_session


def table_updated(table_url: str, sess=None) -> str:
    """The 'updated' date the parent node lists for this table, as YYYY-MM-DD."""
    sess = sess or http_session()
    parent, table_id = table_url.rstrip("/").rsplit("/", 1)
    resp = sess.get(parent, timeout=120)
    if resp.status_code != 200:
        raise SourceError(f"{parent}: HTTP {resp.status_code}")
    for node in resp.json():
        if node.get("id") == table_id:
            return str(node.get("updated", ""))[:10]
    raise SourceError(f"{table_id} not listed under {parent}")


def query(
    key: str,
    table_url: str,
    dataset: str,
    selections: dict[str, list[str]],
    force: bool = False,
) -> RawFile:
    """Post a query selecting ``selections`` (omitted variables are eliminated)."""
    sess = http_session()
    edition = f"upd{table_updated(table_url, sess)}"
    body = {
        "query": [
            {"code": code, "selection": {"filter": "item" if vals != ["*"] else "all",
                                          "values": vals}}
            for code, vals in selections.items()
        ],
        "response": {"format": "json-stat2"},
    }  # fmt: skip
    return download(
        key, table_url, dataset, edition, "json", sess=sess, force=force,
        method="POST", json_body=body,
    )  # fmt: skip


def read_jsonstat2(path) -> pd.DataFrame:
    """Flatten a JSON-stat 2.0 dataset into a long frame with codes and labels."""
    with open(path, encoding="utf-8-sig") as fh:
        ds = json.load(fh)
    dims = ds["id"]
    codes, labels = [], []
    for d in dims:
        cat = ds["dimension"][d]["category"]
        index = cat["index"]
        order = sorted(index, key=index.get) if isinstance(index, dict) else index
        codes.append(order)
        labels.append([cat.get("label", {}).get(c, c) for c in order])
    values = ds["value"]
    if isinstance(values, dict):
        n = 1
        for s in ds["size"]:
            n *= s
        dense = [None] * n
        for k, v in values.items():
            dense[int(k)] = v
        values = dense
    rows = itertools.product(*[range(len(c)) for c in codes])
    records = []
    for flat, idx in zip(range(len(values)), rows, strict=True):
        rec = {}
        for d, i, cs, ls in zip(dims, idx, codes, labels, strict=True):
            rec[d] = cs[i]
            rec[f"{d}_label"] = ls[i]
        rec["value"] = values[flat]
        records.append(rec)
    df = pd.DataFrame.from_records(records)
    status = ds.get("status")
    if isinstance(status, dict):
        df["status"] = [status.get(str(i), "") for i in range(len(df))]
    return df
