# Videos

This directory contains video recordings of test executions.

To enable video recording, configure in conftest.py:
```python
context = browser.new_context(
    record_video_dir="videos/",
    record_video_size={"width": 1920, "height": 1080}
)
```

Videos are saved as WebM format.
