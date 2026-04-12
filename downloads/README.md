# Downloads

This directory contains files downloaded during test execution.

Configure download directory in browser context:
```python
context = browser.new_context(
    accept_downloads=True,
    downloads_path="downloads/"
)
```
