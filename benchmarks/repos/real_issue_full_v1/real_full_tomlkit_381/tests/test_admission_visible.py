import tomlkit


def test_array_of_tables_without_final_newline_roundtrips():
    source = '[[servers]]\nname = "alpha"\n\n[meta]\n\n[[servers]]\nname = "beta"'
    rendered = tomlkit.dumps(tomlkit.parse(source))
    assert tomlkit.parse(rendered) == tomlkit.parse(source)
    assert '"beta"[meta]' not in rendered
