"""
Image Processing Utilities
Advanced image preprocessing for better OCR accuracy
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import io
import logging
from typing import Tuple, Optional
import math

logger = logging.getLogger(__name__)

class ImageProcessor:
    """
    Advanced image processing for prescription label enhancement
    """
    
    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
        self.max_dimension = 2048  # Maximum width or height
        self.min_dimension = 300   # Minimum width or height
    
    def validate_image(self, image_data: bytes) -> bool:
        """
        Validate image data and format
        """
        try:
            # Try to decode image
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return False
            
            height, width = img.shape[:2]
            
            # Check minimum dimensions
            if height < 50 or width < 50:
                return False
            
            # Check maximum file size (10MB)
            if len(image_data) > 10 * 1024 * 1024:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            return False
    
    def preprocess_image(self, image_data: bytes) -> np.ndarray:
        """
        Comprehensive image preprocessing pipeline
        """
        try:
            # Convert bytes to OpenCV image
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("Could not decode image")
            
            # Step 1: Resize if necessary
            img = self._resize_image(img)
            
            # Step 2: Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Step 3: Noise reduction
            denoised = self._denoise_image(gray)
            
            # Step 4: Contrast enhancement
            enhanced = self._enhance_contrast(denoised)
            
            # Step 5: Deskew if needed
            deskewed = self._deskew_image(enhanced)
            
            # Step 6: Adaptive thresholding
            thresholded = self._adaptive_threshold(deskewed)
            
            # Step 7: Morphological operations
            cleaned = self._morphological_cleanup(thresholded)
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            # Return original grayscale as fallback
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
            return img if img is not None else np.zeros((100, 100), dtype=np.uint8)
    
    def _resize_image(self, img: np.ndarray) -> np.ndarray:
        """
        Resize image to optimal dimensions for OCR
        """
        height, width = img.shape[:2]
        
        # Calculate scaling factor
        scale_factor = 1.0
        
        if max(height, width) > self.max_dimension:
            scale_factor = self.max_dimension / max(height, width)
        elif min(height, width) < self.min_dimension:
            scale_factor = self.min_dimension / min(height, width)
        
        if scale_factor != 1.0:
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        return img
    
    def _denoise_image(self, img: np.ndarray) -> np.ndarray:
        """
        Remove noise from the image
        """
        # Use Non-local Means Denoising
        denoised = cv2.fastNlMeansDenoising(img, None, 10, 7, 21)
        return denoised
    
    def _enhance_contrast(self, img: np.ndarray) -> np.ndarray:
        """
        Enhance image contrast using CLAHE
        """
        # Create CLAHE object
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(img)
        return enhanced
    
    def _deskew_image(self, img: np.ndarray) -> np.ndarray:
        """
        Correct image skew/rotation
        """
        try:
            # Find edges
            edges = cv2.Canny(img, 50, 150, apertureSize=3)
            
            # Find lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is not None:
                # Calculate average angle
                angles = []
                for rho, theta in lines[:10]:  # Use first 10 lines
                    angle = theta * 180 / np.pi
                    if angle > 90:
                        angle = angle - 180
                    angles.append(angle)
                
                if angles:
                    avg_angle = np.median(angles)
                    
                    # Only correct if angle is significant
                    if abs(avg_angle) > 0.5:
                        # Rotate image
                        height, width = img.shape
                        center = (width // 2, height // 2)
                        rotation_matrix = cv2.getRotationMatrix2D(center, avg_angle, 1.0)
                        img = cv2.warpAffine(img, rotation_matrix, (width, height), 
                                           flags=cv2.INTER_CUBIC, 
                                           borderMode=cv2.BORDER_REPLICATE)
        
        except Exception as e:
            logger.warning(f"Deskewing failed: {e}")
        
        return img
    
    def _adaptive_threshold(self, img: np.ndarray) -> np.ndarray:
        """
        Apply adaptive thresholding for better text separation
        """
        # Try multiple thresholding methods
        methods = [
            cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                cv2.THRESH_BINARY, 11, 2),
            cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                cv2.THRESH_BINARY, 11, 2),
            cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        ]
        
        # Select the best threshold based on text area
        best_thresh = self._select_best_threshold(methods)
        return best_thresh
    
    def _select_best_threshold(self, thresh_images: list) -> np.ndarray:
        """
        Select the threshold image with the most text-like regions
        """
        best_score = -1
        best_image = thresh_images[0]
        
        for thresh_img in thresh_images:
            try:
                # Count connected components (potential text regions)
                num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh_img)
                
                # Score based on number of reasonable-sized components
                score = 0
                for i in range(1, num_labels):  # Skip background (label 0)
                    area = stats[i, cv2.CC_STAT_AREA]
                    width = stats[i, cv2.CC_STAT_WIDTH]
                    height = stats[i, cv2.CC_STAT_HEIGHT]
                    
                    # Text regions typically have certain aspect ratios and sizes
                    if 10 < area < 5000 and 0.1 < height/width < 10:
                        score += 1
                
                if score > best_score:
                    best_score = score
                    best_image = thresh_img
            
            except Exception:
                continue
        
        return best_image
    
    def _morphological_cleanup(self, img: np.ndarray) -> np.ndarray:
        """
        Clean up the image using morphological operations
        """
        # Define kernels
        kernel_close = np.ones((2, 2), np.uint8)
        kernel_open = np.ones((1, 1), np.uint8)
        
        # Close small gaps
        closed = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel_close)
        
        # Remove small noise
        opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel_open)
        
        return opened
    
    def get_image_quality_score(self, img: np.ndarray) -> float:
        """
        Calculate image quality score for OCR suitability
        """
        try:
            # Convert to grayscale if needed
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img
            
            # Calculate various quality metrics
            
            # 1. Sharpness (Laplacian variance)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness_score = min(1.0, laplacian_var / 1000)
            
            # 2. Contrast (standard deviation)
            contrast_score = min(1.0, gray.std() / 128)
            
            # 3. Brightness (mean intensity)
            brightness = gray.mean()
            brightness_score = 1.0 - abs(brightness - 128) / 128
            
            # 4. Text-like regions
            edges = cv2.Canny(gray, 50, 150)
            text_score = min(1.0, np.sum(edges > 0) / (gray.shape[0] * gray.shape[1]))
            
            # Combine scores
            quality_score = (sharpness_score * 0.3 + 
                           contrast_score * 0.3 + 
                           brightness_score * 0.2 + 
                           text_score * 0.2)
            
            return quality_score
            
        except Exception as e:
            logger.error(f"Quality score calculation failed: {e}")
            return 0.5  # Default medium quality
    
    def extract_text_regions(self, img: np.ndarray) -> list:
        """
        Extract potential text regions from the image
        """
        try:
            # Find contours
            contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            text_regions = []
            
            for contour in contours:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter based on size and aspect ratio
                area = w * h
                aspect_ratio = w / h if h > 0 else 0
                
                if (20 < area < 10000 and 
                    0.1 < aspect_ratio < 20 and 
                    w > 10 and h > 5):
                    
                    text_regions.append({
                        'x': x, 'y': y, 'width': w, 'height': h,
                        'area': area, 'aspect_ratio': aspect_ratio
                    })
            
            # Sort by area (largest first)
            text_regions.sort(key=lambda r: r['area'], reverse=True)
            
            return text_regions
            
        except Exception as e:
            logger.error(f"Text region extraction failed: {e}")
            return []

# Global image processor instance
image_processor = ImageProcessor()