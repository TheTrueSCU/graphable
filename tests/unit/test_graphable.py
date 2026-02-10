from pytest import raises

from graphable.errors import GraphCycleError
from graphable.graphable import Graphable


class TestGraphable:
    def test_initialization(self):
        ref = "my_ref"
        node = Graphable(ref)
        assert node.reference == ref
        assert len(node.dependents) == 0
        assert len(node.depends_on) == 0
        # Ensure reference is accessible and consistent
        assert node.reference == ref

    def test_dependencies_new(self):
        node_a = Graphable("A")
        node_b = Graphable("B")

        # Test adding a new dependency using the public API
        node_a.add_dependency(node_b)
        assert node_b in node_a.depends_on
        assert node_a in node_b.dependents
        # This call should cover lines 47-51 in _add_depends_on and lines in add_dependency that call _add_dependent indirectly

    def test_dependencies_existing(self):
        node_a = Graphable("A")
        node_b = Graphable("B")

        # Add dependency once
        node_a.add_dependency(node_b)
        assert node_b in node_a.depends_on
        assert node_a in node_b.dependents
        initial_dependents_count_b = len(node_b.dependents)
        initial_depends_on_count_a = len(node_a.depends_on)

        # Add the same dependency again - should not change state or execute internal logic again
        node_a.add_dependency(node_b)
        assert node_b in node_a.depends_on
        assert node_a in node_b.dependents
        # Assert that adding an existing dependency does not increase counts
        assert len(node_a.depends_on) == initial_depends_on_count_a
        assert len(node_b.dependents) == initial_dependents_count_b
        # This tests the 'else' path of _add_depends_on and _add_dependent

    def test_add_dependency_and_dependent_new_items(self):
        node_a = Graphable("A")
        node_b = Graphable("B")
        node_c = Graphable("C")

        # Test _add_dependent for a new item, ensuring the 'if' block is covered
        assert len(node_a.dependents) == 0
        node_a._add_dependent(node_b)  # This call should execute lines 36-38
        assert node_b in node_a.dependents  # Verifies line 37
        assert len(node_a.dependents) == 1  # Verifies line 37

        # Test _add_depends_on for a new item, ensuring the 'if' block is covered
        assert len(node_b.depends_on) == 0
        node_b._add_depends_on(node_a)  # This call should execute lines 47-51
        assert node_a in node_b.depends_on  # Verifies line 48
        assert len(node_b.depends_on) == 1  # Verifies line 48

        # Test adding existing items to ensure they are not re-added (tests else path implicitly)
        node_a._add_dependent(node_b)  # Should hit the 'else' path for _add_dependent
        assert len(node_a.dependents) == 1
        node_b._add_depends_on(node_a)  # Should hit the 'else' path for _add_depends_on
        assert len(node_b.depends_on) == 1

        # Test public API method add_dependency which calls _add_depends_on and dependency._add_dependent
        node_c.add_dependency(node_a)  # node_a is now a dependency of node_c
        assert node_a in node_c.depends_on
        assert node_c in node_a.dependents  # tests _add_dependent called via public API

        # Test public API method add_dependent which calls _add_dependent and dependent._add_depends_on
        node_c.add_dependent(node_b)  # node_b is now a dependent of node_c
        assert node_b in node_c.dependents
        assert (
            node_c in node_b.depends_on
        )  # tests _add_depends_on called via public API

    def test_add_dependents_multiple(self):
        node_a = Graphable("A")
        node_b = Graphable("B")
        node_c = Graphable("C")
        dependents_set = {node_b, node_c}

        # Test adding new dependents
        node_a.add_dependents(dependents_set)  # Covers lines 73-75 (logger and loop)
        assert node_b in node_a.dependents
        assert node_c in node_a.dependents
        assert len(node_a.dependents) == 2
        # Verify reciprocal dependencies (lines 73-75 should be covered by this loop)
        assert node_a in node_b.depends_on
        assert node_a in node_c.depends_on
        assert len(node_b.depends_on) == 1
        assert len(node_c.depends_on) == 1

        # Test adding dependents again with some existing
        node_d = Graphable("D")
        node_a.add_dependents({node_b, node_d})  # node_b already exists, node_d is new
        assert node_b in node_a.dependents
        assert node_d in node_a.dependents
        assert len(node_a.dependents) == 3  # node_b, node_c, node_d
        assert node_a in node_d.depends_on

    def test_add_dependencies_multiple(self):
        node_a = Graphable("A")
        node_b = Graphable("B")
        node_c = Graphable("C")
        dependencies_set = {node_b, node_c}

        # Test adding multiple dependencies
        node_a.add_dependencies(dependencies_set)
        assert node_b in node_a.depends_on
        assert node_c in node_a.depends_on
        assert len(node_a.depends_on) == 2
        # Verify reciprocal dependents
        assert node_a in node_b.dependents
        assert node_a in node_c.dependents

    def test_tags(self):
        node = Graphable("A")
        node.add_tag("t1")
        node.add_tag("t2")
        assert node.tags == {"t1", "t2"}
        # Ensure it's a copy
        node.tags.add("t3")
        assert "t3" not in node.tags
        assert node.tags == {"t1", "t2"}

    def test_remove_tag_existing(self):
        node = Graphable("A")
        node.add_tag("t1")
        assert node.is_tagged("t1")
        node.remove_tag("t1")  # Covers line 175 (discard) and 176 (logger)
        assert not node.is_tagged("t1")
        assert len(node.tags) == 0

    def test_remove_tag_non_existent(self):
        node = Graphable("A")
        assert not node.is_tagged("t1")
        node.remove_tag(
            "t1"
        )  # Should not raise an error, covers line 175 (discard) and 176 (logger)
        assert not node.is_tagged("t1")
        assert len(node.tags) == 0

    def test_reference_property_access(self):
        ref_val = "test_ref"
        node = Graphable(ref_val)
        # Accessing reference property directly
        assert node.reference == ref_val  # Covers lines 153-156
        # Accessing it again after some operations
        node.add_tag("test")
        assert node.reference == ref_val
        node_b = Graphable("B")
        node.add_dependency(node_b)
        assert node.reference == ref_val

    def test_dependents_property_is_copy(self):
        node = Graphable("A")
        deps = node.dependents
        assert isinstance(deps, set)
        # Modifying the returned set shouldn't modify the internal set
        deps.add(Graphable("junk"))
        assert len(node.dependents) == 0

    def test_depends_on_property_is_copy(self):
        node = Graphable("A")
        deps = node.depends_on
        assert isinstance(deps, set)
        deps.add(Graphable("junk"))
        assert len(node.depends_on) == 0

    def test_provides_to_alias(self):
        node_a = Graphable("A")
        node_b = Graphable("B")
        node_a.provides_to(node_b)  # Test the alias
        assert node_b in node_a.dependents
        assert node_a in node_b.depends_on

    def test_requires_alias(self):
        node_a = Graphable("A")
        node_b = Graphable("B")
        node_a.requires(node_b)  # Test the alias
        assert node_b in node_a.depends_on
        assert node_a in node_b.dependents

    def test_cycle_detection(self):
        a = Graphable("A")
        b = Graphable("B")
        c = Graphable("C")

        a.add_dependency(b, check_cycles=True)
        b.add_dependency(c, check_cycles=True)

        # C -> B -> A.  Adding A -> C creates a cycle.
        with raises(GraphCycleError) as excinfo:
            c.add_dependency(a, check_cycles=True)
        assert "would create a cycle" in str(excinfo.value)
        assert excinfo.value.cycle is not None
        assert a in excinfo.value.cycle
        assert b in excinfo.value.cycle
        assert c in excinfo.value.cycle

    def test_cycle_detection_dependent(self):
        a = Graphable("A")
        b = Graphable("B")
        c = Graphable("C")

        a.add_dependent(b, check_cycles=True)
        b.add_dependent(c, check_cycles=True)

        # A -> B -> C. Adding C -> A creates a cycle.
        with raises(GraphCycleError) as excinfo:
            c.add_dependent(a, check_cycles=True)
        assert "would create a cycle" in str(excinfo.value)

    def test_find_path(self):
        a = Graphable("A")
        b = Graphable("B")
        c = Graphable("C")
        d = Graphable("D")

        a.add_dependent(b)
        b.add_dependent(c)
        c.add_dependent(d)

        path = a.find_path(d)
        assert path == [a, b, c, d]

        assert (
            a.find_path(a) is None
        )  # Simple BFS doesn't find self unless there's a loop

        a.add_dependent(a)
        assert a.find_path(a) == [a, a]
