"""UI invariants: each test pins a defect a reviewer once saw (blurry icons, two backgrounds, lag, clipped text)."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QPoint, QSettings, Qt, Signal  # noqa: E402
from PySide6.QtGui import QIcon  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QToolTip  # noqa: E402


class FakeWorker(QObject):
    """Takes jobs without running them, so a test decides when each one ends."""

    finished = Signal(int, object)
    failed = Signal(int, str)

    def __init__(self):
        super().__init__()
        self.jobs = []

    def reserve(self):
        return len(self.jobs) + 1

    def submit(self, call, job=None):
        self.jobs.append(call)
        return job or len(self.jobs)


class UiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        folder = tempfile.mkdtemp()
        self.settings = QSettings(os.path.join(folder, "test.ini"), QSettings.Format.IniFormat)
        self.worker = FakeWorker()
        self.window = self.new_window()

    def new_window(self, **kwargs):
        from __app__.window import MainWindow
        window = MainWindow(worker=self.worker, settings=self.settings, **kwargs)
        self.addCleanup(window.close)
        return window

    @staticmethod
    def images(icon_):
        return [icon_.pixmap(32, 32, QIcon.Mode.Normal, state).toImage() for state in (QIcon.State.Off, QIcon.State.On)]

    # ---------------------------------------------------------------- icons
    def test_checked_icon_is_drawn_in_its_own_color(self):
        from __app__.icons import icon
        off, on = self.images(icon("edit", "#000000", "#ff0000"))
        self.assertNotEqual(off, on)

    def test_icon_without_on_color_looks_the_same_when_checked(self):
        from __app__.icons import icon
        off, on = self.images(icon("edit", "#000000"))
        self.assertEqual(off, on)

    def test_stroke_lands_on_whole_device_pixels(self):
        from __app__.icons import svg_bytes
        for pixels in (16, 20, 24, 32, 40):
            width = float(svg_bytes("edit", "#000", pixels=pixels).split(b'stroke-width="')[1].split(b'"')[0])
            self.assertAlmostEqual(width * pixels / 24 % 1, 0, places=2)

    def test_app_icon_is_drawn_for_every_size(self):
        from __app__.icons import app_icon
        self.assertEqual(sorted(s.width() for s in app_icon().availableSizes()), [16, 24, 32, 48, 64, 128, 256])

    # ---------------------------------------------------------------- theme
    def test_text_has_enough_contrast_in_both_themes(self):
        from __app__.theme import THEMES, contrast
        for name, t in THEMES.items():
            for fg, bg, need in (("ink", "panel", 7), ("ink2", "panel", 4.5), ("ink2", "ground", 4.5),
                                 ("accent_text", "accent_soft", 4.5), ("accent_ink", "accent", 4.5),
                                 ("ink3", "panel", 3), ("warn", "warn_soft", 4.5)):
                with self.subTest(theme=name, fg=fg, bg=bg):
                    self.assertGreaterEqual(contrast(t[fg], t[bg]), need)

    def test_both_themes_have_the_same_tokens(self):
        from __app__.theme import THEMES
        self.assertEqual(set(THEMES["light"]), set(THEMES["dark"]))

    def test_theme_button_cycles_and_persists(self):
        from __app__.theme import THEMES
        window = self.window
        self.assertEqual(window.theme_mode, "system")
        self.assertEqual(window.theme_action.toolTip(), "Theme: System (click to change)")
        window.theme_action.trigger()
        self.assertEqual((window.theme_mode, self.settings.value("theme")), ("light", "light"))
        self.assertEqual(window.t["ground"], THEMES["light"]["ground"])
        window.theme_action.trigger()
        self.assertEqual((window.theme_mode, self.settings.value("theme")), ("dark", "dark"))
        window.theme_action.trigger()
        self.assertEqual(window.theme_mode, "system")
        window.theme_action.trigger()
        self.assertEqual(self.new_window().theme_mode, "light")

    def test_invalid_stored_theme_falls_back_to_system(self):
        self.settings.setValue("theme", "neon")
        self.assertEqual(self.new_window().theme_mode, "system")

    def test_dark_cards_use_an_edge_not_a_shadow(self):
        self.window.set_theme("dark")
        self.assertFalse(self.window.cards[0].frame.graphicsEffect().isEnabled())
        self.window.set_theme("light")
        self.assertTrue(self.window.cards[0].frame.graphicsEffect().isEnabled())

    def test_toolbar_keeps_its_height_across_themes(self):
        self.window.show()
        self.app.processEvents()
        height = self.window.toolbar.height()
        for mode in ("dark", "light"):
            self.window.set_theme(mode)
            self.app.processEvents()
            self.assertEqual(self.window.toolbar.height(), height)

    # ---------------------------------------------------------------- popups and focus
    def test_menus_and_tooltips_are_see_through_and_quick(self):
        from __app__.theme import TIP_DELAY
        menu = QMenu()
        menu.ensurePolished()
        self.assertTrue(menu.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground))
        self.assertTrue(menu.windowFlags() & Qt.WindowType.FramelessWindowHint)
        QToolTip.showText(QPoint(50, 50), "tip")
        tips = [w for w in self.app.topLevelWidgets() if w.metaObject().className() == "QTipLabel"]
        self.assertTrue(tips and all(w.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) for w in tips))
        self.assertEqual(self.app.style().styleHint(QStyle.StyleHint.SH_ToolTip_WakeUpDelay), TIP_DELAY)
        self.assertFalse(self.app.isEffectEnabled(Qt.UIEffect.UI_AnimateTooltip))

    def test_buttons_take_focus_by_keyboard_only(self):
        self.assertEqual(self.window.theme_button.focusPolicy(), Qt.FocusPolicy.TabFocus)

    def test_icon_only_buttons_have_a_name_and_a_tip(self):
        self.assertEqual(self.window.theme_button.accessibleName(), "Theme")
        self.assertTrue(self.window.theme_action.toolTip())

    def test_labels_never_render_rich_text(self):
        from __app__.widgets import plain_label
        self.assertEqual(plain_label("<b>x</b>").textFormat(), Qt.TextFormat.PlainText)

    # ---------------------------------------------------------------- target pill
    def test_one_target_has_no_dropdown(self):
        self.assertFalse(self.window.pill.property("menu"))

    def test_several_targets_make_the_pill_a_dropdown(self):
        window = self.new_window(targets=("Local", "Staging"))
        self.assertTrue(window.pill.property("menu"))
        window.switch_target("Staging")
        self.assertEqual(window.pill.text.text(), "Staging")

    def test_a_target_added_later_makes_the_pill_a_dropdown(self):
        self.window.set_targets(["Local", "Staging"])
        self.assertTrue(self.window.pill.property("menu"))

    # ---------------------------------------------------------------- work
    def test_a_job_shows_at_once_as_pending_then_fills_in(self):
        from __app__.window import PENDING
        job = self.window.run()
        row = self.window.log.item(0)
        self.assertTrue(row.data(PENDING))
        self.worker.finished.emit(job, "Finished")
        self.assertFalse(row.data(PENDING))
        self.assertEqual(row.text(), f"Job {job}: Finished")
        self.assertEqual(self.window.count.text(), "1")

    def test_a_failed_job_drops_its_pending_row_and_says_why(self):
        job = self.window.run()
        self.worker.failed.emit(job, "disk full")
        self.assertEqual(self.window.log.count(), 0)
        self.assertEqual(self.window.hint.text(), "disk full")

    def test_a_job_that_ends_at_once_still_fills_its_row(self):
        from __app__.window import MainWindow, PENDING
        from __app__.worker import Worker
        window = MainWindow(worker=Worker(), settings=self.settings, task=lambda: "Done")   # no thread: direct
        self.addCleanup(window.close)
        job = window.run()
        self.assertEqual(window.log.item(0).text(), f"Job {job}: Done")
        self.assertFalse(window.log.item(0).data(PENDING))

    def test_inspect_mode_runs_nothing(self):
        self.window.inspect_mode.trigger()
        self.assertIsNone(self.window.run())
        self.assertEqual(self.worker.jobs, [])


class WorkerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_jobs_run_in_order_off_the_ui_thread(self):
        import threading
        from __app__.worker import Worker, start, stop
        worker, seen, threads = Worker(), [], []
        worker.finished.connect(lambda job, result: seen.append(result))
        thread = start(worker)
        try:
            for n in range(3):
                worker.submit(lambda n=n: (threads.append(threading.get_ident()), n)[1])
            for _ in range(100):
                if len(seen) == 3:
                    break
                QTest.qWait(20)
        finally:
            stop(thread)
        self.assertEqual(seen, [0, 1, 2])
        self.assertNotIn(threading.get_ident(), threads)

    def test_a_failing_job_reports_instead_of_raising(self):
        from __app__.worker import Worker
        worker, errors = Worker(), []
        worker.failed.connect(lambda job, text: errors.append((job, text)))
        job = worker.submit(lambda: 1 / 0)
        self.assertEqual(errors, [(job, "division by zero")])

    def test_refreshes_do_not_pile_up(self):
        from __app__.worker import Worker
        worker, queued = Worker(refresh=lambda: None), []
        worker.poll.disconnect(worker._polled)       # stand in for a worker thread that is busy
        worker.poll.connect(lambda: queued.append(1))
        for _ in range(5):
            worker.request_poll()
        self.assertEqual(queued, [1])

    def test_latest_keeps_only_the_newest_value(self):
        from __app__.worker import Latest
        box = Latest()
        self.assertEqual([box.put(n) for n in range(3)], [True, False, False])
        self.assertEqual(box.take(), 2)
        self.assertIsNone(box.take())
        self.assertTrue(box.put(3))


class SelfCheckTest(unittest.TestCase):
    def test_self_check_writes_a_sound_report(self):
        from __app__.__main__ import main
        report = os.path.join(tempfile.mkdtemp(), "report.txt")
        self.assertEqual(main(["--self-check", report]), 0)
        text = open(report, encoding="utf-8").read()
        self.assertIn("theme dark: ok", text)
        self.assertNotIn("error", text)


if __name__ == "__main__":
    unittest.main()
