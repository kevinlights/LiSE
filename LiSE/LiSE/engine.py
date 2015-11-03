# This file is part of LiSE, a framework for life simulation games.
# Copyright (c) 2013-2014 Zachary Spector,  zacharyspector@gmail.com
"""The core of LiSE is an object relational mapper with special
stores for game data and entities, as well as properties for manipulating the
flow of time.

"""
from random import Random
from collections import defaultdict
from sqlite3 import connect

from gorm import ORM as gORM
from gorm.window import window_left
from .xcollections import (
    StringStore,
    FunctionStore,
    GlobalVarMapping,
    CharacterMapping
)
from .character import Character
from .node import Node
from .portal import Portal
from .rule import AllRuleBooks, AllRules
from .query import QueryEngine
from .util import (
    AbstractEngine,
    reify
)


crhandled_defaultdict = lambda: defaultdict(  # character:
    lambda: defaultdict(  # rulebook:
        lambda: defaultdict(  # rule:
            lambda: defaultdict(  # branch:
                set  # ticks handled
            )
        )
    )
)


class AvatarnessCache(object):
    def __init__(self, db):
        self.db_order = defaultdict(  # character:
            lambda: defaultdict(  # graph:
                lambda: defaultdict(  # node:
                    lambda: defaultdict(  # branch:
                        dict  # tick: is_avatar
                    )
                )
            )
        )
        self.user_order = defaultdict(  # graph:
            lambda: defaultdict(  # node:
                lambda: defaultdict(  # character:
                    lambda: defaultdict(  # branch:
                        dict  # tick: is_avatar
                    )
                )
            )
        )
        for row in db.avatarness_dump():
            self.remember(*row)

    def remember(self, character, graph, node, branch, tick, is_avatar):
        self.db_order[character][graph][node][branch][tick] = is_avatar
        self.user_order[graph][node][character][branch][tick] = is_avatar


