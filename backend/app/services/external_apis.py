"""
External APIs Integration
FDA, RxNorm, and other drug database integrations
"""

import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import json
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)

class ExternalAPIService:
    def __init__(self):
        self.fda_base_url = "https://api.fda.gov"
        self.rxnorm_base_url = "https://rxnav.nlm.nih.gov/REST"
        self.session = None
        self.cache = {}  # Simple in-memory cache
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_fda_drug(self, drug_name: str) -> Dict:
        """
        Search FDA drug database for medication information
        """
        cache_key = f"fda_{drug_name.lower()}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        url = f"{self.fda_base_url}/drug/label.json"
        params = {
            'search': f'openfda.brand_name:"{drug_name}" OR openfda.generic_name:"{drug_name}"',
            'limit': 5
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    result = self.parse_fda_response(data)
                    self.cache[cache_key] = result
                    return result
                else:
                    return {"error": f"FDA API error: {response.status}"}
        except Exception as e:
            logger.error(f"FDA API request failed: {e}")
            return {"error": f"FDA API request failed: {str(e)}"}
    
    def parse_fda_response(self, data: Dict) -> Dict:
        """
        Parse FDA API response into standardized format
        """
        try:
            results = data.get('results', [])
            if not results:
                return {"error": "No results found"}
            
            drug_info = results[0]
            openfda = drug_info.get('openfda', {})
            
            return {
                "brand_name": openfda.get('brand_name', [None])[0],
                "generic_name": openfda.get('generic_name', [None])[0],
                "manufacturer_name": openfda.get('manufacturer_name', [None])[0],
                "product_ndc": openfda.get('product_ndc', []),
                "route": openfda.get('route', []),
                "substance_name": openfda.get('substance_name', []),
                "dosage_form": openfda.get('dosage_form', [None])[0],
                "warnings": drug_info.get('warnings', []),
                "contraindications": drug_info.get('contraindications', []),
                "adverse_reactions": drug_info.get('adverse_reactions', [])
            }
        except Exception as e:
            logger.error(f"Error parsing FDA response: {e}")
            return {"error": f"Error parsing FDA response: {str(e)}"}
    
    async def get_rxnorm_data(self, drug_name: str) -> Dict:
        """
        Get standardized drug information from RxNorm
        """
        cache_key = f"rxnorm_{drug_name.lower()}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # First, find RxCUI for the drug
            rxcui = await self.find_rxcui(drug_name)
            if not rxcui:
                return {"error": "Drug not found in RxNorm"}
            
            # Get detailed drug information
            drug_info = await self.get_drug_details(rxcui)
            
            # Get related drugs and interactions
            related_drugs = await self.get_related_drugs(rxcui)
            
            result = {
                "rxcui": rxcui,
                "drug_info": drug_info,
                "related_drugs": related_drugs,
                "standard_name": drug_info.get("name"),
                "ingredients": drug_info.get("ingredients", [])
            }
            
            self.cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"RxNorm API error: {e}")
            return {"error": f"RxNorm API error: {str(e)}"}
    
    async def find_rxcui(self, drug_name: str) -> Optional[str]:
        """
        Find RxCUI identifier for drug name
        """
        url = f"{self.rxnorm_base_url}/drugs.json"
        params = {'name': drug_name}
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    drug_group = data.get('drugGroup', {})
                    concept_group = drug_group.get('conceptGroup', [])
                    
                    # Look for Semantic Clinical Drug first
                    for group in concept_group:
                        if group.get('tty') == 'SCD':
                            concepts = group.get('conceptProperties', [])
                            if concepts:
                                return concepts[0].get('rxcui')
                    
                    # Fallback to any available concept
                    for group in concept_group:
                        concepts = group.get('conceptProperties', [])
                        if concepts:
                            return concepts[0].get('rxcui')
                            
        except Exception as e:
            logger.error(f"RxNorm RxCUI lookup failed: {e}")
        
        return None
    
    async def get_drug_details(self, rxcui: str) -> Dict:
        """
        Get detailed drug information by RxCUI
        """
        url = f"{self.rxnorm_base_url}/rxcui/{rxcui}/properties.json"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    properties = data.get('properties', {})
                    return {
                        "name": properties.get('name'),
                        "synonym": properties.get('synonym'),
                        "tty": properties.get('tty'),
                        "language": properties.get('language'),
                        "suppress": properties.get('suppress')
                    }
        except Exception as e:
            logger.error(f"RxNorm drug details lookup failed: {e}")
        
        return {}
    
    async def get_related_drugs(self, rxcui: str) -> List[Dict]:
        """
        Get related drugs for given RxCUI
        """
        url = f"{self.rxnorm_base_url}/rxcui/{rxcui}/related.json"
        params = {'tty': 'SCD+SBD+GPCK+BPCK'}
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    related_group = data.get('relatedGroup', {})
                    concept_group = related_group.get('conceptGroup', [])
                    
                    related_drugs = []
                    for group in concept_group:
                        concepts = group.get('conceptProperties', [])
                        for concept in concepts:
                            related_drugs.append({
                                "rxcui": concept.get('rxcui'),
                                "name": concept.get('name'),
                                "tty": concept.get('tty')
                            })
                    
                    return related_drugs
        except Exception as e:
            logger.error(f"RxNorm related drugs lookup failed: {e}")
        
        return []
    
    async def check_drug_interactions_external(self, rxcui_list: List[str]) -> List[Dict]:
        """
        Check drug interactions using external interaction APIs
        """
        if len(rxcui_list) < 2:
            return []
        
        url = f"{self.rxnorm_base_url}/interaction/list.json"
        params = {'rxcuis': '+'.join(rxcui_list)}
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.parse_interaction_response(data)
        except Exception as e:
            logger.error(f"RxNorm interaction API error: {e}")
        
        return []
    
    def parse_interaction_response(self, data: Dict) -> List[Dict]:
        """
        Parse RxNorm interaction response
        """
        interactions = []
        
        try:
            full_interaction_type_group = data.get('fullInteractionTypeGroup', [])
            
            for interaction_group in full_interaction_type_group:
                source_name = interaction_group.get('sourceName', 'Unknown')
                interaction_types = interaction_group.get('fullInteractionType', [])
                
                for interaction_type in interaction_types:
                    interaction_pairs = interaction_type.get('interactionPair', [])
                    
                    for pair in interaction_pairs:
                        interactions.append({
                            "severity": pair.get('severity', 'Unknown'),
                            "description": pair.get('description', ''),
                            "drug1": pair.get('interactionConcept', [{}])[0].get('minConceptItem', {}).get('name', ''),
                            "drug2": pair.get('interactionConcept', [{}])[1].get('minConceptItem', {}).get('name', '') if len(pair.get('interactionConcept', [])) > 1 else '',
                            "source": source_name
                        })
        except Exception as e:
            logger.error(f"Error parsing interaction response: {e}")
        
        return interactions

