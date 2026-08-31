from backend.textbook import catalog_tree, get_section


def test_catalog_includes_expandable_chapter_six():
    tree = catalog_tree()
    chapter_six = next(ch for ch in tree["chapters"] if ch["id"] == "mit-ch6")
    labels = [section["title"] for section in chapter_six["sections"]]
    assert "6.1 An Overview" in labels
    assert "6.4 Logarithms" in labels
    assert "6.7 Hyperbolic Functions" in labels


def test_section_lookup_uses_mit_numbering():
    info = get_section("mit-3-1-linear-approximation")
    assert info["display_title"] == "3.1 Linear Approximation"
    assert info["chapter_title"] == "3 Applications of the Derivative"
