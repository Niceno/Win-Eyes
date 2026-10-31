import math
import functools
import ctypes
from ctypes import wintypes
from PIL import Image, ImageDraw, ImageChops

# ----------------------------------------------------------------------
# Settings (all dimensions are in pixels at 100 % display scaling;
# they grow with Windows scaling, e.g. by 10 % at 110 %).
# ----------------------------------------------------------------------

SIZE          = 70   # Size of one eye; the window is two eyes wide
FOLLOW_MS     = 20   # How often the cursor position is polled
PUPIL_RADIUS  =  6   # Radius of the pupil
PUPIL_GAP     =  4   # Smallest gap between the pupil and the eye outline

EYE_MARGIN    =  5   # Transparent space around each eye
EYE_OUTLINE   =  5   # Thickness of the eye outline

EYE_COLOR     = "#ffffff"
OUTLINE_COLOR = "#202020"
PUPIL_COLOR   = "#000000"

# ----------------------------------------------------------------------
# Win32 definitions needed for a true alpha-transparent window
# ----------------------------------------------------------------------

user32   = ctypes.windll.user32
gdi32    = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

WS_EX_LAYERED    = 0x00080000
WS_EX_TOPMOST    = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_POPUP         = 0x80000000

WM_DESTROY     = 0x0002
WM_LBUTTONDOWN = 0x0201
WM_RBUTTONUP   = 0x0205
WM_TIMER       = 0x0113
WM_DPICHANGED  = 0x02E0

SWP_NOZORDER   = 0x0004
SWP_NOACTIVATE = 0x0010

DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4

WM_NCLBUTTONDOWN = 0x00A1
HTCAPTION        = 2

MF_STRING       = 0x0000
TPM_RIGHTBUTTON = 0x0002
TPM_RETURNCMD   = 0x0100

ULW_ALPHA      = 0x00000002
AC_SRC_OVER    = 0x00
AC_SRC_ALPHA   = 0x01
BI_RGB         = 0
DIB_RGB_COLORS = 0

ID_EXIT         = 1
FOLLOW_TIMER_ID = 1

IDC_ARROW = 32512

LRESULT = ctypes.c_ssize_t

user32.DefWindowProcW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM
]
user32.DefWindowProcW.restype = LRESULT


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ("BlendOp", ctypes.c_ubyte),
        ("BlendFlags", ctypes.c_ubyte),
        ("SourceConstantAlpha", ctypes.c_ubyte),
        ("AlphaFormat", ctypes.c_ubyte),
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class RGBQUAD(ctypes.Structure):
    _fields_ = [
        ("rgbBlue", ctypes.c_ubyte),
        ("rgbGreen", ctypes.c_ubyte),
        ("rgbRed", ctypes.c_ubyte),
        ("rgbReserved", ctypes.c_ubyte),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", RGBQUAD * 1),
    ]


WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


# Full 64-bit prototypes for every Win32 call used below. Without these,
# ctypes assumes 32-bit int arguments and results, truncating handles.
UINT_PTR = ctypes.c_size_t

kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype  = wintypes.HMODULE

user32.GetDC.argtypes = [wintypes.HWND]
user32.GetDC.restype  = wintypes.HDC
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.ReleaseDC.restype  = ctypes.c_int
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetWindowRect.restype  = wintypes.BOOL
user32.UpdateLayeredWindow.argtypes = [
    wintypes.HWND,
    wintypes.HDC,
    ctypes.POINTER(wintypes.POINT),
    ctypes.POINTER(wintypes.SIZE),
    wintypes.HDC,
    ctypes.POINTER(wintypes.POINT),
    wintypes.COLORREF,
    ctypes.POINTER(BLENDFUNCTION),
    wintypes.DWORD,
]
user32.UpdateLayeredWindow.restype = wintypes.BOOL

user32.SendMessageW.argtypes = [
    wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
]
user32.SendMessageW.restype = LRESULT

