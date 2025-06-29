"""
NLP Service for Drug Extraction
Advanced natural language processing for extracting structured medication data from OCR text
"""

import spacy
import re
from typing import Dict, List, Any, Optional
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
import asyncio
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class NLPService:
    def __init__(self):
        # Load pre-trained models
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found, using basic NLP")
            self.nlp = None
        
        # Load specialized medical NER model (fallback to basic if not available)
        try:
            self.medical_ner = pipeline(
                "ner",
                model="dmis-lab/biobert-base-cased-v1.1",
                tokenizer="dmis-lab/biobert-base-cased-v1.1",
                aggregation_strategy="simple"
            )
        except Exception as e:
            logger.warning(f"Medical NER model not available: {e}")
            self.medical_ner = None
        
        # Drug name patterns
        self.drug_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Proper nouns
            r'\b\d+\s*mg\b|\b\d+\s*mcg\b|\b\d+\s*g\b',  # Dosages
            r'\btablet[s]?\b|\bcapsule[s]?\b|\bml\b|\bmL\b'  # Forms
        ]
        
        # Common drug name corrections
        self.drug_corrections = {
            'lisinopril': 'Lisinopril',
            'metformin': 'Metformin',
            'atorvastatin': 'Atorvastatin',
            'amlodipine': 'Amlodipine',
            'omeprazole': 'Omeprazole',
            'simvastatin': 'Simvastatin',
            'losartan': 'Losartan',
            'hydrochlorothiazide': 'Hydrochlorothiazide'
        }
    
    async def parse_prescription_data(self, ocr_text: str) -> Dict[str, Any]:
        """
        Extract structured medication data from OCR text
        """
        try:
            # Clean and normalize text
            cleaned_text = self.clean_text(ocr_text)
            
            # Extract entities using NLP if available
            entities = {}
            if self.medical_ner:
                entities = await self.extract_medical_entities(cleaned_text)
            
            # Pattern-based extraction for specific fields
            patterns_result = self.extract_with_patterns(cleaned_text)
            
            # Combine and validate results
            structured_data = self.combine_extractions(entities, patterns_result)
            
            # Apply drug name corrections
            if structured_data.get("drug_name"):
                corrected_name = self.drug_corrections.get(
                    structured_data["drug_name"].lower(),
                    structured_data["drug_name"]
                )
                structured_data["drug_name"] = corrected_name
            
            return {
                "medication_name": structured_data.get("drug_name"),
                "generic_name": structured_data.get("generic_name"),
                "dosage": structured_data.get("dosage"),
                "quantity": structured_data.get("quantity"),
                "directions": structured_data.get("directions"),
                "prescriber": structured_data.get("prescriber"),
                "pharmacy": structured_data.get("pharmacy"),
                "rx_number": structured_data.get("rx_number"),
                "date_filled": structured_data.get("date_filled"),
                "ndc_number": structured_data.get("ndc_number"),
                "confidence_scores": structured_data.get("confidence_scores", {}),
                "raw_text": ocr_text
            }
            
        except Exception as e:
            logger.error(f"NLP parsing failed: {e}")
            return {
                "medication_name": None,
                "error": str(e),
                "raw_text": ocr_text
            }
    
    async def extract_medical_entities(self, text: str) -> Dict[str, List]:
        """
        Use transformer model to identify medical entities
        """
        if not self.medical_ner:
            return {}
        
        try:
            # Run NER pipeline
            entities = self.medical_ner(text)
            
            # Filter and categorize relevant entities
            categorized = {
                "medications": [],
                "dosages": [],
                "frequencies": [],
                "routes": []
            }
            
            for entity in entities:
                entity_group = entity.get('entity_group', '').upper()
                if entity_group in ['DRUG', 'MEDICATION', 'CHEMICAL']:
                    categorized['medications'].append(entity)
                elif 'DOSE' in entity_group or 'STRENGTH' in entity_group:
                    categorized['dosages'].append(entity)
                elif 'FREQ' in entity_group:
                    categorized['frequencies'].append(entity)
                elif 'ROUTE' in entity_group:
                    categorized['routes'].append(entity)
            
            return categorized
            
        except Exception as e:
            logger.error(f"Medical entity extraction failed: {e}")
            return {}
    
    def extract_with_patterns(self, text: str) -> Dict[str, Any]:
        """
        Pattern-based extraction for specific prescription fields
        """
        patterns = {
            'rx_number': [
                r'(?:Rx|RX|#)\s*:?\s*(\d+)',
                r'(?:Prescription|Script)\s*#?\s*:?\s*(\d+)',
                r'\b(\d{7,10})\b'  # Common Rx number format
            ],
            'ndc_number': [
                r'NDC\s*:?\s*([\d-]+)',
                r'(\d{5}-\d{3}-\d{2})',  # Standard NDC format
                r'(\d{5}-\d{4}-\d{1})',  # Alternative NDC format
            ],
            'date_filled': [
                r'(?:Date|Filled|Date Filled|Dispensed)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            ],
            'quantity': [
                r'(?:Qty|Quantity|Count)\s*:?\s*(\d+)',
                r'#(\d+)',
                r'(\d+)\s*(?:tablets?|capsules?|pills?)',
            ],
            'dosage': [
                r'(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|mL|units?))',
                r'(\d+(?:\.\d+)?/\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|mL))',  # Combination dosages
            ],
            'prescriber': [
                r'(?:Dr\.?|Doctor|Prescriber|Physician)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'(?:Prescribed by|Written by)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            ],
            'pharmacy': [
                r'(?:Pharmacy|Dispensed by|Filled at)\s*:?\s*([A-Z][^\n]*)',
                r'([A-Z][a-z]+\s+Pharmacy)',
            ],
            'directions': [
                r'(?:Take|Use|Apply|Directions?)\s*:?\s*([^\n]*)',
                r'(?:Sig|SIG)\s*:?\s*([^\n]*)',
            ],
            'frequency': [
                r'(?:once|twice|three times?|four times?)\s+(?:daily|per day|a day)',
                r'(?:every|q)\s*\d+\s*(?:hours?|hrs?|h)',
                r'(?:BID|TID|QID|QD|PRN)',
            ]
        }
        
        results = {}
        confidence_scores = {}
        
        for field, pattern_list in patterns.items():
            best_match = None
            best_confidence = 0
            
            for pattern in pattern_list:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Simple confidence based on match length and position
                    confidence = min(1.0, len(match.group(1 if match.groups() else 0)) / 20)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = match.group(1 if match.groups() else 0).strip()
            
            if best_match:
                results[field] = best_match
                confidence_scores[field] = best_confidence
        
        results['confidence_scores'] = confidence_scores
        return results
    
    def combine_extractions(self, entities: Dict, patterns: Dict) -> Dict[str, Any]:
        """
        Combine NLP entities with pattern-based extractions
        """
        combined = patterns.copy()
        
        # Use NLP entities to enhance pattern results
        if entities.get('medications'):
            # Take the highest confidence medication name
            best_med = max(entities['medications'], key=lambda x: x.get('score', 0))
            if best_med.get('score', 0) > 0.8:
                combined['drug_name'] = best_med['word']
        
        # Extract drug name from patterns if not found by NLP
        if not combined.get('drug_name'):
            combined['drug_name'] = self.extract_drug_name_from_text(patterns.get('directions', ''))
        
        return combined
    
    def extract_drug_name_from_text(self, text: str) -> Optional[str]:
        """
        Extract drug name using pattern matching
        """
        # Look for capitalized words that might be drug names
        words = text.split()
        for word in words:
            if (len(word) > 3 and 
                word[0].isupper() and 
                not word.isupper() and 
                word.isalpha()):
                return word
        return None
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        """
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

# Global NLP service instance
nlp_service = NLPService()