"""The main window: a toolbar shell, two cards and a floating action bar, themed from tokens.

A working sample to replace piece by piece: the Run button queues a job on the worker, shows a pending row at
once and fills it in when the job ends."""
import time

from PySide6.QtCore import QSettings, QSize, Qt
from PySide6.QtGui import QAction, QActionGroup, QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (QAbstractButton, QApplication, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
                               QListWidget, QListWidgetItem, QMainWindow, QMenu, QSizePolicy, QSplitter,
                               QStackedWidget, QToolBar, QVBoxLayout, QWidget)

from .icons import ICON_SIZE, app_icon, dot_pixmap, icon
from .theme import THEME_ICONS, THEME_MODES, apply_theme
from .widgets import EmptyState, Pill, card, floating, gap, plain_label, segmented, shade, tool_button
from .worker import Worker

APP_NAME = "__App Name__"
ORG = "__app__"
PENDING = Qt.ItemDataRole.UserRole + 1      # a row for a job that is still running
EDIT_HINT = "Edit: Run queues a job - Ctrl+2 for Inspect"
INSPECT_HINT = "Inspect: nothing runs - Ctrl+1 for Edit"
THEME_TIPS = {mode: f"Theme: {mode.title()} (click to change)" for mode in THEME_MODES}


def sample_task():
    time.sleep(0.3)
    return "Finished"


