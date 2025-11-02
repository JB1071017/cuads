import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

class ASCIIConverter:
    def __init__(self, width=80, height=None, colored=False):
        self.width = width
        self.colored = colored
        
        # ASCII character set from dark to light
        self.ascii_chars = "@%#*+=-:. "
        
    def resize_image(self, image):
        """Resize image while maintaining aspect ratio"""
        h, w = image.shape[:2]
        aspect_ratio = h / w
        height = int(self.width * aspect_ratio * 0.55)  # Adjust for character aspect ratio
        
        if height <= 0:
            height = 1
            
        resized = cv2.resize(image, (self.width, height))
        return resized
    
    def pixel_to_ascii(self, pixel):
        """Convert pixel value to ASCII character"""
        if len(pixel) == 3:  # Color image
            r, g, b = pixel
            brightness = 0.299 * r + 0.587 * g + 0.114 * b
        else:  # Grayscale
            brightness = pixel
            
        ascii_index = int(brightness / 255 * (len(self.ascii_chars) - 1))
        return self.ascii_chars[ascii_index]
    
    def convert_frame(self, frame):
        """Convert a single frame to ASCII art"""
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Resize frame
        resized = self.resize_image(frame_rgb)
        
        # Convert to ASCII
        ascii_art = []
        for row in resized:
            ascii_row = []
            for pixel in row:
                ascii_char = self.pixel_to_ascii(pixel)
                if self.colored:
                    r, g, b = pixel
                    # Create ANSI color code
                    colored_char = f"\033[38;2;{r};{g};{b}m{ascii_char}\033[0m"
                    ascii_row.append(colored_char)
                else:
                    ascii_row.append(ascii_char)
            ascii_art.append("".join(ascii_row))
        
        return "\n".join(ascii_art)