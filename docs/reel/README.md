# FRESH Fire Studio reel

- `fresh-fire-studio-reel.webm` — 70 s, 1280×720, VP9, no audio
- `fresh-fire-studio-reel-poster.jpg` — 1280×720 poster frame
- Script: `scripts/record_reel.py`
- Voice-over beats: `docs/reel-script.md`

## Sequence

1. Landing page and case grid.
2. `2003_526` 3D scene, fire front, near-field tree LOD.
3. Observed/model comparison.
4. Methods page: the validation ladder and limits.
5. Pilot page and closing landing view.

## Reproduce

```bash
cd fresh-fire
PORT=8800 ./run_portal.sh
python scripts/record_reel.py
```

The recorder uses Playwright’s bundled video encoder and converts the raw
capture to VP9 WebM. A system `ffmpeg` with H.264 support can be used to make an
MP4 delivery copy if required.
