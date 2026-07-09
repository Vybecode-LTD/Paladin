"""Pytest anchor: living at the backend root, this makes the `app` package
importable during test collection (pytest adds this directory to sys.path) so
`python -m pytest` works from backend/ without setting PYTHONPATH."""
