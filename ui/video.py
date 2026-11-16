"""Viewport recording (GIF via Pillow, MP4 via ffmpeg when installed) and screenshots."""
import os, shutil, subprocess, tempfile, datetime
from PIL import Image
from PyQt6.QtCore import QTimer, QBuffer, QIODevice
import io


def qimage_to_pil(img):
    buf = QBuffer(); buf.open(QIODevice.OpenModeFlag.ReadWrite); img.save(buf, "PNG"); return Image.open(io.BytesIO(bytes(buf.data()))).convert("RGB")


class ViewportRecorder:
    def __init__(self, viewport, fps=12, max_frames=600, width=960):
        self.vp, self.fps, self.max, self.width = viewport, fps, max_frames, width; self.frames = []
        self.timer = QTimer(); self.timer.timeout.connect(self._grab); self.active = False

    def start(self): self.frames = []; self.active = True; self.timer.start(int(1000 / self.fps))

    def _grab(self):
        if len(self.frames) >= self.max: self.stop_timer(); return
        im = qimage_to_pil(self.vp.grabFramebuffer()); h = int(im.height * self.width / im.width); self.frames.append(im.resize((self.width, h)))

    def stop_timer(self): self.timer.stop(); self.active = False

    def save(self, path):
        """Save as .gif or .mp4 (mp4 needs ffmpeg on PATH). Returns the written path or raises."""
        self.stop_timer()
        if not self.frames: raise RuntimeError("No frames captured")
        if path.lower().endswith(".mp4"):
            if not shutil.which("ffmpeg"): raise RuntimeError("ffmpeg not found - save as .gif or install ffmpeg")
            d = tempfile.mkdtemp()
            for i, f in enumerate(self.frames): f.save(os.path.join(d, f"f{i:05d}.png"))
            subprocess.run(["ffmpeg", "-y", "-framerate", str(self.fps), "-i", os.path.join(d, "f%05d.png"), "-pix_fmt", "yuv420p", path], check=True, capture_output=True)
            shutil.rmtree(d, ignore_errors=True)
        else:
            self.frames[0].save(path, save_all=True, append_images=self.frames[1:], duration=int(1000 / self.fps), loop=0, optimize=True)
        return path


def screenshot(viewport, path): qimage_to_pil(viewport.grabFramebuffer()).save(path)
