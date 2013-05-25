import pyglet
#from util import getLoggerIfLogging, DEBUG

#logger = getLoggerIfLogging(__name__)


"""All the graphics code unique to LiSE."""


class GameWindow:
    """Instantiates a Pyglet window and displays the given board in it."""
    arrowhead_angle = 45
    arrowhead_len = 10

    def __init__(self, gamestate, boardname, batch=None):
        self.db = gamestate.db
        self.gamestate = gamestate
        self.board = self.db.boarddict[boardname]

        self.boardgroup = pyglet.graphics.OrderedGroup(0)
        self.edgegroup = pyglet.graphics.OrderedGroup(1)
        self.spotgroup = pyglet.graphics.OrderedGroup(2)
        self.pawngroup = pyglet.graphics.OrderedGroup(3)
        self.menugroup = pyglet.graphics.OrderedGroup(4)
        self.calendargroup = pyglet.graphics.OrderedGroup(4)
        self.cellgroup = pyglet.graphics.OrderedGroup(5)
        self.labelgroup = pyglet.graphics.OrderedGroup(6)

        self.pressed = None
        self.hovered = None
        self.grabbed = None
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_dx = 0
        self.mouse_dy = 0
        self.mouse_buttons = 0
        self.mouse_mods = 0
        self.view_left = 0
        self.prev_view_left = 0
        self.prev_view_bot = 0
        self.view_bot = 0

        self.to_mouse = (
            self.board.pawndict.values() +
            self.board.spotdict.values())
        for menu in self.board.menudict.itervalues():
            self.to_mouse.extend(menu.items)

        window = pyglet.window.Window()
        if batch is None:
            batch = pyglet.graphics.Batch()

        self.window = window
        self.width = self.window.width
        self.height = self.window.height
        self.batch = batch
        self.menus = self.board.menudict.values()
        self.spots = self.board.spotdict.values()
        self.pawns = self.board.pawndict.values()
        self.calcols = []
        for pawn in self.pawns:
            if hasattr(pawn, 'calcol'):
                self.calcols.append(pawn.calcol)

        self.calendar = self.board.calendar
        self.calendar.set_gw(self)
        for menu in self.board.menudict.itervalues():
            menu.set_gw(self)
        self.drawn_board = None
        self.drawn_edges = None

        self.onscreen = set()

        @window.event
        def on_draw():
            """Draw the background image; all spots, pawns, and edges on the
board; all visible menus; and the calendar, if it's visible."""
            # draw the background image
            x = -1 * self.view_left
            y = -1 * self.view_bot
            s = pyglet.sprite.Sprite(
                self.board.wallpaper, x, y,
                batch=self.batch, group=self.boardgroup)
            try:
                self.drawn_board.delete()
            except AttributeError:
                pass
            self.drawn_board = s
            # if the board has moved since last frame, then
            # so has everything on it.
            # redraw_all = (self.view_left != self.prev_view_left or
            #               self.view_bot != self.prev_view_bot)
            # if redraw_all:
            #     self.onscreen = set()
            # self.prev_view_left = self.view_left
            # self.prev_view_bot = self.view_bot
            # draw the edges, representing portals
            e = []
            for dests in self.board.dimension.portalorigdestdict.itervalues():
                for port in dests.itervalues():
                    origspot = port.orig.spot
                    destspot = port.dest.spot
                    edge = (origspot.x, origspot.y, destspot.x, destspot.y)
                    e.extend(edge)
            try:
                self.drawn_edges.delete()
            except AttributeError:
                pass
            self.drawn_edges = self.batch.add(
                len(e) / 2, pyglet.graphics.GL_LINES,
                self.edgegroup, ('v2i', e))
            # draw the spots, representing places
            for spot in self.board.spotdict.itervalues():
                newstate = spot.get_state_tup()
                if newstate in self.onscreen:
                    continue
                self.onscreen.discard(spot.oldstate)
                self.onscreen.add(newstate)
                spot.oldstate = newstate
                try:
                    spot.sprite.delete()
                except AttributeError:
                    pass
                if spot.is_visible():
                    (x, y) = spot.getcoords()
                    spot.sprite = pyglet.sprite.Sprite(
                        spot.img, x, y, batch=self.batch,
                        group=self.spotgroup)
            # draw the pawns, representing things
            for pawn in self.board.pawndict.itervalues():
                newstate = pawn.get_state_tup()
                if newstate in self.onscreen:
                    continue
                self.onscreen.discard(pawn.oldstate)
                self.onscreen.add(newstate)
                pawn.oldstate = newstate
                try:
                    pawn.sprite.delete()
                except AttributeError:
                    pass
                if pawn.is_visible():
                    (x, y) = pawn.getcoords()
                    pawn.sprite = pyglet.sprite.Sprite(
                        pawn.img, x, y, batch=self.batch,
                        group=self.pawngroup)
            # draw the menus, really just their backgrounds for the moment
            for menu in self.board.menudict.itervalues():
                for menu_item in menu:
                    newstate = menu_item.get_state_tup()
                    if newstate in self.onscreen:
                        continue
                    self.onscreen.discard(menu_item.oldstate)
                    self.onscreen.add(newstate)
                    menu_item.oldstate = newstate
                    try:
                        menu_item.label.delete()
                    except AttributeError:
                        pass
                    if menu.is_visible() and menu_item.is_visible():
                        sty = menu.style
                        if menu_item.hovered:
                            color = sty.fg_active.tup
                        else:
                            color = sty.fg_inactive.tup
                        menu_item.label = pyglet.text.Label(
                        menu_item.text,
                        sty.fontface,
                        sty.fontsize,
                        color=color,
                        x=menu_item.getleft(),
                        y=menu_item.getbot(),
                        batch=self.batch,
                        group=self.labelgroup)
                newstate = menu.get_state_tup()
                if newstate in self.onscreen:
                    continue
                self.onscreen.discard(menu.oldstate)
                self.onscreen.add(newstate)
                menu.oldstate = newstate
                try:
                    menu.sprite.delete()
                except AttributeError:
                    pass
                if menu.is_visible():
                    image = (
                        menu.inactive_pattern.create_image(
                            menu.getwidth(),
                            menu.getheight()))
                    menu.sprite = pyglet.sprite.Sprite(
                        image, menu.getleft(), menu.getbot(),
                        batch=self.batch, group=self.menugroup)

            # draw the calendar
            newstate = self.calendar.get_state_tup()
            if newstate not in self.onscreen:
                self.onscreen.add(newstate)
                self.onscreen.discard(self.calendar.oldstate)
                self.calendar.oldstate = newstate
                for calcol in self.calcols:
                    try:
                        calcol.sprite.delete()
                    except AttributeError:
                        pass
                    if (
                            self.calendar.is_visible() and
                            calcol.is_visible()):
                        image = calcol.inactive_pattern.create_image(
                            calcol.getwidth(), calcol.getheight())
                        calcol.sprite = pyglet.sprite.Sprite(
                            image, calcol.getleft(), calcol.getbot(),
                            batch=self.batch, group=self.calendargroup)
                    for cel in calcol.celldict.itervalues():
                        try:
                            cel.sprite.delete()
                        except AttributeError:
                            pass
                        try:
                            cel.label.delete()
                        except AttributeError:
                            pass
                        if cel.is_visible() and calcol.is_visible() and self.calendar.is_visible():
                            if self.hovered == cel:
                                pat = cel.active_pattern
                                color = cel.style.fg_active.tup
                            else:
                                pat = cel.inactive_pattern
                                color = cel.style.fg_inactive.tup
                            image = pat.create_image(
                                cel.getwidth(), cel.getheight())
                            cel.sprite = pyglet.sprite.Sprite(
                                image, cel.getleft(), cel.getbot(),
                                batch=self.batch, group=self.cellgroup)
                            cel.label = pyglet.text.Label(
                                cel.text, cel.style.fontface,
                                cel.style.fontsize, color=color,
                                x = cel.getleft(),
                                y = cel.label_bot(),
                                batch=self.batch, group=self.labelgroup)
            # well, I lied. I was really only adding those things to the batch.
            # NOW I'll draw them.
            self.batch.draw()
            self.resized = False

        @window.event
        def on_mouse_motion(x, y, dx, dy):
            """Find the widget, if any, that the mouse is over, and highlight
it."""
            if self.hovered is None:
                for menu in self.menus:
                    if (
                            x > menu.getleft() and
                            x < menu.getright() and
                            y > menu.getbot() and
                            y < menu.gettop()):
                        for item in menu.items:
                            if (
                                    x > item.getleft() and
                                    x < item.getright() and
                                    y > item.getbot() and
                                    y < item.gettop()):
                                if hasattr(item, 'set_hovered'):
                                    # logger.log(
                                    #     DEBUG,
                                    #     "Menu item %d of menu %s hovered.",
                                    #     item.idx, item.menu.name)
                                    item.set_hovered()
                                self.hovered = item
                                return
                for spot in self.spots:
                    if (
                            x > spot.getleft() and
                            x < spot.getright() and
                            y > spot.getbot() and
                            y < spot.gettop()):
                        if hasattr(spot, 'set_hovered'):
                            # logger.log(
                            #     DEBUG,
                            #     "Spot for place %s hovered.",
                            #     spot.place.name)
                            spot.set_hovered()
                        self.hovered = spot
                        return
                for pawn in self.pawns:
                    if (
                            x > pawn.getleft() and
                            x < pawn.getright() and
                            y > pawn.getbot() and
                            y < pawn.gettop()):
                        if hasattr(pawn, 'set_hovered'):
                            # logger.log(
                            #     DEBUG,
                            #     "Pawn for thing %s hovered.",
                            #     pawn.thing.name)
                            pawn.set_hovered()
                        self.hovered = pawn
                        return
            else:
                if (
                        x < self.hovered.getleft() or
                        x > self.hovered.getright() or
                        y < self.hovered.getbot() or
                        y > self.hovered.gettop()):
                    if hasattr(self.hovered, 'unset_hovered'):
                        # logger.log(DEBUG, "Unhovered.")
                        self.hovered.unset_hovered()
                    self.hovered = None

        @window.event
        def on_mouse_press(x, y, button, modifiers):
            """If there's something already highlit, and the mouse is still over
it when pressed, it's been half-way clicked; remember this."""
            if self.hovered is None:
                return
            else:
                self.pressed = self.hovered
                if hasattr(self.pressed, 'set_pressed'):
                    # logger.log(DEBUG, "Pressed.")
                    self.pressed.set_pressed()

        @window.event
        def on_mouse_release(x, y, button, modifiers):
            """If something was being dragged, drop it. If something was being
pressed but not dragged, it's been clicked. Otherwise do nothing."""
            if self.grabbed is not None:
                if hasattr(self.grabbed, 'dropped'):
                    # logger.log(DEBUG, "Dropped.")
                    self.grabbed.dropped(x, y, button, modifiers)
                self.grabbed = None
            elif (self.pressed is not None and
                  x > self.pressed.getleft() and
                  x < self.pressed.getright() and
                  y > self.pressed.getbot() and
                  y < self.pressed.gettop() and
                  hasattr(self.pressed, 'onclick')):
                # logger.log(DEBUG, "Clicked.")
                self.pressed.onclick(button, modifiers)
            if self.pressed is not None:
                if hasattr(self.pressed, 'unset_pressed'):
                    # logger.log(DEBUG, "Unpressed.")
                    self.pressed.unset_pressed()
                self.pressed = None

        @window.event
        def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
            """If the thing previously pressed has a move_with_mouse method, use
it."""
            if self.grabbed is not None:
                # logger.log(DEBUG, "Moved %d by %d.", dx, dy)
                self.grabbed.move_with_mouse(x, y, dx, dy, buttons, modifiers)
            elif (self.pressed is not None and
                  x > self.pressed.getleft() and
                  x < self.pressed.getright() and
                  y > self.pressed.getbot() and
                  y < self.pressed.gettop() and
                  hasattr(self.pressed, 'move_with_mouse')):
                # logger.log(DEBUG, "Grabbed at %d, %d.", x, y)
                self.grabbed = self.pressed
            else:
                if self.pressed is not None:
                    self.pressed.unset_pressed()
                    self.pressed = None
                self.grabbed = None

        @window.event
        def on_resize(w, h):
            """Inform the on_draw function that the window's been resized."""
            self.width = w
            self.height = h
            self.resized = True

    def getwidth(self):
        return self.window.width

    def getheight(self):
        return self.window.height
