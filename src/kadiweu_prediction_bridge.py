"""Conservative bridge from source-tree positions to emitted UD word IDs.

No lexical fields are changed here. Empty traces participate in inference but
are never emitted; MWT range rows are not words and have no source position.
"""
from kadiweu_constituency import tree_from_sentence
from kadiweu_constituency_dependencies import infer_dependencies


def predict(sentence):
    # Read the original tree, before the legacy empty-category resolver.
    return infer_dependencies(tree_from_sentence(sentence))


def align_predictions(assignments, tokens):
    by_source = {t.source_pos: t for t in tokens}
    if len(by_source) != len(tokens):
        raise ValueError("duplicate emitted source positions")
    result = {}
    for a in assignments:
        if a.dependent_position not in by_source:
            raise ValueError("predicted dependent was not emitted")
        if a.head_position != 0 and a.head_position not in by_source:
            raise ValueError("predicted head was not emitted")
        dep = by_source[a.dependent_position].id
        head = 0 if a.head_position == 0 else by_source[a.head_position].id
        edge = (head, a.deprel, a.rule)
        if dep in result and result[dep] != edge:
            raise ValueError("conflicting predictions for one word")
        if dep == head or ((head == 0) != (a.deprel == "root")):
            raise ValueError("invalid predicted root/self attachment")
        result[dep] = edge
    if sum(h == 0 for h, _, _ in result.values()) > 1:
        raise ValueError("multiple predicted roots")
    return result


def graph_problem(tokens):
    """Validate the combined predicted/fallback basic dependency graph."""
    edges = {t.id: t.head for t in tokens}
    if not tokens:
        return None
    if sum(t.head == 0 and t.deprel == "root" for t in tokens) != 1:
        return "expected one root"
    for t in tokens:
        if (t.head == 0) != (t.deprel == "root"):
            return "inconsistent root relation"
        if t.head != 0 and t.head not in edges:
            return "missing head"
        seen = set()
        current = t.id
        while current:
            if current in seen:
                return "cycle in combined predictions and fallbacks"
            seen.add(current)
            current = edges.get(current, 0)
    return None


def demote_unlocked_duplicates(tokens):
    """Limit fallback core dependents per predicate, never sentence-wide.

    Locked tree/trace relations take priority. Multiple locked dependents are
    left intact for review, not silently rewritten by a weak fallback.
    """
    groups = {}
    for t in tokens:
        if t.deprel in {"nsubj", "obj"}:
            groups.setdefault((t.head, t.deprel), []).append(t)
    for (_, relation), group in groups.items():
        locked = [t for t in group if t.locked_deprel]
        keep = locked or group[:1]
        for t in group:
            if t not in keep:
                t.deprel = "nmod:poss" if relation == "nsubj" and t.xpos == "N$" else "dep"