user32.CreatePopupMenu.argtypes = []
user32.CreatePopupMenu.restype  = wintypes.HMENU
user32.AppendMenuW.argtypes = [
    wintypes.HMENU, wintypes.UINT, UINT_PTR, wintypes.LPCWSTR
]
user32.AppendMenuW.restype = wintypes.BOOL
user32.TrackPopupMenu.argtypes = [
    wintypes.HMENU,
    wintypes.UINT,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.HWND,
    ctypes.c_void_p,
]
user32.TrackPopupMenu.restype = wintypes.BOOL
user32.DestroyMenu.argtypes = [wintypes.HMENU]
user32.DestroyMenu.restype  = wintypes.BOOL
user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
user32.GetCursorPos.restype  = wintypes.BOOL
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.restype  = wintypes.BOOL
user32.ReleaseCapture.argtypes = []
user32.ReleaseCapture.restype  = wintypes.BOOL

user32.LoadCursorW.argtypes = [wintypes.HINSTANCE, ctypes.c_void_p]
user32.LoadCursorW.restype  = wintypes.HANDLE
user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
user32.RegisterClassW.restype  = wintypes.ATOM
user32.CreateWindowExW.argtypes = [
    wintypes.DWORD,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.DWORD,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.HWND,
    wintypes.HMENU,
    wintypes.HINSTANCE,
    wintypes.LPVOID,
]
user32.CreateWindowExW.restype = wintypes.HWND
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype  = wintypes.BOOL
user32.DestroyWindow.argtypes = [wintypes.HWND]
user32.DestroyWindow.restype  = wintypes.BOOL
user32.SetWindowPos.argtypes = [
    wintypes.HWND,
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
]
user32.SetWindowPos.restype = wintypes.BOOL

user32.SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
user32.SetProcessDpiAwarenessContext.restype  = wintypes.BOOL
user32.GetDpiForWindow.argtypes = [wintypes.HWND]
user32.GetDpiForWindow.restype  = wintypes.UINT

user32.SetTimer.argtypes = [
    wintypes.HWND, UINT_PTR, wintypes.UINT, ctypes.c_void_p
]
user32.SetTimer.restype = UINT_PTR
user32.KillTimer.argtypes = [wintypes.HWND, UINT_PTR]
user32.KillTimer.restype  = wintypes.BOOL

user32.GetMessageW.argtypes = [
    ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT
]
user32.GetMessageW.restype = wintypes.BOOL
user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.TranslateMessage.restype  = wintypes.BOOL
user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.DispatchMessageW.restype  = LRESULT
user32.PostQuitMessage.argtypes = [ctypes.c_int]
user32.PostQuitMessage.restype  = None

gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleDC.restype  = wintypes.HDC
gdi32.CreateDIBSection.argtypes = [
    wintypes.HDC,
    ctypes.POINTER(BITMAPINFO),
    wintypes.UINT,
    ctypes.POINTER(ctypes.c_void_p),
    wintypes.HANDLE,
    wintypes.DWORD,
]
gdi32.CreateDIBSection.restype = wintypes.HBITMAP
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi32.SelectObject.restype  = wintypes.HGDIOBJ
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteObject.restype  = wintypes.BOOL
gdi32.DeleteDC.argtypes = [wintypes.HDC]
gdi32.DeleteDC.restype  = wintypes.BOOL


# ----------------------------------------------------------------------
# Drawing: Pillow draws the eyes 4x larger and downsamples them smoothly,
# so every edge blends with whatever is behind the window.
# ----------------------------------------------------------------------

SCALE = 4

# Display scaling of the monitor the window is on (1.0 = 100 %, 96 DPI).
# All sizes above are given at 100 % and multiplied by this when drawing.
dpi_scale = 1.0

# Pupil offsets from the eye centres (at 100 % scaling) drawn last,
# so nothing is redrawn while neither the cursor nor the window moves.
current_pupils = ((0.0, 0.0), (0.0, 0.0))


def eye_size():
    return round(SIZE * dpi_scale)


def window_width():
    return 2 * eye_size()


