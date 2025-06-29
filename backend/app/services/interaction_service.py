"""
Drug interaction detection service
"""

import asyncio
from typing import List, Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import structlog
from fuzzywuzzy import fuzz, process

from app.models.database_models import Drug, DrugInteraction, Medication
from app.schemas.interactions import InteractionAlert, SeverityLevel
from app.core.exceptions import ProcessingException

logger = structlog.get_logger(__name__)

class InteractionService:
    """Drug interaction detection and analysis service"""
    
    def __init__(self):
        self.severity_scores = {
            SeverityLevel.MINOR: 1,
            SeverityLevel.MODERATE: 2,
            SeverityLevel.MAJOR: 3,
            SeverityLevel.CRITICAL: 4
        }
    
    async def check_interactions(
        self,
        db: AsyncSession,
        medication_ids: Optional[List[int]] = None,
        drug_names: Optional[List[str]] = None,
        user_id: Optional[int] = None
    ) -> List[InteractionAlert]:
        """
        Check for drug interactions
        """
        try:
            # Get medications to check
            medications = await self._get_medications_to_check(
                db, medication_ids, drug_names, user_id
            )
            
            if len(medications) < 2:
                return []
            
            # Find interactions
            interactions = await self._find_interactions(db, medications)
            
            # Convert to alerts
            alerts = []
            for interaction in interactions:
                alert = await self._create_interaction_alert(interaction, medications)
                alerts.append(alert)
            
            # Sort by severity and risk score
            alerts.sort(key=lambda x: (self.severity_scores[x.severity], x.risk_score), reverse=True)
            
            return alerts
            
        except Exception as e:
            logger.error("Interaction check failed", error=str(e))
            raise ProcessingException(f"Interaction check failed: {str(e)}")
    
    async def _get_medications_to_check(
        self,
        db: AsyncSession,
        medication_ids: Optional[List[int]],
        drug_names: Optional[List[str]],
        user_id: Optional[int]
    ) -> List[Dict]:
        """Get medications to check for interactions"""
        medications = []
        
        # Get medications by IDs
        if medication_ids:
            result = await db.execute(
                select(Medication, Drug)
                .join(Drug, Medication.drug_id == Drug.id, isouter=True)
                .where(Medication.id.in_(medication_ids))
            )
            
            for medication, drug in result.all():
                medications.append({
                    'medication_id': medication.id,
                    'drug_id': drug.id if drug else None,
                    'name': drug.name if drug else medication.custom_name,
                    'generic_name': drug.generic_name if drug else None,
                    'drug': drug
                })
        
        # Get medications by drug names
        if drug_names:
            for drug_name in drug_names:
                # Try to find exact match first
                result = await db.execute(
                    select(Drug).where(
                        or_(
                            Drug.name.ilike(f"%{drug_name}%"),
                            Drug.generic_name.ilike(f"%{drug_name}%")
                        )
                    )
                )
                drug = result.scalar_one_or_none()
                
                if drug:
                    medications.append({
                        'medication_id': None,
                        'drug_id': drug.id,
                        'name': drug.name,
                        'generic_name': drug.generic_name,
                        'drug': drug
                    })
                else:
                    # Add as custom medication
                    medications.append({
                        'medication_id': None,
                        'drug_id': None,
                        'name': drug_name,
                        'generic_name': None,
                        'drug': None
                    })
        
        # Get user's active medications if user_id provided
        if user_id and not medication_ids:
            result = await db.execute(
                select(Medication, Drug)
                .join(Drug, Medication.drug_id == Drug.id, isouter=True)
                .where(
                    and_(
                        Medication.user_id == user_id,
                        Medication.is_active == True
                    )
                )
            )
            
            for medication, drug in result.all():
                medications.append({
                    'medication_id': medication.id,
                    'drug_id': drug.id if drug else None,
                    'name': drug.name if drug else medication.custom_name,
                    'generic_name': drug.generic_name if drug else None,
                    'drug': drug
                })
        
        return medications
    
    async def _find_interactions(
        self,
        db: AsyncSession,
        medications: List[Dict]
    ) -> List[DrugInteraction]:
        """Find interactions between medications"""
        interactions = []
        
        # Check all pairs of medications
        for i, med1 in enumerate(medications):
            for med2 in medications[i+1:]:
                # Skip if either medication doesn't have a drug_id
                if not med1.get('drug_id') or not med2.get('drug_id'):
                    continue
                
                # Query for interaction
                result = await db.execute(
                    select(DrugInteraction).where(
                        or_(
                            and_(
                                DrugInteraction.drug1_id == med1['drug_id'],
                                DrugInteraction.drug2_id == med2['drug_id']
                            ),
                            and_(
                                DrugInteraction.drug1_id == med2['drug_id'],
                                DrugInteraction.drug2_id == med1['drug_id']
                            )
                        )
                    )
                )
                
                interaction = result.scalar_one_or_none()
                if interaction:
                    # Add medication info to interaction
                    interaction.med1_info = med1
                    interaction.med2_info = med2
                    interactions.append(interaction)
        
        return interactions
    
    async def _create_interaction_alert(
        self,
        interaction: DrugInteraction,
        medications: List[Dict]
    ) -> InteractionAlert:
        """Create interaction alert from database interaction"""
        
        # Calculate confidence and risk score
        confidence = self._calculate_confidence(interaction)
        risk_score = self._calculate_risk_score(interaction, confidence)
        
        return InteractionAlert(
            drug1_name=interaction.med1_info['name'],
            drug2_name=interaction.med2_info['name'],
            severity=interaction.severity,
            description=interaction.clinical_effect,
            clinical_effects=interaction.clinical_effect,
            management=interaction.management,
            confidence=confidence,
            risk_score=risk_score,
            source=interaction.source or "database"
        )
    
    def _calculate_confidence(self, interaction: DrugInteraction) -> float:
        """Calculate confidence score for interaction"""
        evidence_scores = {
            'systematic_review': 1.0,
            'clinical_trial': 0.9,
            'observational': 0.7,
            'case_report': 0.5,
            'theoretical': 0.3
        }
        
        documentation_scores = {
            'excellent': 1.0,
            'good': 0.8,
            'fair': 0.6,
            'poor': 0.4
        }
        
        evidence_score = evidence_scores.get(interaction.evidence_level, 0.5)
        doc_score = documentation_scores.get(interaction.documentation, 0.6)
        
        return (evidence_score + doc_score) / 2
    
    def _calculate_risk_score(self, interaction: DrugInteraction, confidence: float) -> float:
        """Calculate risk score for interaction"""
        severity_score = self.severity_scores[interaction.severity] / 4.0
        
        # Adjust for frequency and onset
        frequency_multiplier = 1.0
        if interaction.frequency == 'common':
            frequency_multiplier = 1.2
        elif interaction.frequency == 'rare':
            frequency_multiplier = 0.8
        
        onset_multiplier = 1.0
        if interaction.onset == 'rapid':
            onset_multiplier = 1.1
        
        risk_score = severity_score * confidence * frequency_multiplier * onset_multiplier
        
        return min(risk_score, 1.0)
    
    async def generate_recommendations(
        self,
        interactions: List[InteractionAlert]
    ) -> List[str]:
        """Generate clinical recommendations based on interactions"""
        recommendations = []
        
        if not interactions:
            recommendations.append("No significant drug interactions detected.")
            return recommendations
        
        # Count interactions by severity
        critical_count = sum(1 for i in interactions if i.severity == SeverityLevel.CRITICAL)
        major_count = sum(1 for i in interactions if i.severity == SeverityLevel.MAJOR)
        
        if critical_count > 0:
            recommendations.extend([
                "🚨 URGENT: Critical drug interactions detected.",
                "Contact your healthcare provider immediately.",
                "Do not stop taking medications without medical supervision.",
                "Consider emergency care if experiencing adverse symptoms."
            ])
        
        if major_count > 0:
            recommendations.extend([
                "⚠️ Important: Major drug interactions found.",
                "Schedule an appointment with your healthcare provider.",
                "Monitor for unusual symptoms or side effects.",
                "Bring this interaction report to your appointment."
            ])
        
        # General recommendations
        recommendations.extend([
            "Always inform healthcare providers about all medications you're taking.",
            "Include over-the-counter drugs and supplements in medication lists.",
            "Keep an updated list of your medications with you.",
            "Use the same pharmacy when possible for interaction checking."
        ])
        
        return recommendations
    
    async def search_drug_by_name(
        self,
        db: AsyncSession,
        drug_name: str,
        limit: int = 20
    ) -> List[Drug]:
        """Search for drugs by name using fuzzy matching"""
        
        # First try exact matches
        result = await db.execute(
            select(Drug).where(
                or_(
                    Drug.name.ilike(f"%{drug_name}%"),
                    Drug.generic_name.ilike(f"%{drug_name}%")
                )
            ).limit(limit)
        )
        
        exact_matches = result.scalars().all()
        
        if exact_matches:
            return exact_matches
        
        # If no exact matches, try fuzzy matching
        all_drugs_result = await db.execute(select(Drug))
        all_drugs = all_drugs_result.scalars().all()
        
        # Create list of drug names for fuzzy matching
        drug_names = []
        for drug in all_drugs:
            drug_names.append((drug.name, drug))
            if drug.generic_name:
                drug_names.append((drug.generic_name, drug))
        
        # Perform fuzzy matching
        matches = process.extract(
            drug_name,
            [name for name, _ in drug_names],
            limit=limit,
            scorer=fuzz.ratio
        )
        
        # Filter by minimum score and return drugs
        fuzzy_matches = []
        seen_ids = set()
        
        for match_name, score in matches:
            if score >= 70:  # Minimum similarity threshold
                for name, drug in drug_names:
                    if name == match_name and drug.id not in seen_ids:
                        fuzzy_matches.append(drug)
                        seen_ids.add(drug.id)
                        break
        
        return fuzzy_matches

# Global interaction service instance
interaction_service = InteractionService()