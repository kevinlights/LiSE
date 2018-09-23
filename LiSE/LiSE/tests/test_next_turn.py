"""Tests for the rules engine's basic polling functionality"""

from .util import engy


def test_character_dot_rule(engy):
    char = engy.new_character('who')

    @char.rule(always=True)
    def yes(char):
        char.stat['run'] = True

    engy.next_turn()
    btt = engy.btt()
    assert char.stat['run']
    engy.time = 'trunk', 0
    engy.tick = 0
    assert 'run' not in char.stat
    engy.next_turn()
    assert btt == engy.btt()
    assert char.stat['run']


def test_avatar_dot_rule(engy):
    char = engy.new_character('char')
    graph = engy.new_character('graph')
    av = graph.new_place('av')
    char.add_avatar(av)
    starttick = engy.tick

    @char.avatar.rule(always=True)
    def yes(av):
        av['run'] = True

    engy.next_turn()
    btt = engy.btt()
    assert av['run']
    engy.time = 'trunk', 0
    engy.tick = starttick
    assert 'run' not in av
    engy.next_turn()
    assert btt == engy.btt()
    assert av['run']


def test_thing_dot_rule(engy):
    char = engy.new_character('char')
    place = char.new_place('place')
    thing = place.new_thing('thing')
    starttick = engy.tick

    @char.thing.rule(always=True)
    def yes(thing):
        thing['run'] = True

    engy.next_turn()
    btt = engy.btt()
    assert thing['run']
    engy.time = 'trunk', 0
    engy.tick = starttick
    assert 'run' not in thing
    engy.next_turn()
    assert btt == engy.btt()
    assert thing['run']


def test_place_dot_rule(engy):
    char = engy.new_character('char')
    place = char.new_place('place')
    starttick = engy.tick

    @char.place.rule(always=True)
    def yes(plac):
        plac['run'] = True

    engy.next_turn()
    btt = engy.btt()
    assert place['run']
    engy.time = 'trunk', 0
    engy.tick = starttick
    assert 'run' not in place
    engy.next_turn()
    assert btt == engy.btt()
    assert place['run']


def test_portal_dot_rule(engy):
    char = engy.new_character('char')
    orig = char.new_place('orig')
    dest = char.new_place('dest')
    port = orig.one_way(dest)
    starttick = engy.tick

    @char.portal.rule(always=True)
    def yes(portl):
        portl['run'] = True

    engy.next_turn()
    btt = engy.btt()
    assert port['run']
    engy.time = 'trunk', 0
    engy.tick = starttick
    assert 'run' not in port
    engy.next_turn()
    assert btt == engy.btt()
    assert port['run']


def test_node_rule(engy):
    char = engy.new_character('char')
    place = char.new_place('place')
    thing = place.new_thing('thing')
    starttick = engy.tick

    @place.rule(always=True)
    def yes(plac):
        plac['run'] = True

    @thing.rule(always=True)
    def definitely(thig):
        thig['run'] = True

    engy.next_turn()
    btt = engy.btt()
    assert place['run']
    assert thing['run']
    engy.time = 'trunk', 0
    engy.tick = starttick
    assert 'run' not in place
    assert 'run' not in thing
    engy.next_turn()
    assert btt == engy.btt()
    assert place['run']
    assert thing['run']


def test_portal_rule(engy):
    char = engy.new_character('char')
    orig = char.new_place('orig')
    dest = char.new_place('dest')
    port = orig.one_way(dest)
    starttick = engy.tick

    @port.rule(always=True)
    def yes(portl):
        portl['run'] = True

    engy.next_turn()
    btt = engy.btt()
    assert port['run']
    engy.time = 'trunk', 0
    engy.tick = starttick
    assert 'run' not in port
    engy.next_turn()
    assert btt == engy.btt()
    assert port['run']