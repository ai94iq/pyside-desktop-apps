# Responsiveness: nothing slow on the UI thread

Code: `src/<package>/worker.py`; its use in `window.py` (`run`, `_finished`, `_failed`).

## Contents

- [The worker](#the-worker)
- [Pending rows](#pending-rows)
- [Refreshes that do not pile up](#refreshes-that-do-not-pile-up)
- [Streams: newest value only](#streams-newest-value-only)
- [Two workers](#two-workers)
- [Measure, then write the number down](#measure-then-write-the-number-down)
- [Calling other programs](#calling-other-programs)

## The worker

`Worker` is a `QObject` moved to its own `QThread` (`start()`; `stop()` before quitting). Jobs are callables;
they run one at a time in submit order, so one slow resource (a socket, a device, a database file) is never
used from two threads. A job's exception becomes `failed(job, text)`; it never reaches Qt.

Signals cross threads as queued connections: the UI slot runs on the UI thread. Never touch a widget from a
job; return data and let the slot render it.

## Pending rows

The UI calls `reserve()` for a job id, shows a dimmed pending row for it, then `submit(call, job)`. The
result fills the row in; a failure removes the row and puts the reason in the hint line. Reserving before
submitting matters: a job that ends at once (direct connection in tests, a cache hit) otherwise answers before
its row exists (`test_a_job_that_ends_at_once_still_fills_its_row`).

## Refreshes that do not pile up

A periodic refresh (re-read state every few seconds) goes through `request_poll()`: if one is already
queued, another is not added. Without it, refreshes queued faster than they run held every user action back
by seconds. Pause the timer while a job is pending.

Watching for new targets (a server comes up, a file appears): compare a cheap signature on each poll and run
the expensive listing only when it changed.

## Streams: newest value only

A producer thread that delivers frames, log lines or progress faster than the UI paints uses `Latest`: `put()`
returns True only for the first value since the last `take()`, which is when to emit the ready signal; the UI
slot calls `take()` and gets the newest value. Old values are dropped, so the view never falls behind. Lowering
the source's resolution (for example 720 px instead of full size) was the other half of a smooth live view.

## Two workers

When fast actions (taps, keystrokes) wait behind slow reads on one worker, give the fast ones their own worker
and route each job to whichever is idle; a fast worker that needs the state refreshed asks the main worker to
do it. Edits to local data (undo, delete a row) never wait behind remote calls.

## Measure, then write the number down

Every latency claim comes from a timestamp, not a feeling. `Worker.timed(job, seconds)` reports each job's
duration; log it during development, and for a user-visible delay measure from input to the row appearing and
to the result. Record measured numbers (and the hardware) in the docs next to the feature, for example
"recorded 0.13 to 0.17 s after a click; the old path took 4 to 7 s". When asked "is it faster", measure both.

## Calling other programs

- Resolve tools with `shutil.which` once, keep the absolute path, and pass argument lists; never `shell=True`
  with text that came from outside.
- On Windows every console program opens a console window unless started with
  `creationflags=subprocess.CREATE_NO_WINDOW`; a GUI that flashes a console per call was a release blocker.
- Long-running helpers get a timeout and are stopped in `closeEvent`.
