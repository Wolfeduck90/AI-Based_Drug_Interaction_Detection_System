"""
OCR and image processing service
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import asyncio
import time
from typing import Dict, List, Optional, Tuple
import structlog
from pathlib import Path
import tempfile
import os

from app.core.config import get_settings
from app.core.exceptions import ProcessingException
from app.schemas.scans import ExtractedMedication, ScanResult

logger = structlog.get_logger(__name__)
settings = get_settings()

class OCRService:
    """OCR and image processing service"""
    
    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
        
        # Configure Tesseract
        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
        
        # OCR configurations for different scenarios
        self.tesseract_configs = [
            '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,()-/: ',
            '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,()-/: ',
            '--psm 13',
            '--psm 6',
        ]
    
    async def process_image(self, image_data: bytes, enhance: bool = True) -> ScanResult:
        """
        Process prescription image and extract medication information
        """
        start_time = time.time()
        
        try:
            # Validate image
            if not self._validate_image_data(image_data):
                raise ProcessingException("Invalid image data")
            
            # Preprocess image if requested
            if enhance:
                processed_image = await self._preprocess_image(image_data)
            else:
                processed_image = self._bytes_to_cv2(image_data)
            
            # Extract text using OCR
            ocr_result = await self._extract_text_multi_config(processed_image)
            
            # Extract structured medication data
            medications = await self._extract_medication_data(ocr_result['text'])
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return ScanResult(
                extracted_text=ocr_result['text'],
                confidence_score=ocr_result['confidence'],
                medications=medications,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error("OCR processing failed", error=str(e))
            raise ProcessingException(f"OCR processing failed: {str(e)}")
    
    def _validate_image_data(self, image_data: bytes) -> bool:
        """Validate image data"""
        try:
            # Check file size
            if len(image_data) > settings.MAX_FILE_SIZE:
                return False
            
            # Try to decode image
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            return img is not None
        except Exception:
            return False
    
    def _bytes_to_cv2(self, image_data: bytes) -> np.ndarray:
        """Convert bytes to OpenCV image"""
        nparr = np.frombuffer(image_data, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    async def _preprocess_image(self, image_data: bytes) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy
        """
        try:
            # Convert to OpenCV format
            img = self._bytes_to_cv2(image_data)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Noise reduction
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Contrast enhancement using CLAHE
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # Adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Morphological operations to clean up
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
            
            # Resize if too small
            height, width = cleaned.shape
            if height < 300 or width < 300:
                scale_factor = max(300 / height, 300 / width)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                cleaned = cv2.resize(cleaned, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            return cleaned
            
        except Exception as e:
            logger.error("Image preprocessing failed", error=str(e))
            # Return original image if preprocessing fails
            return cv2.cvtColor(self._bytes_to_cv2(image_data), cv2.COLOR_BGR2GRAY)
    
    async def _extract_text_multi_config(self, image: np.ndarray) -> Dict[str, any]:
        """
        Extract text using multiple OCR configurations and select best result
        """
        best_result = None
        best_confidence = 0
        
        for config in self.tesseract_configs:
            try:
                # Extract text with confidence data
                data = pytesseract.image_to_data(
                    image, config=config, output_type=pytesseract.Output.DICT
                )
                
                # Calculate average confidence
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                # Extract text
                text = pytesseract.image_to_string(image, config=config).strip()
                
                if avg_confidence > best_confidence and text:
                    best_confidence = avg_confidence
                    best_result = {
                        'text': text,
                        'confidence': avg_confidence / 100.0,  # Normalize to 0-1
                        'data': data
                    }
            
            except Exception as e:
                logger.warning("OCR config failed", config=config, error=str(e))
                continue
        
        if not best_result:
            raise ProcessingException("All OCR configurations failed")
        
        return best_result
    
    async def _extract_medication_data(self, text: str) -> List[ExtractedMedication]:
        """
        Extract structured medication data from OCR text
        """
        medications = []
        
        try:
            # Clean text
            cleaned_text = self._clean_text(text)
            
            # Extract medication information using patterns
            extracted_info = self._extract_with_patterns(cleaned_text)
            
            # Create medication objects
            if extracted_info.get('drug_names'):
                for drug_name in extracted_info['drug_names']:
                    medication = ExtractedMedication(
                        name=drug_name,
                        dosage=extracted_info.get('dosage'),
                        frequency=extracted_info.get('frequency'),
                        prescriber=extracted_info.get('prescriber'),
                        pharmacy=extracted_info.get('pharmacy'),
                        rx_number=extracted_info.get('rx_number'),
                        ndc_number=extracted_info.get('ndc_number'),
                        confidence=0.8  # Base confidence, could be improved with ML
                    )
                    medications.append(medication)
            
            return medications
            
        except Exception as e:
            logger.error("Medication data extraction failed", error=str(e))
            return []
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        import re
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common OCR artifacts
        text = re.sub(r'[|{}[\]~`]', '', text)
        
        # Fix common OCR mistakes in drug names
        replacements = {
            '0': 'O',  # In drug names, 0 is often O
            '1': 'I',  # In drug names, 1 is often I
        }
        
        # Apply replacements only to probable drug names
        words = text.split()
        cleaned_words = []
        
        for word in words:
            if word.isupper() or (word and word[0].isupper()):
                # This might be a drug name
                for old, new in replacements.items():
                    if old in word and not any(char.isdigit() for char in word):
                        word = word.replace(old, new)
            cleaned_words.append(word)
        
        return ' '.join(cleaned_words).strip()
    
    def _extract_with_patterns(self, text: str) -> Dict[str, any]:
        """Extract specific information using regex patterns"""
        import re
        
        patterns = {
            'rx_number': r'(?:Rx|RX|#)\s*:?\s*(\d+)',
            'ndc_number': r'NDC\s*:?\s*([\d-]+)',
            'date_filled': r'(?:Date|Filled|Date Filled)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            'quantity': r'(?:Qty|Quantity)\s*:?\s*(\d+)',
            'dosage': r'(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|units?))',
            'frequency': r'(?:take|use|apply)\s+([^\\n]*?)(?:daily|twice|once|every|as needed)',
            'prescriber': r'(?:Dr\.?|Doctor|Prescriber)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            'pharmacy': r'(?:Pharmacy|Dispensed by)\s*:?\s*([A-Z][^\\n]*)',
        }
        
        results = {}
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                results[field] = match.group(1).strip()
        
        # Extract drug names (more complex logic)
        drug_names = self._extract_drug_names(text)
        if drug_names:
            results['drug_names'] = drug_names
        
        return results
    
    def _extract_drug_names(self, text: str) -> List[str]:
        """Extract potential drug names from text"""
        import re
        
        # Patterns for drug names
        patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Capitalized words (brand names)
            r'\b[a-z]{3,}(?:\s+[a-z]+)*\b',         # Lowercase words (generic names)
        ]
        
        potential_drugs = []
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            potential_drugs.extend(matches)
        
        # Filter out common non-drug words
        common_words = {
            'tablet', 'capsule', 'take', 'with', 'food', 'water', 'daily', 'twice',
            'once', 'morning', 'evening', 'night', 'doctor', 'pharmacy', 'prescription',
            'refill', 'quantity', 'date', 'patient', 'name', 'address', 'phone'
        }
        
        filtered_drugs = []
        for drug in potential_drugs:
            if drug.lower() not in common_words and len(drug) > 2:
                filtered_drugs.append(drug.title())
        
        # Remove duplicates and return top candidates
        return list(dict.fromkeys(filtered_drugs))[:5]

# Global OCR service instance
ocr_service = OCRService()