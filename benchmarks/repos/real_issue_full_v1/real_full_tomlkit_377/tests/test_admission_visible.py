import tomlkit


def test_multiple_empty_children_do_not_emit_parent_header():
    doc = tomlkit.document()
    outer = tomlkit.table()
    outer.add("north", tomlkit.table())
    outer.add("south", tomlkit.table())
    doc.add("region", outer)
    result = tomlkit.dumps(doc)
    assert "[region]" not in result.splitlines()
    assert "[region.north]" in result
    assert "[region.south]" in result
