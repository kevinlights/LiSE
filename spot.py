from util import SaveableMetaclass, dictify_row, stringlike


__metaclass__ = SaveableMetaclass


class Spot:
    """Controller for the icon that represents a Place.

    Spot(place, x, y, spotgraph) => a Spot representing the given
    place; at the given x and y coordinates on the screen; in the
    given graph of Spots. The Spot will be magically connected to the other
    Spots in the same way that the underlying Places are connected."""
    tablenames = ["spot"]
    coldecls = {"spot":
                {"dimension": "text",
                 "place": "text",
                 "img": "text",
                 "x": "integer",
                 "y": "integer",
                 "visible": "boolean",
                 "interactive": "boolean"}}
    primarykeys = {"spot": ("dimension", "place")}
    foreignkeys = {"spot":
                   {"dimension, place": ("place", "dimension, name"),
                    "img": ("img", "name")}}

    def __init__(self, dimension, place, img, x, y,
                 visible, interactive, db=None):
        self.dimension = dimension
        self.place = place
        self.img = img
        self.x = x
        self.y = y
        self.visible = visible
        self.interactive = interactive
        if db is not None:
            dimname = None
            placename = None
            if stringlike(self.dimension):
                dimname = self.dimension
            else:
                dimname = self.dimension.name
            if stringlike(self.place):
                placename = self.place
            else:
                placename = self.place.name
            if dimname not in db.spotdict:
                db.spotdict[dimname] = {}
            db.spotdict[dimname][placename] = self

    def __repr__(self):
        return "spot(%i,%i)->%s" % (self.x, self.y, str(self.place))

    def __eq__(self, other):
        return (
            isinstance(other, Spot) and
            self.dimension == other.dimension and
            self.name == other.name)

    def __hash__(self):
        return self.hsh

    def unravel(self, db):
        if stringlike(self.dimension):
            self.dimension = db.dimensiondict[self.dimension]
        if stringlike(self.place):
            self.place = db.placedict[self.dimension.name][self.place]
        if stringlike(self.img):
            self.img = db.imgdict[self.img]

    def getleft(self):
        return self.x - self.r

    def getbot(self):
        return self.y - self.r

    def gettop(self):
        return self.y + self.r

    def getright(self):
        return self.x + self.r

    def getcenter(self):
        return (self.x, self.y)

    def gettup(self):
        return (self.img, self.getleft(), self.getbot())

    def is_visible(self):
        return self.visible

    def is_interactive(self):
        return self.interactive

    def onclick(self, button, modifiers):
        pass

    def dropped(self, x, y, button, modifiers):
        self.grabpoint = None

    def move_with_mouse(self, x, y, dx, dy, buttons, modifiers):
        if self.grabpoint is None:
            self.grabpoint = (x - self.x, y - self.y)
        (grabx, graby) = self.grabpoint
        self.x = x - grabx + dx
        self.y = y - graby + dy


spot_dimension_qryfmt = (
    "SELECT {0} FROM spot WHERE dimension IN ({1})".format(
        ", ".join(Spot.colnames["spot"]), "{0}"))


def read_spots_in_dimensions(db, names):
    qryfmt = spot_dimension_qryfmt
    qrystr = qryfmt.format(", ".join(["?"] * len(names)))
    db.c.execute(qrystr, names)
    r = {}
    for name in names:
        r[name] = {}
    for row in db.c:
        rowdict = dictify_row(row, Spot.colnames["spot"])
        rowdict["db"] = db
        r[rowdict["dimension"]][rowdict["place"]] = Spot(**rowdict)
    return r


def unravel_spots(db, spd):
    for spot in spd.itervalues():
        spot.unravel(db)
    return spd


def unravel_spots_in_dimensions(db, spdd):
    for spots in spdd.itervalues():
        unravel_spots(db, spots)
    return spdd


def load_spots_in_dimensions(db, names):
    return unravel_spots_in_dimensions(db, read_spots_in_dimensions(db, names))
