"""
OCR and Image Processing Module for Drug Interaction Detection System
Handles medication label image processing and text extraction using Tesseract OCR
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import logging
from fastai.vision.all import *
import torch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OCRResult:
    """Data class to store OCR processing results"""
    raw_text: str
    confidence: float
    processed_text: str
    detected_elements: Dict[str, str]
    bounding_boxes: List[Dict]
    processing_errors: List[str]

class ImagePreprocessor:
    """
    Handles image preprocessing to improve OCR accuracy
    Implements various image enhancement techniques
    """
    
    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    
    def validate_image(self, image_path: str) -> bool:
        """Validate if the image file is supported and readable"""
        try:
            path = Path(image_path)
            if not path.exists():
                logger.error(f"Image file not found: {image_path}")
                return False
            
            if path.suffix.lower() not in self.supported_formats:
                logger.error(f"Unsupported image format: {path.suffix}")
                return False
            
            # Try to open the image
            img = cv2.imread(str(path))
            if img is None:
                logger.error(f"Cannot read image file: {image_path}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Image validation error: {e}")
            return False
    
    def enhance_image_for_ocr(self, image_path: str) -> np.ndarray:
        """
        Apply comprehensive image preprocessing for better OCR results
        Returns the enhanced image as numpy array
        """
        try:
            # Read the image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Cannot read image: {image_path}")
            
            # Step 1: Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Step 2: Noise reduction using Gaussian blur
            denoised = cv2.GaussianBlur(gray, (1, 1), 0)
            
            # Step 3: Contrast enhancement using CLAHE
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # Step 4: Adaptive thresholding for better text separation
            # Try multiple thresholding methods and choose the best
            thresh_methods = [
                cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                    cv2.THRESH_BINARY, 11, 2),
                cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                    cv2.THRESH_BINARY, 11, 2),
                cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            ]
            
            # Select the best threshold based on text area
            best_thresh = self._select_best_threshold(thresh_methods)
            
            # Step 5: Morphological operations to clean up the image
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(best_thresh, cv2.MORPH_CLOSE, kernel)
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
            
            # Step 6: Resize if image is too small (OCR works better on larger images)
            height, width = cleaned.shape
            if height < 300 or width < 300:
                scale_factor = max(300 / height, 300 / width)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                cleaned = cv2.resize(cleaned, (new_width, new_height), 
                                   interpolation=cv2.INTER_CUBIC)
            
            logger.info(f"Image preprocessing completed successfully for {image_path}")
            return cleaned
            
        except Exception as e:
            logger.error(f"Image preprocessing error: {e}")
            raise
    
    def _select_best_threshold(self, thresh_images: List[np.ndarray]) -> np.ndarray:
        """Select the threshold image with the most text-like regions"""
        best_score = -1
        best_image = thresh_images[0]
        
        for thresh_img in thresh_images:
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
        
        return best_image

class MedicationLabelOCR:
    """
    Specialized OCR processor for medication labels
    Handles text extraction and medication-specific information parsing
    """
    
    def __init__(self):
        self.preprocessor = ImagePreprocessor()
        
        # Tesseract configuration for medication labels
        # PSM 6: Assume uniform block of text
        # PSM 8: Treat image as single word
        # PSM 13: Raw line. Treat image as single text line
        self.tesseract_configs = [
            '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,()-/: ',
            '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,()-/: ',
            '--psm 13 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,()-/: ',
            '--psm 6',  # Default with all characters
        ]
        
        # Regex patterns for medication information extraction
        self.patterns = {
            'drug_name': [
                r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Capitalized words (brand names)
                r'\b[a-z]+(?:\s+[a-z]+)*\b',            # Lowercase words (generic names)
            ],
            'strength': [
                r'\b\d+(?:\.\d+)?\s*(?:mg|g|mcg|µg|mL|L|units?|IU)\b',
                r'\b\d+(?:\.\d+)?/\d+(?:\.\d+)?\s*(?:mg|g|mcg|µg|mL|L)\b',  # Combination strengths
            ],
            'ndc': [
                r'\bNDC\s*:?\s*(\d{5}-\d{3}-\d{2}|\d{5}-\d{4}-\d{1}|\d{4}-\d{4}-\d{2})\b',
                r'\b\d{5}-\d{3}-\d{2}\b',
                r'\b\d{5}-\d{4}-\d{1}\b',
                r'\b\d{4}-\d{4}-\d{2}\b',
            ],
            'lot_number': [
                r'\b(?:LOT|Lot|Batch)\s*:?\s*([A-Z0-9]+)\b',
                r'\bLOT\s*[:#]?\s*([A-Z0-9]+)\b',
            ],
            'expiry_date': [
                r'\b(?:EXP|Exp|Expires?)\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})\b',
                r'\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b',
            ],
            'dosage_form': [
                r'\b(?:tablet|capsule|liquid|solution|injection|cream|ointment|gel|patch|inhaler)s?\b',
            ]
        }
    
    def extract_text_from_image(self, image_path: str) -> OCRResult:
        """
        Main method to extract and process text from medication label image
        Returns comprehensive OCR results
        """
        processing_errors = []
        
        try:
            # Validate image
            if not self.preprocessor.validate_image(image_path):
                raise ValueError(f"Invalid image file: {image_path}")
            
            # Preprocess image
            try:
                enhanced_img = self.preprocessor.enhance_image_for_ocr(image_path)
            except Exception as e:
                processing_errors.append(f"Image preprocessing failed: {e}")
                # Fall back to original image
                enhanced_img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            
            # Try multiple OCR configurations and select best result
            best_result = None
            best_confidence = 0
            
            for config in self.tesseract_configs:
                try:
                    # Extract text with confidence scores
                    data = pytesseract.image_to_data(enhanced_img, config=config, 
                                                   output_type=pytesseract.Output.DICT)
                    
                    # Calculate average confidence
                    confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                    
                    # Extract text
                    text = pytesseract.image_to_string(enhanced_img, config=config).strip()
                    
                    if avg_confidence > best_confidence and text:
                        best_confidence = avg_confidence
                        best_result = {
                            'text': text,
                            'confidence': avg_confidence,
                            'data': data
                        }
                
                except Exception as e:
                    processing_errors.append(f"OCR config '{config}' failed: {e}")
                    continue
            
            if not best_result:
                raise ValueError("All OCR configurations failed")
            
            raw_text = best_result['text']
            confidence = best_result['confidence']
            
            # Process and clean the extracted text
            processed_text = self._clean_extracted_text(raw_text)
            
            # Extract specific medication information
            detected_elements = self._extract_medication_info(processed_text)
            
            # Extract bounding boxes for detected text
            bounding_boxes = self._extract_bounding_boxes(best_result['data'])
            
            logger.info(f"OCR completed successfully. Confidence: {confidence:.2f}%")
            
            return OCRResult(
                raw_text=raw_text,
                confidence=confidence,
                processed_text=processed_text,
                detected_elements=detected_elements,
                bounding_boxes=bounding_boxes,
                processing_errors=processing_errors
            )
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            processing_errors.append(f"OCR processing failed: {e}")
            
            return OCRResult(
                raw_text="",
                confidence=0.0,
                processed_text="",
                detected_elements={},
                bounding_boxes=[],
                processing_errors=processing_errors
            )
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common OCR artifacts
        text = re.sub(r'[|{}[\]~`]', '', text)
        
        # Fix common OCR mistakes
        replacements = {
            '0': 'O',  # In drug names, 0 is often O
            '1': 'I',  # In drug names, 1 is often I
            '5': 'S',  # Sometimes 5 is misread as S
        }
        
        # Apply replacements only to probable drug names (capitalized words)
        words = text.split()
        cleaned_words = []
        
        for word in words:
            if word.isupper() or (word and word[0].isupper()):
                # This might be a drug name, apply character corrections
                for old, new in replacements.items():
                    if old in word and not any(char.isdigit() for char in word):
                        word = word.replace(old, new)
            cleaned_words.append(word)
        
        return ' '.join(cleaned_words).strip()
    
    def _extract_medication_info(self, text: str) -> Dict[str, str]:
        """Extract specific medication information using regex patterns"""
        detected_info = {}
        
        for info_type, patterns in self.patterns.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, text, re.IGNORECASE)
                matches.extend(found)
            
            if matches:
                if info_type == 'drug_name':
                    # For drug names, prefer longer matches and capitalize properly
                    matches = sorted(set(matches), key=len, reverse=True)
                    detected_info[info_type] = [match.title() for match in matches[:3]]
                else:
                    detected_info[info_type] = list(set(matches))
        
        return detected_info
    
    def _extract_bounding_boxes(self, ocr_data: Dict) -> List[Dict]:
        """Extract bounding box information for detected text"""
        boxes = []
        
        for i in range(len(ocr_data['text'])):
            if int(ocr_data['conf'][i]) > 30:  # Only include confident detections
                box = {
                    'text': ocr_data['text'][i],
                    'confidence': int(ocr_data['conf'][i]),
                    'left': int(ocr_data['left'][i]),
                    'top': int(ocr_data['top'][i]),
                    'width': int(ocr_data['width'][i]),
                    'height': int(ocr_data['height'][i])
                }
                boxes.append(box)
        
        return boxes

class FastAIImageClassifier:
    """
    FastAI-based image classifier for medication label recognition
    Can classify different types of medication labels and improve OCR targeting
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.model = None
        self.is_trained = False
        
    def load_model(self, model_path: str):
        """Load pre-trained FastAI model"""
        try:
            self.model = load_learner(model_path)
            self.is_trained = True
            logger.info(f"FastAI model loaded from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load FastAI model: {e}")
            raise
    
    def train_model(self, data_path: str, epochs: int = 10):
        """
        Train FastAI model for medication label classification
        This would be used to classify different types of labels
        """
        try:
            # Create data loaders
            dls = ImageDataLoaders.from_folder(
                data_path,
                train='train',
                valid='valid',
                item_tfms=Resize(224),
                batch_tfms=aug_transforms(size=224, min_scale=0.75)
            )
            
            # Create learner with ResNet34 architecture
            learn = vision_learner(dls, resnet34, metrics=accuracy)
            
            # Find optimal learning rate
            learn.lr_find()
            
            # Train the model
            learn.fine_tune(epochs)
            
            # Save the model
            model_save_path = f"models/medication_classifier_{epochs}epochs.pkl"
            learn.export(model_save_path)
            
            self.model = learn
            self.is_trained = True
            self.model_path = model_save_path
            
            logger.info(f"Model trained and saved to {model_save_path}")
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            raise
    
    def classify_image(self, image_path: str) -> Dict[str, any]:
        """
        Classify medication label image
        Returns classification results and confidence scores
        """
        if not self.is_trained or not self.model:
            logger.warning("Model not loaded. Returning default classification.")
            return {
                'predicted_class': 'generic_label',
                'confidence': 0.5,
                'all_predictions': {}
            }
        
        try:
            # Load and predict
            img = PILImage.create(image_path)
            pred_class, pred_idx, probs = self.model.predict(img)
            
            # Get all class probabilities
            class_names = self.model.dls.vocab
            all_predictions = {
                class_names[i]: float(probs[i]) 
                for i in range(len(class_names))
            }
            
            return {
                'predicted_class': str(pred_class),
                'confidence': float(probs[pred_idx]),
                'all_predictions': all_predictions
            }
            
        except Exception as e:
            logger.error(f"Image classification failed: {e}")
            return {
                'predicted_class': 'unknown',
                'confidence': 0.0,
                'all_predictions': {},
                'error': str(e)
            }

