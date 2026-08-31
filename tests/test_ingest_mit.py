from scripts.ingest_mit import build_chunks


def test_verified_figures_are_scoped_to_their_chapter():
    chunks, figures = build_chunks([1, 8])
    section = [
        chunk
        for chunk in chunks
        if chunk["section_id"] == "mit-1-2-calculus-without-limits"
        and chunk["content_type"] != "exercise"
    ]
    figure_ids = [
        figure_id for chunk in section for figure_id in chunk["figure_ids"]
    ]

    assert figure_ids
    assert all(figure_id.startswith(("fig-1-", "asset-1-")) for figure_id in figure_ids)
    assert figures["asset-1-e670251d267eb84b"]["figure_number"] == "Figure 1.7a"
    assert section[0]["subtype"] == "definition"
    assert section[0]["formulas"]