class Engine(AbstractEngine, gORM):
    """LiSE, the Life Simulator Engine.

    Each instance of LiSE maintains a connection to a database
    representing the state of a simulated world. Simulation rules
    within this world are described by lists of Python functions, some
    of which make changes to the world.

    The top-level data structure within LiSE is the character. Most
    data within the world model is kept in some character or other;
    these will quite frequently represent people, but can be readily
    adapted to represent any kind of data that can be comfortably
    described as a graph or a JSON object. Every change to a character
    will be written to the database.

    LiSE tracks history as a series of ticks. In each tick, each
    simulation rule is evaluated once for each of the simulated
    entities it's been applied to. World changes in a given tick are
    remembered together, such that the whole world state can be
    rewound: simply set the properties ``branch`` and ``tick`` back to
    what they were just before the change you want to undo.

    """
    char_cls = Character
    node_cls = Node
    portal_cls = Portal

    @reify
    def _rulebooks_cache(self):
        assert(self.caching)
        r = defaultdict(list)
        for (rulebook, rule) in self.rule.db.rulebooks_rules():
            r[rulebook].append(rule)
        return r

    @reify
    def _characters_rulebooks_cache(self):
        assert(self.caching)
        r = {}
        for (
                character,
                character_rulebook,
                avatar_rulebook,
                character_thing_rulebook,
                character_place_rulebook,
                character_node_rulebook,
                character_portal_rulebook
        ) in self.db.characters_rulebooks():
            r[character] = {
                'character': character_rulebook,
                'avatar': avatar_rulebook,
                'character_thing': character_thing_rulebook,
                'character_place': character_place_rulebook,
                'character_node': character_node_rulebook,
                'character_portal': character_portal_rulebook
            }
        return r

    @reify
    def _nodes_rulebooks_cache(self):
        assert(self.caching)
        r = defaultdict(dict)
        for (character, node, rulebook) in self.db.nodes_rulebooks():
            r[character][node] = rulebook
        return r

    @reify
    def _portals_rulebooks_cache(self):
        assert(self.caching)
        r = defaultdict(
            lambda: defaultdict(dict)
        )
        for (character, nodeA, nodeB, rulebook) in self.db.portals_rulebooks():
            r[character][nodeA][nodeB] = rulebook
        return r

    @reify
    def _avatarness_cache(self):
        assert(self.caching)
        return AvatarnessCache(self.db)

    @reify
    def _active_rules_cache(self):
        assert(self.caching)
        r = defaultdict(  # rulebook:
            lambda: defaultdict(  # rule:
                lambda: defaultdict(  # branch:
                    dict  # tick: active
                )
            )
        )
        for (rulebook, rule, branch, tick, active) in \
                self.db.dump_active_rules():
            r[rulebook][rule][branch][tick] = active
        return r

    @reify
    def _node_rules_handled_cache(self):
        assert(self.caching)
        r = defaultdict(  # character:
            lambda: defaultdict(  # node:
                lambda: defaultdict(  # rulebook:
                    lambda: defaultdict(  # rule:
                        lambda: defaultdict(  # branch:
                            set  # ticks handled
                        )
                    )
                )
            )
        )
        for (character, node, rulebook, rule, branch, tick) \
                in self.db.dump_node_rules_handled():
            r[character][node][rulebook][rule][branch].add(tick)
        return r

    @reify
    def _portal_rules_handled_cache(self):
        assert(self.caching)
        r = defaultdict(  # character:
            lambda: defaultdict(  # nodeA:
                lambda: defaultdict(  # nodeB:
                    lambda: defaultdict(  # rulebook:
                        lambda: defaultdict(  # rule:
                            lambda: defaultdict(  # branch:
                                set  # ticks handled
                            )
                        )
                    )
                )
            )
        )
        for (character, nodeA, nodeB, idx, rulebook, rule, branch, tick) \
                in self.db.dump_portal_rules_handled():
            r[character][nodeA][nodeB][rulebook][rule][branch].add(tick)
        return r

    @reify
    def _character_rules_handled_cache(self):
        assert(self.caching)
        r = crhandled_defaultdict()
        for (character, rulebook, rule, branch, tick) in \
                self.db.handled_character_rules():
            r[character][rulebook][rule][branch].add(tick)
        return r

    @reify
    def _avatar_rules_handled_cache(self):
        assert(self.caching)
        r = crhandled_defaultdict()
        for (character, rulebook, rule, branch, tick) in \
                self.db.handled_avatar_rules():
            r[character][rulebook][rule][branch].add(tick)
        return r

    @reify
    def _character_thing_rules_handled_cache(self):
        assert(self.caching)
        r = crhandled_defaultdict()
        for (character, rulebook, rule, branch, tick) in \
                self.db.handled_character_thing_rules():
            r[character][rulebook][rule][branch].add(tick)
        return r

    @reify
    def _character_place_rules_handled_cache(self):
        assert(self.caching)
        r = crhandled_defaultdict()
        for (character, rulebook, rule, branch, tick) in \
                self.db.handled_character_place_rules():
            r[character][rulebook][rule][branch].add(tick)
        return r

    @reify
    def _character_node_rules_handled_cache(self):
        assert(self.caching)
        r = crhandled_defaultdict()
        for (character, rulebook, rule, branch, tick) in \
                self.db.handled_character_node_rules():
            r[character][rulebook][rule][branch].add(tick)
        return r

    @reify
    def _character_portal_rules_handled_cache(self):
        assert(self.caching)
        r = crhandled_defaultdict()
        for (character, rulebook, rule, branch, tick) in \
                self.db.handled_character_portal_rules():
            r[character][rulebook][rule][branch].add(tick)
        return r

    @reify
    def _things_cache(self):
        assert(self.caching)
        r = defaultdict(  # character:
            lambda: defaultdict(  # thing:
                lambda: defaultdict(  # branch:
                    dict  # tick: (location, next_location)
                )
            )
        )
        for (character, thing, branch, tick, loc, nextloc) in \
                self.db.things_dump():
            r[character][thing][branch][tick] = (loc, nextloc)
        return r

    @reify
    def _time_listeners(self):
        return []

    @reify
    def codedb(self):
        return connect(self._codedb)

    @reify
    def worlddb(self):
        if hasattr(self.db, 'alchemist'):
            return self.db.alchemist.conn.connection
        else:
            return self.db.connection

    def __init__(
            self,
            worlddb,
            codedb,
            connect_args={},
            alchemy=False,
            caching=True,
            commit_modulus=None,
            random_seed=None,
            sql_rule_polling=False
    ):
        """Store the connections for the world database and the code database;
        set up listeners; and start a transaction

        """
        super().__init__(
            worlddb,
            query_engine_class=QueryEngine,
            connect_args=connect_args,
            alchemy=alchemy,
            caching=caching,
            json_dump=self.json_dump,
            json_load=self.json_load
        )
        self._sql_polling = sql_rule_polling
        self.commit_modulus = commit_modulus
        self.random_seed = random_seed
        self._code_qe = QueryEngine(
            codedb, connect_args, alchemy, self.json_dump, self.json_load
        )
        self._code_qe.initdb()
        self._rules_iter = self._follow_rules()
        # set up the randomizer
        self.rando = Random()
        if 'rando_state' in self.universal:
            self.rando.setstate(self.universal['rando_state'])
        else:
            self.rando.seed(self.random_seed)
            self.universal['rando_state'] = self.rando.getstate()
        self.betavariate = self.rando.betavariate
        self.choice = self.rando.choice
        self.expovariate = self.rando.expovariate
        self.gammaraviate = self.rando.gammavariate
        self.gauss = self.rando.gauss
        self.getrandbits = self.rando.getrandbits
        self.lognormvariate = self.rando.lognormvariate
        self.normalvariate = self.rando.normalvariate
        self.paretovariate = self.rando.paretovariate
        self.randint = self.rando.randint
        self.random = self.rando.random
        self.randrange = self.rando.randrange
        self.sample = self.rando.sample
        self.shuffle = self.rando.shuffle
        self.triangular = self.rando.triangular
        self.uniform = self.rando.uniform
        self.vonmisesvariate = self.rando.vonmisesvariate
        self.weibullvariate = self.rando.weibullvariate

    @reify
    def action(self):
        return FunctionStore(self, self._code_qe, 'actions')

    @reify
    def prereq(self):
        return FunctionStore(self, self._code_qe, 'prereqs')

    @reify
    def trigger(self):
        return FunctionStore(self, self._code_qe, 'triggers')

    @reify
    def function(self):
        return FunctionStore(self, self._code_qe, 'functions')

    @property
    def stores(self):
        return (
            self.action,
            self.prereq,
            self.trigger,
            self.function,
            self.string
        )

    @reify
    def rule(self):
        return AllRules(self, self._code_qe)

    @reify
    def rulebook(self):
        return AllRuleBooks(self, self._code_qe)

    @reify
    def string(self):
        return StringStore(self._code_qe)

    @reify
    def universal(self):
        return GlobalVarMapping(self)

    @reify
    def character(self):
        return CharacterMapping(self)

    def coinflip(self):
        """Return True or False with equal probability."""
        return self.choice((True, False))

    def roll_die(self, d):
        """Roll a die with ``d`` faces. Return the result."""
        return self.randint(1, d)

    def dice(self, n, d):
        """Roll ``n`` dice with ``d`` faces, and yield the results.

        """
        for i in range(0, n):
            yield self.roll_die(d)

    def dice_check(self, n, d, target, comparator=lambda x, y: x <= y):
        """Roll ``n`` dice with ``d`` sides, sum them, and return whether they
        are <= ``target``.

        If ``comparator`` is provided, use it instead of <=.

        """
        return comparator(sum(self.dice(n, d)), target)

    def percent_chance(self, pct):
        """Given a ``pct``% chance of something happening right now, decide at
        random whether it actually happens, and return ``True`` or
        ``False`` as appropriate.

        Values not between 0 and 100 are treated as though they
        were 0 or 100, whichever is nearer.

        """
        if pct <= 0:
            return False
        if pct >= 100:
            return True
        return pct / 100 < self.random()

    def commit(self):
        """Commit to both the world and code databases, and begin a new
        transaction for the world database

        """
        for store in self.stores:
            store.commit()
        super().commit()

    def close(self):
        """Commit changes and close the database."""
        self.commit()
        super().close()

    def __enter__(self):
        """Return myself. For compatibility with ``with`` semantics."""
        return self

    def __exit__(self, *args):
        """Close on exit."""
        self.close()

    def time_listener(self, v):
        """Arrange to call a function whenever my ``branch`` or ``tick``
        changes.

        The arguments will be the old branch and tick followed by the
        new branch and tick.

        """
        if not callable(v):
            raise TypeError("This is a decorator")
        if v not in self._time_listeners:
            self._time_listeners.append(v)
        return v

    def time_unlisten(self, v):
        if v in self._time_listeners:
            self._time_listeners.remove(v)
        return v

    @property
    def branch(self):
        if self._obranch is not None:
            return self._obranch
        return self.db.globl['branch']

    @branch.setter
    def branch(self, v):
        """Set my gorm's branch and call listeners"""
        (b, t) = self.time
        if self.caching:
            if v == b:
                return
            if v not in self._branches:
                parent = b
                child = v
                assert(parent in self._branches)
                self._branch_parents[child] = parent
                self._branches[parent][child] = {}
                self._branches[child] = self._branches[parent][child]
                self._branches_start[child] = t
            self._obranch = v
        self.db.globl['branch'] = v
        if not hasattr(self, 'locktime'):
            for time_listener in self._time_listeners:
                time_listener(b, t, v, t)

    @property
    def tick(self):
        return self.rev

    @tick.setter
    def tick(self, v):
        """Update gorm's ``rev``, and call listeners"""
        if not isinstance(v, int):
            raise TypeError("tick must be integer")
        (branch_then, tick_then) = self.time
        if self.caching:
            if v == self.tick:
                return
            self._orev = v
        self.rev = v
        if not hasattr(self, 'locktime'):
            for time_listener in self._time_listeners:
                time_listener(branch_then, tick_then, branch_then, v)

    @property
    def time(self):
        """Return tuple of branch and tick"""
        return (self.branch, self.tick)

    @time.setter
    def time(self, v):
        """Set my ``branch`` and ``tick``, and call listeners"""
        (branch_then, tick_then) = self.time
        (branch_now, tick_now) = v
        relock = hasattr(self, 'locktime')
        self.locktime = True
        # setting tick and branch in this order makes it practical to
        # track the timestream genealogy
        self.tick = tick_now
        self.branch = branch_now
        if not relock:
            del self.locktime
        if not hasattr(self, 'locktime'):
            for time_listener in self._time_listeners:
                time_listener(
                    branch_then, tick_then, branch_now, tick_now
                )

    def _rule_active(self, rulebook, rule):
        cache = self._active_rules_cache[rulebook][rule]
        for (branch, tick) in self._active_branches(*self.time):
            if branch in cache:
                return cache[branch][
                    window_left(cache[branch].keys(), tick)
                ]
        return False

    def _poll_char_rules(self):
        if not self.caching or self._sql_polling:
            yield from self.db.poll_char_rules(*self.time)
            return

        def handled(rulebook, rule):
            cache = self._character_rules_handled_cache
            return (
                rulebook in cache and
                rule in cache[rulebook] and
                self.branch in cache[rulebook][rule] and
                self.tick in cache[rulebook][rule][self.branch]
            )

        for char in self._characters_rulebooks_cache:
            for (
                    rulemap,
                    rulebook
            ) in self._characters_rulebooks_cache[char].items():
                for rule in self._rulebooks_cache[rulebook]:
                    if (
                        self._rule_active(rulebook, rule) and not
                        handled(rulebook, rule)
                    ):
                        yield (rulemap, char, rulebook, rule)

    def _poll_node_rules(self):
        if not self.caching or self._sql_polling:
            yield from self.db.poll_node_rules(*self.time)
            return
        cache = self._node_rules_handled_cache

        def handled(char, node, rulebook, rule):
            return (
                char in cache and
                node in cache[char] and
                rulebook in cache[char][node] and
                rule in cache[char][rule][rulebook] and
                self.branch in cache[char][rule][rulebook] and
                self.tick in cache[char][rule][rulebook][self.branch]
            )

        for char in self._nodes_rulebooks_cache:
            for (node, rulebook) in self._nodes_rulebooks_cache[char].items():
                for rule in self._rulebooks_cache[rulebook]:
                    if (
                        self._rule_active(rulebook, rule) and not
                        handled(char, node, rulebook, rule)
                    ):
                        yield ('node', char, node, rulebook, rule)

    def _poll_portal_rules(self):
        if not self.caching or self._sql_polling:
            yield from self.db.poll_portal_rules(*self.time)
            return

        def handled(char, nodeA, nodeB, rulebook, rule):
            cache = self._portal_rules_handled_cache
            return (
                char in cache and
                nodeA in cache[char] and
                nodeB in cache[char][nodeA] and
                rulebook in cache[char][nodeA][nodeB] and
                rule in cache[char][nodeA][nodeB][rulebook] and
                self.branch in cache[char][nodeA][nodeB][rulebook][rule] and
                self.tick in cache[char][nodeA][nodeB][rulebook][rule][
                    self.branch
                ]
            )

        cache = self._portals_rulebooks_cache
        for char in cache:
            for nodeA in cache[char]:
                for (nodeB, rulebook) in cache[char][nodeA].items():
                    for rule in self._rulebooks_cache[rulebook]:
                        if (
                            self._rule_active(rulebook, rule) and not
                            handled(char, nodeA, nodeB, rulebook, rule)
                        ):
                            yield (
                                'portal',
                                char,
                                nodeA,
                                nodeB,
                                rulebook,
                                rule
                            )

    def _poll_rules(self):
        """Iterate over tuples containing rules yet unresolved in the current tick.

        The tuples are of the form: ``(ruletype, character, entity,
        rulebook, rule)`` where ``ruletype`` is what kind of entity
        the rule is about (character', 'thing', 'place', or
        'portal'), and ``entity`` is the :class:`Place`,
        :class:`Thing`, or :class:`Portal` that the rule is attached
        to. For character-wide rules it is ``None``.

        """
        for (
                rulemap, character, rulebook, rule
        ) in self._poll_char_rules():
            try:
                yield (
                    rulemap,
                    self.character[character],
                    None,
                    rulebook,
                    self.rule[rule]
                )
            except KeyError:
                continue
        for (
                character, node, rulebook, rule
        ) in self._poll_node_rules():
            try:
                c = self.character[character]
                n = c.node[node]
            except KeyError:
                continue
            typ = 'thing' if hasattr(n, 'location') else 'place'
            yield typ, c, n, rulebook, self.rule[rule]
        for (
                character, a, b, i, rulebook, rule
        ) in self._poll_portal_rules():
            try:
                c = self.character[character]
                yield 'portal', c.portal[a][b], rulebook, self.rule[rule]
            except KeyError:
                continue

    def _handled_thing_rule(self, char, thing, rulebook, rule, branch, tick):
        if self.caching:
            cache = self._node_rules_handled_cache
            cache[char][thing][rulebook][rule][branch].add(tick)
        self.db.handled_thing_rule(
            char, thing, rulebook, rule, branch, tick
        )

    def _handled_place_rule(self, char, place, rulebook, rule, branch, tick):
        if self.caching:
            cache = self._node_rules_handled_cache
            cache[char][place][rulebook][rule][branch].add(tick)
        self.db.handled_place_rule(
            char, place, rulebook, rule, branch, tick
        )

    def _handled_portal_rule(
            self, char, nodeA, nodeB, rulebook, rule, branch, tick
    ):
        if self.caching:
            cache = self._portal_rules_handled_cache
            cache[char][nodeA][nodeB][rulebook][rule][branch].add(tick)
        self.db.handled_portal_rule(
            char, nodeA, nodeB, rulebook, rule, branch, tick
        )

    def _handled_character_rule(
            self, typ, char, rulebook, rule, branch, tick
    ):
        if self.caching:
            cache = {
                'character': self._character_rules_handled_cache,
                'avatar': self._avatar_rules_handled_cache,
                'character_thing': self._character_thing_rules_handled_cache,
                'character_place': self._character_place_rules_handled_cache,
                'character_node': self._character_node_rules_handled_cache,
                'character_portal': self._character_portal_rules_handled_cache,
            }[typ]
            cache[char][rulebook][rule][branch].add(tick)
        self.db.handled_character_rule(
            typ, char, rulebook, rule, branch, tick
        )

    def _follow_rules(self):
        """For each rule in play at the present tick, call it and yield a
        tuple describing the results.

        Tuples are of the form: ``(returned, rulename, ruletype,
        rulebook)`` where ``returned`` is whatever the rule itself
        returned upon being called, and ``ruletype`` is what sort of
        entity the rule applies to.

        """
        (branch, tick) = self.time
        for (typ, character, entity, rulebook, rule) in self._poll_rules():
            def follow(*args):
                return (rule(self, *args), rule.name, typ, rulebook)

            if typ in ('thing', 'place', 'portal'):
                yield follow(character, entity)
                if typ == 'thing':
                    self._handled_thing_rule(
                        character.name,
                        entity.name,
                        rulebook,
                        rule.name,
                        branch,
                        tick
                    )
                elif typ == 'place':
                    self._handled_place_rule(
                        character.name,
                        entity.name,
                        rulebook,
                        rule.name,
                        branch,
                        tick
                    )
                else:
                    self._handled_portal_rule(
                        character.name,
                        entity.origin.name,
                        entity.destination.name,
                        rulebook,
                        rule.name,
                        branch,
                        tick
                    )
            else:
                if typ == 'character':
                    yield follow(character)
                elif typ == 'avatar':
                    for avatar in character.avatars():
                        yield follow(character, avatar)
                elif typ == 'character_thing':
                    for thing in character.thing.values():
                        yield follow(character, thing)
                elif typ == 'character_place':
                    for place in character.place.values():
                        yield follow(character, place)
                elif typ == 'character_node':
                    for node in character.node.values():
                        yield follow(character, node)
                elif typ == 'character_portal':
                    for portal in character.portal.values():
                        yield follow(character, portal)
                else:
                    raise ValueError('Unknown type of rule')
                self._handled_character_rule(
                    typ, character.name, rulebook, rule.name, branch, tick
                )

    def advance(self):
        """Follow the next rule, or if there isn't one, advance to the next
        tick.

        """
        try:
            r = next(self._rules_iter)
        except StopIteration:
            self.tick += 1
            self._rules_iter = self._follow_rules()
            self.universal['rando_state'] = self.rando.getstate()
            if self.commit_modulus and self.tick % self.commit_modulus == 0:
                self.commit()
            r = None
        return r

    def next_tick(self):
        """Call ``advance`` repeatedly, appending its results to a list until
        the tick has ended.  Return the list.

        """
        curtick = self.tick
        r = []
        while self.tick == curtick:
            r.append(self.advance())
        # The last element is always None, but is not a sentinel; any
        # rule may return None.
        return r[:-1]

    def new_character(self, name, **kwargs):
        """Create and return a new :class:`Character`."""
        self.add_character(name, **kwargs)
        return self.character[name]

    def add_character(self, name, data=None, **kwargs):
        """Create the :class:`Character` so it'll show up in my ``character``
        mapping.

        """
        self.new_digraph(name, data, **kwargs)
        ch = Character(self, name)
        if data is not None:
            for a in data.adj:
                for b in data.adj[a]:
                    assert(
                        a in ch.adj and
                        b in ch.adj[a]
                    )
        if hasattr(self.character, '_cache'):
            self.character._cache[name] = ch

    def del_character(self, name):
        """Remove the Character from the database entirely.

        This also deletes all its history. You'd better be sure.

        """
        self.db.del_character(name)
        self.del_graph(name)
        del self.character[name]

    def _is_thing(self, character, node):
        """Private utility function to find out if a node is a Thing or not.

        ``character`` argument must be the name of a character, not a
        :class:`Character` object. Likewise ``node`` argument is the
        node's ID.

        """
        if self.caching:
            try:
                cache = self._things_cache[character][node]
            except KeyError:
                return False
            for (branch, tick) in self._active_branches():
                try:
                    return cache[branch][
                        window_left(cache[branch].keys(), tick)
                    ]
                except (KeyError, ValueError):
                    continue
            return False
        return self.db.node_is_thing(character, node, *self.time)

    def _node_exists(self, character, node):
        if self.caching:
            try:
                cache = self._nodes_cache[character][node]
            except KeyError:
                return False
            for (branch, tick) in self._active_branches():
                try:
                    return cache[branch][
                        window_left(cache[branch].keys(), tick)
                    ]
                except (KeyError, ValueError):
                    continue
            return False
        return self.db.node_exists(character, node, *self.time)