def max_pupil_offset():
    """How far a pupil centre may move from the eye centre (at 100 %)."""
    return SIZE / 2 - EYE_MARGIN - EYE_OUTLINE - PUPIL_GAP - PUPIL_RADIUS


# The eye whites never change, so they are rendered once per DPI. The
# dpi argument is not used directly, it only keeps the cache per DPI.
@functools.lru_cache(maxsize=None)
def make_eyes(dpi):
    big_eye = eye_size() * SCALE
    image = Image.new("RGBA", (2 * big_eye, big_eye), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    s = dpi_scale * SCALE
    margin = round(EYE_MARGIN * s)

    for left in (0, big_eye):
        draw.ellipse(
            (left + margin, margin,
             left + big_eye - margin, big_eye - margin),
            fill=EYE_COLOR,
            outline=OUTLINE_COLOR,
            width=round(EYE_OUTLINE * s),
        )

    return image


def make_frame(pupils):
    image = make_eyes(dpi_scale).copy()
    draw = ImageDraw.Draw(image)

    s = dpi_scale * SCALE
    big_eye = eye_size() * SCALE
    r = PUPIL_RADIUS * s

    for index, (dx, dy) in enumerate(pupils):
        cx = big_eye * index + big_eye / 2 + dx * s
        cy = big_eye / 2 + dy * s
        draw.ellipse((round(cx-r), round(cy-r), round(cx+r), round(cy+r)),
                     fill=PUPIL_COLOR)

    image = image.resize((window_width(), eye_size()),
                         Image.Resampling.LANCZOS)

    # UpdateLayeredWindow expects premultiplied BGRA pixels.
    red, green, blue, alpha = image.split()
    image = Image.merge("RGBA", (
        ImageChops.multiply(blue, alpha),
        ImageChops.multiply(green, alpha),
        ImageChops.multiply(red, alpha),
        alpha,
    ))
    return image.tobytes()


def draw_eyes(hwnd, pupils):
    global current_pupils
    current_pupils = pupils

    pixels = make_frame(pupils)
    width = window_width()
    height = eye_size()

    screen_dc = user32.GetDC(None)
    memory_dc = gdi32.CreateCompatibleDC(screen_dc)

    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = width
    bmi.bmiHeader.biHeight = -height     # top-down bitmap
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = BI_RGB

    bits = ctypes.c_void_p()

    bitmap = gdi32.CreateDIBSection(
        memory_dc,
        ctypes.byref(bmi),
        DIB_RGB_COLORS,
        ctypes.byref(bits),
        None,
        0,
    )

    ctypes.memmove(bits, pixels, len(pixels))

    old_bitmap = gdi32.SelectObject(memory_dc, bitmap)

    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))

    destination = wintypes.POINT(rect.left, rect.top)
    source = wintypes.POINT(0, 0)
    size = wintypes.SIZE(width, height)

    blend = BLENDFUNCTION(
        AC_SRC_OVER,
        0,
        255,
        AC_SRC_ALPHA,
    )

    user32.UpdateLayeredWindow(
        hwnd,
        screen_dc,
        ctypes.byref(destination),
        ctypes.byref(size),
        memory_dc,
        ctypes.byref(source),
        0,
        ctypes.byref(blend),
        ULW_ALPHA,
    )

    gdi32.SelectObject(memory_dc, old_bitmap)
    gdi32.DeleteObject(bitmap)
    gdi32.DeleteDC(memory_dc)
    user32.ReleaseDC(None, screen_dc)


# ----------------------------------------------------------------------
# Following the mouse: each pupil moves towards the cursor, but no
# further than the edge of its eye. A cursor inside an eye gets the
# pupil right underneath it.
# ----------------------------------------------------------------------

