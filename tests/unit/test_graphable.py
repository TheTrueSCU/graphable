from graphable.graphable import Graphable


class TestGraphable:
    def test_initialization(self):
        ref = "my_ref"
        node = Graphable(ref)
        assert node.reference == ref
        assert len(node.dependents) == 0
        assert len(node.depends_on) == 0

    def test_dependencies(self):
        node_a = Graphable("A")
        node_b = Graphable("B")

        # Manually verify internal methods (though usually we test public API, these are used by Graph)
        node_a._add_dependent(node_b)
        assert node_b in node_a.dependents

        node_b._add_depends_on(node_a)
        assert node_a in node_b.depends_on

    def test_tags(self):
        node = Graphable("A")
        node.add_tag("t1")
        node.add_tag("t2")
        assert node.tags == {"t1", "t2"}
        # Ensure it's a copy
        node.tags.add("t3")
        assert "t3" not in node.tags
        assert node.tags == {"t1", "t2"}

    def test_remove_tag(self):
        node = Graphable("A")
        node.add_tag("t1")
        assert node.is_tagged("t1")
        node.remove_tag("t1")
        assert not node.is_tagged("t1")

    def test_dependents_property_is_copy(self):
        node = Graphable("A")
        deps = node.dependents
        # Modifying the returned set shouldn't modify the internal set
        deps.add("junk")
        assert len(node.dependents) == 0

    def test_depends_on_property_is_copy(self):
        node = Graphable("A")
        deps = node.depends_on
        deps.add("junk")
        assert len(node.depends_on) == 0
