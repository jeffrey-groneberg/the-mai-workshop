Capture command (from repository root; FFmpeg and cwebp required):
WORKSHOP_MEDIA_DIR=test-results/workshop-media python -m pytest -q tests/test_lessons.py

Screenshots show the actual app produced by the published lesson edits.
The silent GIF records that completed learner app, including optional mnemonics.
Model responses and microphone input are offline fixtures, not live model calls.
The image fixture is an apple crop (320:320:30:220) of the existing MAI-generated
docs/assets/images/vocabulary-journey.webp. No endpoint or key is captured.