class DrugStandardizationService:
    """
    Service to standardize drug names and map to standard databases
    """
    def __init__(self):
        self.external_api = ExternalAPIService()
        # Cache for frequently looked up drugs
        self.drug_cache = {}
        
        # Common drug name mappings
        self.common_mappings = {
            'tylenol': 'acetaminophen',
            'advil': 'ibuprofen',
            'motrin': 'ibuprofen',
            'aleve': 'naproxen',
            'zocor': 'simvastatin',
            'lipitor': 'atorvastatin',
            'crestor': 'rosuvastatin',
            'norvasc': 'amlodipine',
            'prinivil': 'lisinopril',
            'zestril': 'lisinopril'
        }
    
    async def standardize_drug_name(self, drug_name: str) -> Dict[str, Any]:
        """
        Standardize drug name using multiple sources
        """
        # Normalize input
        normalized_name = drug_name.lower().strip()
        
        # Check cache first
        if normalized_name in self.drug_cache:
            return self.drug_cache[normalized_name]
        
        # Check common mappings
        if normalized_name in self.common_mappings:
            normalized_name = self.common_mappings[normalized_name]
        
        try:
            # Try RxNorm first (most comprehensive)
            async with self.external_api as api:
                rxnorm_data = await api.get_rxnorm_data(normalized_name)
                
                if not rxnorm_data.get('error'):
                    standardized = {
                        'standard_name': rxnorm_data['standard_name'],
                        'rxcui': rxnorm_data['rxcui'],
                        'ingredients': rxnorm_data['ingredients'],
                        'source': 'rxnorm',
                        'standardized': True
                    }
                    
                    # Cache the result
                    self.drug_cache[drug_name.lower()] = standardized
                    return standardized
                
                # Fallback to FDA database
                fda_data = await api.search_fda_drug(normalized_name)
                if not fda_data.get('error'):
                    standardized = {
                        'standard_name': fda_data.get('brand_name', drug_name),
                        'generic_name': fda_data.get('generic_name'),
                        'ndc_numbers': fda_data.get('product_ndc', []),
                        'source': 'fda',
                        'standardized': True
                    }
                    
                    self.drug_cache[drug_name.lower()] = standardized
                    return standardized
        
        except Exception as e:
            logger.error(f"Drug standardization failed: {e}")
        
        # If all else fails, return original name with flag
        result = {
            'standard_name': drug_name,
            'standardized': False,
            'source': 'input',
            'error': 'Could not standardize drug name'
        }
        
        self.drug_cache[drug_name.lower()] = result
        return result
    
    async def get_drug_interactions(self, drug_names: List[str]) -> List[Dict]:
        """
        Get drug interactions for a list of drug names
        """
        # First standardize all drug names and get RxCUIs
        rxcuis = []
        
        for drug_name in drug_names:
            standardized = await self.standardize_drug_name(drug_name)
            if standardized.get('rxcui'):
                rxcuis.append(standardized['rxcui'])
        
        if len(rxcuis) < 2:
            return []
        
        # Check interactions using RxNorm
        async with self.external_api as api:
            return await api.check_drug_interactions_external(rxcuis)

# Global services
external_api_service = ExternalAPIService()
drug_standardization_service = DrugStandardizationService()