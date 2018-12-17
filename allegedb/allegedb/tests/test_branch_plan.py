import pytest
import allegedb


@pytest.fixture(scope='function')
def orm():
    with allegedb.ORM("sqlite:///:memory:") as it:
        yield it


def test_single_plan(orm):
    g = orm.new_graph('graph')
    g.add_node(0)
    orm.turn = 1
    g.add_node(1)
    with orm.plan():
        orm.turn = 2
        g.add_node(2)
        g.node[2]['clever'] = False
        orm.turn = 3
        g.node[2]['funny'] = True
        g.add_node(3)
        orm.turn = 4
        g.node[2]['successful'] = True
    assert orm.turn == 1
    assert 2 not in g.node
    orm.branch = 'b'
    assert 2 not in g.node
    assert 1 in g
    orm.turn = 2
    assert 2 in g.node
    assert g.node[2].keys() == {'clever'}
    orm.turn = 3
    assert g.node[2]['funny']
    assert 3 in g
    assert g.node[2].keys() == {'funny', 'clever'}
    orm.turn = 4
    assert g.node[2].keys() == {'funny', 'clever', 'successful'}
    orm.turn = 2
    assert g.node[2].keys() == {'clever'}
    g.node[2]['funny'] = False
    assert g.node[2].keys() == {'funny', 'clever'}
    orm.turn = 3
    assert not g.node[2]['funny']
    assert 3 not in g.node
    orm.turn = 4
    assert g.node[2].keys() == {'funny', 'clever'}
    orm.turn = 1
    orm.branch = 'trunk'
    orm.turn = 0
    assert 1 not in g.node
    orm.branch = 'c'
    orm.turn = 2
    assert 1 not in g.node
    assert 2 not in g.node
    orm.turn = 0
    orm.branch = 'trunk'
    orm.turn = 2
    assert 2 in g.node


def test_multi_plan(orm):
    g1 = orm.new_graph(1)
    g2 = orm.new_graph(2)
    with orm.plan():
        g1.add_node(1)
        g1.add_node(2)
        orm.turn = 1
        g1.add_edge(1, 2)
    assert orm.turn == 0
    with orm.plan():
        g2.add_node(1)
        g2.add_node(2)
        orm.turn = 1
        g2.add_edge(1, 2)
    assert orm.turn == 0
    # go to end of turn
    orm.turn = 0
    # contradict the plan
    del g1.node[2]
    assert 1 in g2.node
    assert 2 in g2.node
    orm.turn = 1
    assert 2 not in g1.node
    assert 2 not in g1.edge[1]
    assert 2 in g2.edge[1]