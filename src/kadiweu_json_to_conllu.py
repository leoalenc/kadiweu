#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys

# --- CONFIG (from your induced mapping) ---

UPOS_MAP = {
    "VB": "VERB",
    "VBAPL": "VERB",
    "N": "NOUN",
    "N$": "NOUN",
    "NPR": "PROPN",
    "D": "DET",
    "Q": "DET",
    "PRO": "PRON",
    "ADV": "ADV",
    "ADJ": "ADJ",
    "NEG": "PART",
    "C": "SCONJ",
    "CONJ": "CCONJ",
    "T": "AUX"
}

CHUNK_MAP = {
    "NP-SBJ": "nsubj",
    "NP-ACC": "obj",
    "NP": "obj",
    "ADVP": "advmod"
}


def get_split_tags(token):
    return [s.get("t") for s in token.get("splits", []) if isinstance(s, dict)]


def build_feats(split_tags):
    feats = []

    if "Gen" in split_tags:
        feats.append("Poss=Yes")
    if "PFV" in split_tags:
        feats.append("Aspect=Perf")
    if "Neg" in split_tags:
        feats.append("Polarity=Neg")

    return "|".join(feats) if feats else "_"


def guess_deprel(token_chunks, upos):
    if "NP-SBJ" in token_chunks:
        return "nsubj"
    if "NP-ACC" in token_chunks:
        return "obj"
    if upos == "VERB":
        return "root"
    return "dep"


def convert_sentence(sent, index):
    struct = sent["struct"]
    tokens = struct["tokens"]
    chunks = struct.get("chunks", [])

    text = sent["text"]
    text_orig = sent["text"]
    sent_uid = sent.get("uid")

    # Add punctuation if missing
    if not text.endswith("."):
        text = text + "."

    # Metadata
    print(f"# sent_id = ped-gramm-{index}")
    print(f"# sent_uid = {sent_uid}")
    print(f"# text = {text}")
    print(f"# text_orig = {text_orig}")

    if "translations" in sent:
        pt = sent["translations"].get("pt-br")
        if pt:
            if not pt.endswith("."):
                pt += "."
            print(f"# text_por = {pt}")

    # Build chunk membership
    chunk_map = {}
    for ch in chunks:
        start, end = ch.get("i"), ch.get("f")
        label = ch.get("t")
        for i in range(start, end + 1):
            chunk_map.setdefault(i, []).append(label)

    root_id = None

    rows = []
    for i, tok in enumerate(tokens, start=1):
        form = tok["v"]
        tag = tok["t"]

        upos = UPOS_MAP.get(tag, "X")
        xpos = tag

        split_tags = get_split_tags(tok)
        feats = build_feats(split_tags)

        chunks_here = chunk_map.get(tok.get("p"), [])

        deprel = guess_deprel(chunks_here, upos)

        if deprel == "root":
            root_id = i

        rows.append({
            "id": i,
            "form": form,
            "lemma": form.lower(),
            "upos": upos,
            "xpos": xpos,
            "feats": feats,
            "head": 0,
            "deprel": deprel
        })

    # assign heads
    for row in rows:
        if row["deprel"] == "root":
            row["head"] = 0
        else:
            row["head"] = root_id if root_id else 0

    # print rows
    for row in rows:
        print("\t".join([
            str(row["id"]),
            row["form"],
            row["lemma"],
            row["upos"],
            row["xpos"],
            row["feats"],
            str(row["head"]),
            row["deprel"],
            "_",
            "_"
        ]))

    # punctuation
    last_id = len(rows) + 1
    print(f"{last_id}\t.\t.\tPUNCT\tPUNCT\t_\t{root_id}\tpunct\t_\tSpaceAfter=No")

    print()


def main(json_file):
    data = json.load(open(json_file, encoding="utf-8"))

    sentences = []
    for page in data.get("pages", []):
        sentences.extend(page.get("sentences", []))

    for i, sent in enumerate(sentences, start=1):
        convert_sentence(sent, i)


if __name__ == "__main__":
    main(sys.argv[1])