def process_medication_image(image_path: str, classifier_model_path: str = None) -> Dict:
    """
    Main function to process a medication label image
    Combines OCR, classification, and information extraction
    """
    try:
        # Initialize processors
        ocr_processor = MedicationLabelOCR()
        classifier = FastAIImageClassifier(classifier_model_path)
        
        # Load classifier if model path provided
        if classifier_model_path and Path(classifier_model_path).exists():
            classifier.load_model(classifier_model_path)
        
        # Classify the image first
        classification_result = classifier.classify_image(image_path)
        
        # Extract text using OCR
        ocr_result = ocr_processor.extract_text_from_image(image_path)
        
        # Combine results
        processing_result = {
            'image_path': image_path,
            'classification': classification_result,
            'ocr_results': {
                'raw_text': ocr_result.raw_text,
                'processed_text': ocr_result.processed_text,
                'confidence': ocr_result.confidence,
                'detected_elements': ocr_result.detected_elements,
                'bounding_boxes': ocr_result.bounding_boxes
            },
            'processing_errors': ocr_result.processing_errors,
            'processing_status': 'completed' if ocr_result.raw_text else 'failed'
        }
        
        logger.info(f"Image processing completed for {image_path}")
        return processing_result
        
    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        return {
            'image_path': image_path,
            'classification': {'predicted_class': 'unknown', 'confidence': 0.0},
            'ocr_results': {
                'raw_text': '',
                'processed_text': '',
                'confidence': 0.0,
                'detected_elements': {},
                'bounding_boxes': []
            },
            'processing_errors': [str(e)],
            'processing_status': 'failed'
        }

# Example usage and testing
if __name__ == "__main__":
    # Test the OCR processor
    test_image_path = "test_images/medication_label.jpg"
    
    if Path(test_image_path).exists():
        print("Testing medication label OCR processing...")
        result = process_medication_image(test_image_path)
        
        print(f"Processing Status: {result['processing_status']}")
        print(f"OCR Confidence: {result['ocr_results']['confidence']:.2f}%")
        print(f"Detected Text: {result['ocr_results']['processed_text'][:100]}...")
        print(f"Detected Elements: {json.dumps(result['ocr_results']['detected_elements'], indent=2)}")
        
        if result['processing_errors']:
            print(f"Errors: {result['processing_errors']}")
    else:
        print(f"Test image not found: {test_image_path}")
        print("Please place a medication label image at the specified path to test the OCR functionality.")
