# Win-Eyes

A pair of eyes for the Windows desktop that follow your mouse, in the
spirit of the classic Unix `xeyes`.

The eyes float on top of other windows with no frame, title bar or
taskbar button. Their edges are smoothly blended with whatever is behind
them, and they stay sharp at any display scaling, including when moved
between monitors with different scaling.

## Requirements

- Windows 10 or 11
- Python 3
- [Pillow](https://python-pillow.org/)

```
pip install pillow
```

## Running

```
python Win-Eyes.py
```

To start it without a console window, use `pythonw` instead:

```
pythonw Win-Eyes.py
```

## Using

- **Left-drag** the eyes to move them anywhere on the screen.
- **Right-click** them for a menu with **Exit**.

Each pupil looks towards the mouse pointer, stopping at the edge of its
eye. When the pointer is inside an eye, the pupil sits right under it.

## Settings

The look and behaviour are set by constants at the top of `Win-Eyes.py`.
All dimensions are in pixels at 100 % display scaling and grow with
Windows scaling.

| Setting         | Meaning                                            |
|-----------------|----------------------------------------------------|
| `SIZE`          | Size of one eye; the window is two eyes wide       |
| `FOLLOW_MS`     | How often the mouse position is checked (ms)       |
| `PUPIL_RADIUS`  | Radius of the pupil                                |
| `PUPIL_GAP`     | Smallest gap between the pupil and the eye outline |
| `EYE_MARGIN`    | Transparent space around each eye                  |
| `EYE_OUTLINE`   | Thickness of the eye outline                       |
| `EYE_COLOR`     | Colour of the eye whites                           |
| `OUTLINE_COLOR` | Colour of the eye outline                          |
| `PUPIL_COLOR`   | Colour of the pupils                               |

## Origin

Win-Eyes grew out of [Net-Eye](https://github.com/Niceno/Net-Eye), a
small always-on-top internet-connection indicator, and reuses its
borderless, alpha-blended window.