class MainWindow(QMainWindow):
    def __init__(self, worker=None, settings=None, targets=(), task=sample_task):
        super().__init__()
        self.worker = worker or Worker()
        self.task, self.targets, self.target = task, list(targets), (targets[0] if targets else "Local")
        self.settings = settings if settings is not None else QSettings(ORG, APP_NAME)
        mode = self.settings.value("theme", "system")
        self.theme_mode = mode if mode in THEME_MODES else "system"
        self.t = apply_theme(QApplication.instance(), self.theme_mode)
        self._icons, self.rows = [], {}
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(app_icon())
        self._toolbar()
        self.items = QListWidget()
        self.items_empty = EmptyState(self.t, "inspect", "Nothing here yet", "Items show here once a job adds them.")
        self.items_stack = QStackedWidget()
        self.items_stack.addWidget(self.items_empty)
        self.items_stack.addWidget(self.items)
        self.log = QListWidget()
        for view in (self.items, self.log):
            view.setIconSize(ICON_SIZE)            # Qt's default draws row icons far larger than the text
        self.count = plain_label("0", "chip")
        left = self._pane("Items", self.items_stack, self.count)
        right = self._pane("Activity", self.log)
        self.hint = plain_label(EDIT_HINT, "hint")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bar = self._action_bar()
        self.cards = [card(left, self.t), card(right, self.t)]
        split = QSplitter()
        split.setHandleWidth(4)                    # the cards' shadow room already spaces them
        split.setChildrenCollapsible(False)
        for widget in self.cards:
            split.addWidget(widget)
        ground = QWidget()
        ground.setObjectName("ground")
        outer = QVBoxLayout(ground)
        outer.setContentsMargins(16, 8, 16, 8)
        outer.addWidget(split, 1)
        outer.addWidget(self.bar, 0, Qt.AlignmentFlag.AlignHCenter)
        outer.addWidget(self.hint)
        self.setCentralWidget(ground)
        self.worker.finished.connect(self._finished)
        self.worker.failed.connect(self._failed)
        for button in self.findChildren(QAbstractButton):    # a mouse click leaves no focus ring; Tab still does
            button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        for keys, slot in (("Ctrl+1", self.edit_mode.trigger), ("Ctrl+2", self.inspect_mode.trigger),
                           ("Ctrl+R", self.run)):
            QShortcut(QKeySequence(keys), self, activated=slot)
        self.resize(1100, 720)

    # ------------------------------------------------------------------ layout
    def _toolbar(self):
        bar = QToolBar("Main")
        bar.setObjectName("shell")
        bar.setMovable(False)
        bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        bar.setIconSize(ICON_SIZE)
        self.addToolBar(bar)
        bar.addWidget(plain_label(APP_NAME, "product"))
        bar.addWidget(gap())
        self.pill = Pill()
        self.pill.clicked.connect(self._target_menu)
        bar.addWidget(self.pill)
        bar.addWidget(gap())
        modes = QActionGroup(self)
        modes.setExclusive(True)
        self.edit_mode = self._iconed(QAction("Edit", self, checkable=True, checked=True), "edit", on="accent_ink")
        self.edit_mode.setToolTip("Edit\nRun queues jobs and the results are listed")
        self.inspect_mode = self._iconed(QAction("Inspect", self, checkable=True), "inspect", on="accent_ink")
        self.inspect_mode.setToolTip("Inspect\nClicks select; nothing runs")
        for action, mode in ((self.edit_mode, "edit"), (self.inspect_mode, "inspect")):
            modes.addAction(action)
            action.triggered.connect(lambda _=False, m=mode: self._mode(m))
        bar.addWidget(segmented((self.edit_mode, self.inspect_mode)))
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        bar.addWidget(spacer)
        self.theme_action = QAction("Theme", self)
        self.theme_action.triggered.connect(self.next_theme)
        bar.addAction(self.theme_action)
        self.theme_button = bar.widgetForAction(self.theme_action)
        self.theme_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.theme_button.setAccessibleName("Theme")
        self.toolbar = bar
        self._theme_look()
        self._show_target()

    def _pane(self, title, body, chip=None):
        pane = QWidget()
        column = QVBoxLayout(pane)
        column.setContentsMargins(10, 8, 10, 8)
        head = QHBoxLayout()
        head.addWidget(plain_label(title, "title"))
        if chip:
            head.addWidget(chip)
        head.addStretch(1)
        column.addLayout(head)
        column.addWidget(body, 1)
        return pane

    def _action_bar(self):
        box = QFrame()
        box.setObjectName("bar")
        box.setGraphicsEffect(QGraphicsDropShadowEffect(box))
        row = QHBoxLayout(box)
        row.setContentsMargins(8, 6, 8, 6)
        row.setSpacing(4)
        self.run_action = self._iconed(QAction("Run", self), "run")
        self.run_action.setToolTip("Run\nQueues the sample job; its row shows at once and fills in when it ends.")
        self.run_action.triggered.connect(self.run)
        self.clear_action = self._iconed(QAction("Clear", self), "clear")
        self.clear_action.setToolTip("Clear\nEmpties both lists.")
        self.clear_action.triggered.connect(self.clear)
        for action in (self.run_action, self.clear_action):
            row.addWidget(tool_button(action))
        return floating(box, self.t)

    def showEvent(self, event):
        # Qt applies the toolbar's QSS padding to a shown toolbar only on a later stylesheet change: without this
        # the bar opens short and grows on the first theme switch (measured).
        if not self.toolbar.styleSheet():
            self.toolbar.setStyleSheet(" ")
        super().showEvent(event)

    # ------------------------------------------------------------------ icons and theme
    def _iconed(self, action, name, key="ink", on="accent"):
        """Gives an action its icon now and again on every theme change."""
        self._icons.append((action, name, key, on))
        action.setIcon(icon(name, self.t[key], self.t[on]))
        return action

    def set_theme(self, mode, save=True):
        self.theme_mode = mode if mode in THEME_MODES else "system"
        if save:
            self.settings.setValue("theme", self.theme_mode)
        self.t = apply_theme(QApplication.instance(), self.theme_mode)
        for action, name, key, on in self._icons:
            action.setIcon(icon(name, self.t[key], self.t[on]))
        for holder in self.cards + [self.bar]:
            shade(holder.frame, self.t)
        self.items_empty.retheme(self.t)
        self._theme_look()
        self._show_target()

    def next_theme(self):
        self.set_theme(THEME_MODES[(THEME_MODES.index(self.theme_mode) + 1) % len(THEME_MODES)])

    def _theme_look(self):
        self.theme_action.setIcon(icon(THEME_ICONS[self.theme_mode], self.t["ink2"]))
        self.theme_action.setToolTip(THEME_TIPS[self.theme_mode])

    # ------------------------------------------------------------------ target pill
    def _show_target(self):
        ratio = self.devicePixelRatioF()
        self.pill.glyph.setPixmap(icon("target", self.t["ink2"]).pixmap(QSize(16, 16), ratio))
        self.pill.dot.setPixmap(dot_pixmap(self.t["ok"], 8, ratio=ratio))
        self.pill.text.setText(self.target)
        several = len(self.targets) > 1
        self.pill.setProperty("menu", several)
        self.pill.chevron.setPixmap(icon("chevron-down", self.t["ink2"]).pixmap(QSize(14, 14), ratio)
                                    if several else dot_pixmap("transparent", 1, ratio=ratio))
        self.pill.setCursor(Qt.CursorShape.PointingHandCursor if several else Qt.CursorShape.ArrowCursor)
        self.pill.setToolTip("Switch target" if several else "")
        self.pill.style().unpolish(self.pill)
        self.pill.style().polish(self.pill)

    def set_targets(self, targets):
        self.targets = list(targets)
        self._show_target()

    def _target_menu(self):
        menu = QMenu(self)
        for name in self.targets:
            action = menu.addAction(icon("target", self.t["ink2"]), name)
            action.triggered.connect(lambda _=False, n=name: self.switch_target(n))
        menu.exec(self.pill.mapToGlobal(self.pill.rect().bottomLeft()))

    def switch_target(self, name):
        """Moves to another target in place: same window, same lists."""
        self.target = name
        self._show_target()

    # ------------------------------------------------------------------ work
    def _mode(self, mode):
        self.hint.setText(EDIT_HINT if mode == "edit" else INSPECT_HINT)
        self.run_action.setEnabled(mode == "edit")

    def run(self):
        if not self.run_action.isEnabled():
            return
        job = self.worker.reserve()
        row = QListWidgetItem(f"Job {job}: running")
        row.setData(PENDING, True)
        row.setForeground(QColor(self.t["ink3"]))
        self.log.addItem(row)                      # shown now; the result fills it in
        self.rows[job] = row
        return self.worker.submit(self.task, job)

    def _finished(self, job, result):
        row = self.rows.pop(job, None)
        if row is not None:
            row.setText(f"Job {job}: {result}")
            row.setData(PENDING, False)
            row.setData(Qt.ItemDataRole.ForegroundRole, None)
        self.items.addItem(QListWidgetItem(f"Result of job {job}"))
        self.items_stack.setCurrentWidget(self.items)
        self.count.setText(str(self.items.count()))

    def _failed(self, job, text):
        row = self.rows.pop(job, None)
        if row is not None:
            self.log.takeItem(self.log.row(row))
        self.hint.setText(text[:160])               # a short note; full errors belong in the log file

    def clear(self):
        self.items.clear()
        self.log.clear()
        self.rows.clear()
        self.count.setText("0")
        self.items_stack.setCurrentWidget(self.items_empty)
