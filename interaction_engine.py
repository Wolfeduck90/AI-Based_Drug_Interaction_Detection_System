"""
Drug Interaction Detection Engine
Handles drug name matching, interaction lookup, and risk assessment
Uses machine learning models for prediction and database lookups for known interactions
"""

import re
import json
import requests
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz, process
import sqlite3
from sqlalchemy.orm import Session
from database import Drug, Interaction, get_db
import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModel
import torch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DrugMatch:
    """Represents a matched drug with confidence scores"""
    drug_name: str
    matched_name: str
    confidence: float
    drug_id: Optional[int] = None
    brand_names: List[str] = None
    generic_name: str = ""
    rxcui: str = ""

@dataclass
class InteractionAlert:
    """Represents a drug interaction alert"""
    drug1: str
    drug2: str
    interaction_type: str
    severity: str
    description: str
    clinical_effects: str
    management: str
    confidence: float
    risk_score: float
    source: str

class DrugNameMatcher:
    """
    Handles drug name matching using multiple approaches:
    1. Exact matching
    2. Fuzzy string matching
    3. NLP-based semantic matching
    """
    
    def __init__(self, db_session: Session = None):
        self.db = db_session
        self.drug_names_cache = {}
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 3), max_features=5000)
        self.drug_vectors = None
        self.drug_list = []
        self.load_drug_database()
        
        # Initialize NLP model for semantic matching
        try:
            self.tokenizer = AutoTokenizer.from_pretrained('microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext')
            self.model = AutoModel.from_pretrained('microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext')
            self.nlp_available = True
        except:
            logger.warning("BioBERT model not available, using fallback methods")
            self.nlp_available = False
    
    def load_drug_database(self):
        """Load drug names from database and create search indices"""
        try:
            if not self.db:
                # Create a temporary session if none provided
                from database import SessionLocal
                self.db = SessionLocal()
            
            # Load all drugs from database
            drugs = self.db.query(Drug).all()
            
            # Create comprehensive drug name list
            all_drug_names = []
            self.drug_names_cache = {}
            
            for drug in drugs:
                # Add generic name
                generic_name = drug.name.lower()
                all_drug_names.append(generic_name)
                self.drug_names_cache[generic_name] = {
                    'drug_id': drug.id,
                    'generic_name': drug.name,
                    'brand_names': json.loads(drug.brand_names) if drug.brand_names else [],
                    'rxcui': drug.rxcui
                }
                
                # Add brand names
                if drug.brand_names:
                    brand_names = json.loads(drug.brand_names)
                    for brand in brand_names:
                        brand_lower = brand.lower()
                        all_drug_names.append(brand_lower)
                        self.drug_names_cache[brand_lower] = {
                            'drug_id': drug.id,
                            'generic_name': drug.name,
                            'brand_names': brand_names,
                            'rxcui': drug.rxcui
                        }
            
            self.drug_list = list(set(all_drug_names))
            
            # Create TF-IDF vectors for fuzzy matching
            if self.drug_list:
                self.drug_vectors = self.vectorizer.fit_transform(self.drug_list)
            
            logger.info(f"Loaded {len(self.drug_list)} drug names from database")
            
        except Exception as e:
            logger.error(f"Failed to load drug database: {e}")
            self.drug_list = []
            self.drug_names_cache = {}
    
    def match_drug_names(self, extracted_names: List[str], threshold: float = 0.7) -> List[DrugMatch]:
        """
        Match extracted drug names against database using multiple methods
        Returns list of matched drugs with confidence scores
        """
        matched_drugs = []
        
        for name in extracted_names:
            if not name or len(name.strip()) < 2:
                continue
            
            name_clean = self._clean_drug_name(name)
            best_matches = self._find_best_matches(name_clean, threshold)
            
            for match in best_matches:
                drug_info = self.drug_names_cache.get(match['matched_name'].lower(), {})
                
                drug_match = DrugMatch(
                    drug_name=name,
                    matched_name=match['matched_name'],
                    confidence=match['confidence'],
                    drug_id=drug_info.get('drug_id'),
                    brand_names=drug_info.get('brand_names', []),
                    generic_name=drug_info.get('generic_name', ''),
                    rxcui=drug_info.get('rxcui', '')
                )
                matched_drugs.append(drug_match)
        
        # Remove duplicates and sort by confidence
        unique_matches = self._deduplicate_matches(matched_drugs)
        return sorted(unique_matches, key=lambda x: x.confidence, reverse=True)
    
    def _clean_drug_name(self, name: str) -> str:
        """Clean and normalize drug name for matching"""
        # Remove common suffixes and prefixes
        name = re.sub(r'\b(tablet|capsule|mg|g|ml|injection|solution|cream|ointment)\b', '', name, flags=re.IGNORECASE)
        
        # Remove numbers and dosage information
        name = re.sub(r'\d+(?:\.\d+)?(?:mg|g|ml|mcg|µg)', '', name, flags=re.IGNORECASE)
        
        # Remove special characters and extra spaces
        name = re.sub(r'[^\w\s]', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name.lower()
    
    def _find_best_matches(self, drug_name: str, threshold: float) -> List[Dict]:
        """Find best matches using multiple matching algorithms"""
        matches = []
        
        # Method 1: Exact matching
        if drug_name in self.drug_names_cache:
            matches.append({
                'matched_name': drug_name,
                'confidence': 1.0,
                'method': 'exact'
            })
        
        # Method 2: Fuzzy string matching
        fuzzy_matches = process.extract(drug_name, self.drug_list, limit=5, scorer=fuzz.ratio)
        for match_name, score in fuzzy_matches:
            if score >= threshold * 100:  # fuzzywuzzy uses 0-100 scale
                matches.append({
                    'matched_name': match_name,
                    'confidence': score / 100.0,
                    'method': 'fuzzy'
                })
        
        # Method 3: TF-IDF based matching
        if self.drug_vectors is not None:
            tfidf_matches = self._tfidf_matching(drug_name, threshold)
            matches.extend(tfidf_matches)
        
        # Method 4: Semantic matching using NLP model
        if self.nlp_available:
            semantic_matches = self._semantic_matching(drug_name, threshold)
            matches.extend(semantic_matches)
        
        # Deduplicate and return top matches
        unique_matches = {}
        for match in matches:
            name = match['matched_name']
            if name not in unique_matches or match['confidence'] > unique_matches[name]['confidence']:
                unique_matches[name] = match
        
        return list(unique_matches.values())
    
    def _tfidf_matching(self, drug_name: str, threshold: float) -> List[Dict]:
        """Use TF-IDF vectors for similarity matching"""
        try:
            query_vector = self.vectorizer.transform([drug_name])
            similarities = cosine_similarity(query_vector, self.drug_vectors).flatten()
            
            matches = []
            for i, similarity in enumerate(similarities):
                if similarity >= threshold:
                    matches.append({
                        'matched_name': self.drug_list[i],
                        'confidence': float(similarity),
                        'method': 'tfidf'
                    })
            
            return matches
        except Exception as e:
            logger.error(f"TF-IDF matching failed: {e}")
            return []
    
    def _semantic_matching(self, drug_name: str, threshold: float) -> List[Dict]:
        """Use transformer model for semantic similarity matching"""
        try:
            # This is computationally expensive, so we limit to top candidates
            candidate_names = self.drug_list[:100]  # Limit for performance
            
            # Get embeddings
            query_embedding = self._get_embedding(drug_name)
            
            matches = []
            for candidate in candidate_names:
                candidate_embedding = self._get_embedding(candidate)
                similarity = cosine_similarity([query_embedding], [candidate_embedding])[0][0]
                
                if similarity >= threshold:
                    matches.append({
                        'matched_name': candidate,
                        'confidence': float(similarity),
                        'method': 'semantic'
                    })
            
            return matches
        except Exception as e:
            logger.error(f"Semantic matching failed: {e}")
            return []
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding vector for text using BioBERT"""
        inputs = self.tokenizer(text, return_tensors='pt', truncation=True, padding=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
    
    def _deduplicate_matches(self, matches: List[DrugMatch]) -> List[DrugMatch]:
        """Remove duplicate matches based on drug_id"""
        seen_ids = set()
        unique_matches = []
        
        for match in matches:
            if match.drug_id and match.drug_id not in seen_ids:
                seen_ids.add(match.drug_id)
                unique_matches.append(match)
            elif not match.drug_id:  # Keep unmatched entries
                unique_matches.append(match)
        
        return unique_matches

class InteractionDetector:
    """
    Detects drug interactions using database lookups and ML models
    """
    
    def __init__(self, db_session: Session = None):
        self.db = db_session or SessionLocal()
        self.drug_matcher = DrugNameMatcher(self.db)
        self.interaction_cache = {}
        self.load_interaction_database()
    
    def load_interaction_database(self):
        """Load known drug interactions from database"""
        try:
            interactions = self.db.query(Interaction).all()
            logger.info(f"Loaded {len(interactions)} known interactions")
        except Exception as e:
            logger.error(f"Failed to load interactions: {e}")
    
    def detect_interactions(self, drug_names: List[str]) -> List[InteractionAlert]:
        """
        Main method to detect drug interactions
        Takes list of drug names and returns interaction alerts
        """
        # Match drug names to database
        matched_drugs = self.drug_matcher.match_drug_names(drug_names)
        
        if len(matched_drugs) < 2:
            logger.info(f"Need at least 2 drugs for interaction detection, got {len(matched_drugs)}")
            return []
        
        # Get all drug pairs for interaction checking
        drug_pairs = self._get_drug_pairs(matched_drugs)
        
        # Check each pair for interactions
        alerts = []
        for drug1, drug2 in drug_pairs:
            interaction_alerts = self._check_drug_pair_interaction(drug1, drug2)
            alerts.extend(interaction_alerts)
        
        # Sort by risk score and severity
        alerts.sort(key=lambda x: (self._severity_score(x.severity), x.risk_score), reverse=True)
        
        return alerts
    
    def _get_drug_pairs(self, drugs: List[DrugMatch]) -> List[Tuple[DrugMatch, DrugMatch]]:
        """Generate all unique pairs of drugs for interaction checking"""
        pairs = []
        for i in range(len(drugs)):
            for j in range(i + 1, len(drugs)):
                pairs.append((drugs[i], drugs[j]))
        return pairs
    
    def _check_drug_pair_interaction(self, drug1: DrugMatch, drug2: DrugMatch) -> List[InteractionAlert]:
        """
        Check if two drugs have known interactions
        Returns list of interaction alerts
        """
        alerts = []
        
        # Skip if either drug couldn't be matched to database
        if not drug1.drug_id or not drug2.drug_id:
            logger.debug(f"Skipping interaction check for unmatched drugs: {drug1.drug_name}, {drug2.drug_name}")
            return alerts
        
        try:
            # Query database for known interactions
            interactions = self.db.query(Interaction).join(
                drug_interaction_association, 
                Interaction.id == drug_interaction_association.c.interaction_id
            ).filter(
                drug_interaction_association.c.drug_id.in_([drug1.drug_id, drug2.drug_id])
            ).all()
            
            for interaction in interactions:
                # Calculate risk score based on severity and confidence
                risk_score = self._calculate_risk_score(
                    interaction.severity, 
                    interaction.evidence_level,
                    min(drug1.confidence, drug2.confidence)
                )
                
                alert = InteractionAlert(
                    drug1=drug1.matched_name,
                    drug2=drug2.matched_name,
                    interaction_type=interaction.interaction_type,
                    severity=interaction.severity,
                    description=interaction.description,
                    clinical_effects=interaction.clinical_effects or "",
                    management=interaction.management or "",
                    confidence=min(drug1.confidence, drug2.confidence),
                    risk_score=risk_score,
                    source=interaction.source or "database"
                )
                alerts.append(alert)
        
        except Exception as e:
            logger.error(f"Error checking drug interaction: {e}")
        
        # If no database interactions found, check for potential interactions using ML
        if not alerts:
            ml_alerts = self._predict_potential_interactions(drug1, drug2)
            alerts.extend(ml_alerts)
        
        return alerts
    
    def _predict_potential_interactions(self, drug1: DrugMatch, drug2: DrugMatch) -> List[InteractionAlert]:
        """
        Use ML models to predict potential interactions for drug pairs
        not found in the database
        """
        # This is a placeholder for ML-based prediction
        # In a full implementation, you would:
        # 1. Use drug properties (class, mechanism, etc.)
        # 2. Train models on known interactions
        # 3. Predict likelihood of new interactions
        
        # For now, we'll implement a simple rule-based approach
        alerts = []
        
        try:
            # Get drug information
            drug1_info = self.db.query(Drug).filter(Drug.id == drug1.drug_id).first()
            drug2_info = self.db.query(Drug).filter(Drug.id == drug2.drug_id).first()
            
            if not drug1_info or not drug2_info:
                return alerts
            
            # Simple rule: warn about same drug class interactions
            if (drug1_info.drug_class and drug2_info.drug_class and 
                drug1_info.drug_class == drug2_info.drug_class):
                
                alert = InteractionAlert(
                    drug1=drug1.matched_name,
                    drug2=drug2.matched_name,
                    interaction_type="drug-drug",
                    severity="moderate",
                    description=f"Potential interaction between drugs of the same class ({drug1_info.drug_class})",
                    clinical_effects="May have additive effects or increased risk of adverse reactions",
                    management="Monitor patient closely for signs of increased drug effects",
                    confidence=min(drug1.confidence, drug2.confidence) * 0.7,  # Lower confidence for predictions
                    risk_score=0.5,
                    source="ml_prediction"
                )
                alerts.append(alert)
        
        except Exception as e:
            logger.error(f"Error in ML prediction: {e}")
        
        return alerts
    
    def _calculate_risk_score(self, severity: str, evidence_level: str, confidence: float) -> float:
        """Calculate numerical risk score based on interaction parameters"""
        severity_scores = {
            'critical': 1.0,
            'major': 0.8,
            'moderate': 0.6,
            'minor': 0.3
        }
        
        evidence_scores = {
            'established': 1.0,
            'probable': 0.8,
            'theoretical': 0.5
        }
        
        severity_score = severity_scores.get(severity.lower(), 0.5)
        evidence_score = evidence_scores.get(evidence_level.lower(), 0.5)
        
        # Combine scores with confidence
        risk_score = (severity_score + evidence_score) / 2 * confidence
        
        return min(risk_score, 1.0)
    
    def _severity_score(self, severity: str) -> int:
        """Convert severity to numerical score for sorting"""
        scores = {
            'critical': 4,
            'major': 3,
            'moderate': 2,
            'minor': 1
        }
        return scores.get(severity.lower(), 0)

# External API integration for additional drug data
class ExternalDrugDataAPI:
    """
    Integrates with external APIs for drug information
    Useful for getting additional drug data and interaction information
    """
    
    def __init__(self):
        self.rxnorm_api_base = "https://rxnav.nlm.nih.gov/REST"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Drug-Interaction-Detector/1.0'
        })
    
    def search_drug_by_name(self, drug_name: str) -> Dict:
        """Search for drug information using RxNorm API"""
        try:
            url = f"{self.rxnorm_api_base}/drugs.json"
            params = {'name': drug_name}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data.get('drugGroup', {})
            
        except Exception as e:
            logger.error(f"External API search failed: {e}")
            return {}
    
    def get_drug_interactions(self, rxcui: str) -> List[Dict]:
        """Get drug interactions from RxNorm API"""
        try:
            url = f"{self.rxnorm_api_base}/interaction/interaction.json"
            params = {'rxcui': rxcui}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data.get('interactionTypeGroup', [])
            
        except Exception as e:
            logger.error(f"External API interaction lookup failed: {e}")
            return []

# Main interaction detection function
def detect_drug_interactions(drug_names: List[str], db_session: Session = None) -> Dict:
    """
    Main function to detect drug interactions from a list of drug names
    Returns comprehensive interaction analysis
    """
    try:
        detector = InteractionDetector(db_session)
        
        # Detect interactions
        alerts = detector.detect_interactions(drug_names)
        
        # Categorize alerts by severity
        critical_alerts = [a for a in alerts if a.severity.lower() == 'critical']
        major_alerts = [a for a in alerts if a.severity.lower() == 'major']
        moderate_alerts = [a for a in alerts if a.severity.lower() == 'moderate']
        minor_alerts = [a for a in alerts if a.severity.lower() == 'minor']
        
        # Calculate overall risk assessment
        max_risk_score = max([a.risk_score for a in alerts]) if alerts else 0.0
        
        result = {
            'total_interactions': len(alerts),
            'max_risk_score': max_risk_score,
            'risk_level': _get_risk_level(max_risk_score),
            'alerts': {
                'critical': [_alert_to_dict(a) for a in critical_alerts],
                'major': [_alert_to_dict(a) for a in major_alerts],
                'moderate': [_alert_to_dict(a) for a in moderate_alerts],
                'minor': [_alert_to_dict(a) for a in minor_alerts]
            },
            'recommendations': _generate_recommendations(alerts),
            'matched_drugs': [
                {
                    'original_name': match.drug_name,
                    'matched_name': match.matched_name,
                    'confidence': match.confidence,
                    'generic_name': match.generic_name
                }
                for match in detector.drug_matcher.match_drug_names(drug_names)
            ]
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Drug interaction detection failed: {e}")
        return {
            'total_interactions': 0,
            'max_risk_score': 0.0,
            'risk_level': 'unknown',
            'alerts': {'critical': [], 'major': [], 'moderate': [], 'minor': []},
            'recommendations': ['System error occurred during analysis'],
            'matched_drugs': [],
            'error': str(e)
        }

def _alert_to_dict(alert: InteractionAlert) -> Dict:
    """Convert InteractionAlert to dictionary"""
    return {
        'drug1': alert.drug1,
        'drug2': alert.drug2,
        'interaction_type': alert.interaction_type,
        'severity': alert.severity,
        'description': alert.description,
        'clinical_effects': alert.clinical_effects,
        'management': alert.management,
        'confidence': alert.confidence,
        'risk_score': alert.risk_score,
        'source': alert.source
    }

def _get_risk_level(risk_score: float) -> str:
    """Convert numerical risk score to categorical risk level"""
    if risk_score >= 0.8:
        return 'high'
    elif risk_score >= 0.6:
        return 'moderate'
    elif risk_score >= 0.3:
        return 'low'
    else:
        return 'minimal'

def _generate_recommendations(alerts: List[InteractionAlert]) -> List[str]:
    """Generate actionable recommendations based on detected interactions"""
    recommendations = []
    
    if not alerts:
        recommendations.append("No significant drug interactions detected.")
        return recommendations
    
    critical_count = sum(1 for a in alerts if a.severity.lower() == 'critical')
    major_count = sum(1 for a in alerts if a.severity.lower() == 'major')
    
    if critical_count > 0:
        recommendations.append("URGENT: Critical drug interactions detected. Consult healthcare provider immediately.")
    
    if major_count > 0:
        recommendations.append("Important: Major drug interactions found. Medical review recommended.")
    
    recommendations.append("Always inform your healthcare provider about all medications you are taking.")
    recommendations.append("Monitor for unusual symptoms or side effects.")
    
    return recommendations

# Example usage
if __name__ == "__main__":
    # Test the interaction detection system
    test_drugs = ["warfarin", "aspirin", "ibuprofen"]
    
    print("Testing drug interaction detection...")
