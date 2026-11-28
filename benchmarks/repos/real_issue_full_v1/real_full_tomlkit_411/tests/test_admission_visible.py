import tomlkit


def test_nested_dotted_subtable_can_be_dumped():
    document = tomlkit.parse('root.branch.leaf.value = 7')
    subtable = document['root']
    assert tomlkit.dumps(subtable) == 'branch.leaf.value = 7'