def pupils_for_cursor(hwnd):
    cursor = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(cursor))

    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))

    limit = max_pupil_offset()
    half = eye_size() / 2
    pupils = []

    for index in range(2):
        # Screen pixels are scaled pixels; convert them to 100 % sizes.
        centre_x = rect.left + eye_size() * index + half
        centre_y = rect.top + half
        dx = (cursor.x - centre_x) / dpi_scale
        dy = (cursor.y - centre_y) / dpi_scale

        distance = math.hypot(dx, dy)
        if distance > limit:
            dx *= limit / distance
            dy *= limit / distance

        # Finer steps than this are invisible after downsampling.
        step = 1 / (dpi_scale * SCALE)
        pupils.append((round(dx / step) * step, round(dy / step) * step))

    return tuple(pupils)


def follow_cursor(hwnd):
    pupils = pupils_for_cursor(hwnd)
    if pupils != current_pupils:
        draw_eyes(hwnd, pupils)


# ----------------------------------------------------------------------
# Native Windows mouse/menu handling
# ----------------------------------------------------------------------

def show_menu(hwnd):
    menu = user32.CreatePopupMenu()

    user32.AppendMenuW(menu, MF_STRING, ID_EXIT, "Exit")

    point = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(point))

    user32.SetForegroundWindow(hwnd)

    command = user32.TrackPopupMenu(
        menu,
        TPM_RIGHTBUTTON | TPM_RETURNCMD,
        point.x,
        point.y,
        0,
        hwnd,
        None,
    )

    user32.DestroyMenu(menu)

    if command == ID_EXIT:
        user32.DestroyWindow(hwnd)


@WNDPROC
def window_proc(window, message, wparam, lparam):
    global dpi_scale

    if message == WM_LBUTTONDOWN:
        # Drag the eyes around by any visible part.
        user32.ReleaseCapture()
        user32.SendMessageW(window, WM_NCLBUTTONDOWN, HTCAPTION, 0)
        return 0

    if message == WM_RBUTTONUP:
        show_menu(window)
        return 0

    if message == WM_TIMER:
        if wparam == FOLLOW_TIMER_ID:
            follow_cursor(window)
        return 0

    if message == WM_DPICHANGED:
        # Moved to a monitor with different scaling: resize and redraw.
        dpi_scale = (wparam & 0xFFFF) / 96
        suggested = wintypes.RECT.from_address(lparam)
        user32.SetWindowPos(
            window,
            None,
            suggested.left,
            suggested.top,
            window_width(),
            eye_size(),
            SWP_NOZORDER | SWP_NOACTIVATE,
        )
        draw_eyes(window, current_pupils)
        return 0

    if message == WM_DESTROY:
        user32.KillTimer(window, FOLLOW_TIMER_ID)
        user32.PostQuitMessage(0)
        return 0

    return user32.DefWindowProcW(window, message, wparam, lparam)


# ----------------------------------------------------------------------
# Create the small layered window
# ----------------------------------------------------------------------

hinstance = kernel32.GetModuleHandleW(None)
class_name = "WinEyesWindow"

window_class = WNDCLASSW()
window_class.lpfnWndProc = window_proc
window_class.hInstance = hinstance
window_class.hCursor = user32.LoadCursorW(
    None,
    ctypes.c_void_p(IDC_ARROW)
)
window_class.lpszClassName = class_name

user32.RegisterClassW(ctypes.byref(window_class))

# Handle display scaling ourselves, so Windows does not blur the window
# by stretching it. Must happen before the window is created.
user32.SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)

hwnd = user32.CreateWindowExW(
    WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW,
    class_name,
    "WinEyes",
    WS_POPUP,
    100,
    100,
    2 * SIZE,
    SIZE,
    None,
    None,
    hinstance,
    None,
)

dpi_scale = user32.GetDpiForWindow(hwnd) / 96

draw_eyes(hwnd, pupils_for_cursor(hwnd))

user32.ShowWindow(hwnd, 5)
user32.SetTimer(hwnd, FOLLOW_TIMER_ID, FOLLOW_MS, None)

# Windows message loop.
message = wintypes.MSG()

while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
    user32.TranslateMessage(ctypes.byref(message))
    user32.DispatchMessageW(ctypes.byref(message))
