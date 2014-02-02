from kivy.uix.boxlayout import BoxLayout
from kivy.properties import (
    AliasProperty,
    DictProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
    ReferenceListProperty
)
from kivy.clock import Clock
from kivy.logger import Logger

from LiSE.gui.kivybits import ClosetButton


class Sizer(ClosetButton):
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.ud['charsheet'] = self.charsheet
            touch.ud['sizer'] = self
            touch.grab(self)
            self.prior_y = self.y
            self.state = 'down'
            touch.ud['sizer_i'] = self.spacer.i
            return True

    def on_touch_move(self, touch):
        if 'sizer' not in touch.ud or touch.ud['sizer'] is not self:
            touch.ungrab(self)
            self.state = 'normal'
            return
        self.center_y = touch.pos
        return True

    def on_touch_up(self, touch):
        if 'sizer' not in touch.ud or touch.ud['sizer'] is not self:
            touch.ungrab(self)
            self.state = 'normal'
            return
        self.state = 'normal'
        return True


class Spacer(BoxLayout):
    csitem = ObjectProperty()
    charsheet = AliasProperty(
        lambda self: self.csitem.charsheet if self.csitem else None,
        lambda self, v: None,
        bind=('csitem',))
    i = AliasProperty(
        lambda self: self.csitem.i if self.csitem else None,
        lambda self, v: None,
        bind=('csitem',))

    def __init__(self, **kwargs):
        _ = lambda x: x
        kwargs['size_hint_y'] = None
        kwargs['height'] = 30
        super(Spacer, self).__init__(**kwargs)
        self.sizer = Sizer(
            spacer=self,
            size_hint_x=0.2)
        self.adder = ClosetButton(
            closet=self.charsheet.character.closet,
            symbolic=True,
            stringname=_('@add'),
            fun=self.charsheet.add_item,
            arg=self.i,
            size_hint_y=0.8)
        self.add_widget(self.sizer)
        self.add_widget(self.adder)


class CharSheetItemButtonBox(BoxLayout):
    csitem = ObjectProperty()


class CharSheetItem(BoxLayout):
    csbone = ObjectProperty()
    content = ObjectProperty()
    spacer = ObjectProperty()
    buttons = ListProperty()
    middle = ObjectProperty()
    item_class = ObjectProperty()
    item_kwargs = DictProperty()
    widspec = ReferenceListProperty(item_class, item_kwargs)
    charsheet = AliasProperty(
        lambda self: self.item_kwargs['charsheet']
        if self.item_kwargs else None,
        lambda self, v: None,
        bind=('item_kwargs',))
    closet = AliasProperty(
        lambda self: self.item_kwargs['charsheet'].character.closet
        if self.item_kwargs else None,
        lambda self, v: None,
        bind=('item_kwargs',))
    mybone = AliasProperty(
        lambda self: self.item_kwargs['mybone']
        if self.item_kwargs and 'mybone' in self.item_kwargs
        else None,
        lambda self, v: None,
        bind=('item_kwargs',))
    i = AliasProperty(
        lambda self: self.csbone.idx if self.csbone else -1,
        lambda self, v: None,
        bind=('csbone',))

    def __init__(self, **kwargs):
        self._trigger_set_bone = Clock.create_trigger(self.set_bone)
        kwargs['orientation'] = 'vertical'
        kwargs['size_hint_y'] = None
        super(CharSheetItem, self).__init__(**kwargs)
        self.finalize()

    def set_bone(self, *args):
        if self.csbone:
            self.closet.set_bone(self.csbone)

    def upd_height(self, *args):
        self.height = self.spacer.top - self.y
        dh = self.height - self.csbone.height
        try:
            wid_before = self.charsheet.i2wid[self.i-1]
            wid_before.y += dh
            wid_before.height -= dh
        except KeyError:
            pass
        if self.csbone and self.height != self.csbone.height:
            self.csbone = self.csbone._replace(height=self.height)
            self.content.height = self.height
            self.buttons.height = self.height
            self._trigger_set_bone()

    def on_touch_move(self, touch):
        if not ('sizer_i' in touch.ud and touch.ud['sizer_i'] == self.i):
            return
        if 'wid_before' in touch.ud:
            return
        touch.ud['wid_after'] = self
        if self.i > 0:
            touch.ud['wid_before'] = self.charsheet.i2wid[self.i-1]

    def finalize(self, *args):
        _ = lambda x: x
        if not (self.item_class and self.item_kwargs):
            Clock.schedule_once(self.finalize, 0)
            return
        self.spacer = Spacer(csitem=self)
        self.middle = BoxLayout()
        self.content = self.item_class(**self.item_kwargs)
        buttonbox = BoxLayout(
            orientation='vertical',
            size_hint_x=0.2)
        self.buttons = [ClosetButton(
            closet=self.closet,
            symbolic=True,
            stringname=_('@del'),
            fun=self.charsheet.del_item,
            arg=self.i)]
        if self.i > 0:
            self.buttons.insert(0, ClosetButton(
                closet=self.closet,
                symbolic=True,
                stringname=_('@up'),
                fun=self.charsheet.move_it_up,
                arg=self.i,
                size_hint_y=0.1))
            if self.i+1 < len(self.charsheet.csitems):
                self.buttons.append(ClosetButton(
                    closet=self.closet,
                    symbolic=True,
                    stringname=_('@down'),
                    fun=self.charsheet.move_it_down,
                    arg=self.i,
                    size_hint_y=0.1))
        for button in self.buttons:
            buttonbox.add_widget(button)
        self.middle.add_widget(self.content)
        self.middle.add_widget(buttonbox)
        self.add_widget(self.spacer)
        self.spacer.bind(top=self.upd_height)
        self.add_widget(self.middle)
        self.height = self.csbone.height
        self.charsheet.i2wid[self.i] = self
