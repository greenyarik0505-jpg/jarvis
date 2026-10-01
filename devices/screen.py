import io
import base64
import mss
from PIL import Image
import config
from utils.logger import log_error

class ScreenCapture:
    def __init__(self):
        self.sct = mss.mss()
        # Primary monitor is usually monitor 1 in mss
        # monitor 0 is all monitors combined
        self.monitor = self.sct.monitors[1] if len(self.sct.monitors) > 1 else self.sct.monitors[0]
        self.width = self.monitor["width"]
        self.height = self.monitor["height"]

    def capture_base64(self, quality: int = config.JPEG_QUALITY, scale: float = config.SCREEN_SCALE) -> tuple[str, int, int]:
        """
        Captures the primary screen, optionally scales it, and returns:
        (base64_data_url, width, height)
        """
        try:
            sct_img = self.sct.grab(self.monitor)
            # Convert mss image to PIL Image (RGB)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

            target_w = int(img.width * scale)
            target_h = int(img.height * scale)

            if scale != 1.0:
                img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality, optimize=True)
            encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
            data_url = f"data:image/jpeg;base64,{encoded}"

            return data_url, target_w, target_h
        except Exception as e:
            log_error(f"Failed to capture screen: {e}")
            raise e

    def get_resolution(self) -> tuple[int, int]:
        return self.width, self.height

# Global singleton instance
screen = ScreenCapture()
