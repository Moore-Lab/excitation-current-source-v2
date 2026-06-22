"""Staged bench bring-up procedures (TESTING_PLAN Part 2, Stages 0–8).

Each module is a go/no-go gate that imports the host/ acquisition library and the
bench/ harness. Runnable hardware-free against the mock (``--mock``, default) or
against a real T7 (``--real``). ``run_all`` drives the whole sequence.
"""