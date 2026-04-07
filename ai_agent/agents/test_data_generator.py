"""
AI Test Data Generator
Generates realistic HCP data for testing using AI
Understands medical context and creates believable test data
"""
from langchain_openai import AzureChatOpenAI
import json
import random
from typing import List, Dict
from ai_agent.config import AIConfig


class TestDataGenerator:
    """AI generates realistic test data for HCP application"""
    
    def __init__(self):
        AIConfig.validate()
        self.llm = AzureChatOpenAI(
            azure_deployment=AIConfig.AZURE_OPENAI_DEPLOYMENT,
            openai_api_version=AIConfig.AZURE_OPENAI_API_VERSION,
            azure_endpoint=AIConfig.AZURE_OPENAI_ENDPOINT,
            api_key=AIConfig.AZURE_OPENAI_API_KEY,
            temperature=0.7,  # Higher temp for variety
            max_tokens=3000
        )
    
    def generate_hcp_data(
        self,
        count: int = 10,
        specialties: List[str] = None,
        states: List[str] = None,
        include_edge_cases: bool = True
    ) -> List[Dict]:
        """
        Generate realistic HCP (Healthcare Professional) test data
        
        Args:
            count: Number of HCP records to generate
            specialties: List of medical specialties to include
            states: List of US states
            include_edge_cases: Include edge cases (special chars, long names, etc.)
            
        Returns:
            List of HCP dictionaries with realistic data
        """
        
        if not specialties:
            specialties = ["Cardiology", "Oncology", "Primary Care", "Endocrinology", "Neurology"]
        
        if not states:
            states = ["California", "New York", "Texas", "Florida", "Illinois"]
        
        prompt = f"""Generate {count} realistic Healthcare Professional (HCP) records for testing.

REQUIREMENTS:
- Include diverse medical specialties: {', '.join(specialties)}
- Geographic diversity: {', '.join(states)}
- Realistic data: Names sound like real doctors, NPIs are valid format
- Include variety: Different Rx volumes, institution types, years of experience

{"INCLUDE EDGE CASES:" if include_edge_cases else ""}
{'''- Special characters in names: O'Brien, García, Dr. Smith-Jones
- Very long names (30+ characters)
- Minimum/maximum Rx volumes (0 and 1,000,000)
- Rare specialties mixed in''' if include_edge_cases else ''}

RETURN JSON ARRAY:
[
  {{
    "npi": "1234567890",  // 10-digit number
    "name": "Dr. Sarah Johnson, M.D.",
    "specialty": "Cardiology",
    "state": "California",
    "city": "Los Angeles",
    "institution": "UCLA Medical Center",
    "rx_volume_monthly": 150,
    "years_experience": 12,
    "accepts_new_patients": true,
    "phone": "(555) 123-4567",
    "email": "s.johnson@ucla.edu"
  }}
]

Generate {count} varied, realistic HCP records now.
"""
        
        response = self.llm.invoke(prompt)
        
        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            hcp_data = json.loads(content)
            
            # Ensure NPIs are unique
            self._ensure_unique_npis(hcp_data)
            
            return hcp_data
        except:
            # Fallback to programmatic generation
            return self._generate_fallback_data(count, specialties, states)
    
    def generate_segment_test_data(self, segment_config: Dict) -> Dict:
        """
        Generate test data for a specific segment configuration
        
        Args:
            segment_config: {
                "name": "Top CA Cardiologists",
                "filters": {
                    "specialty": "Cardiology",
                    "state": "California",
                    "rx_volume_min": 100
                }
            }
            
        Returns:
            {
                "segment": {...},
                "matching_hcps": [...],  // HCPs that SHOULD match filters
                "non_matching_hcps": [...],  // HCPs that should NOT match
                "edge_case_hcps": [...]  // Boundary cases
            }
        """
        
        filters = segment_config.get("filters", {})
        
        prompt = f"""Generate test data for HCP segment testing.

SEGMENT CONFIGURATION:
{json.dumps(segment_config, indent=2)}

GENERATE 3 TYPES OF HCP DATA:

1. MATCHING HCPs (10 records): 
   - Must satisfy ALL filters
   - Should match the segment criteria perfectly
   - Variety in other attributes

2. NON-MATCHING HCPs (10 records):
   - Violate at least ONE filter
   - Test different filter violations (wrong specialty, wrong state, low Rx volume)

3. EDGE CASE HCPs (5 records):
   - Exactly at filter boundaries
   - Example: If rx_volume_min=100, include HCP with exactly 100
   - Tricky cases like "Cardiology/Internal Medicine" (dual specialty)

RETURN JSON:
{{
  "matching_hcps": [{{...}}],
  "non_matching_hcps": [{{...}}],
  "edge_case_hcps": [{{...}}]
}}
"""
        
        response = self.llm.invoke(prompt)
        
        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except:
            return {
                "matching_hcps": [],
                "non_matching_hcps": [],
                "edge_case_hcps": []
            }
    
    def generate_performance_test_data(self, record_count: int) -> List[Dict]:
        """
        Generate large dataset for performance testing
        
        Args:
            record_count: Number of records (e.g., 100,000)
            
        Returns:
            Large HCP dataset
        """
        # For large datasets, use template-based generation with AI variety
        print(f"Generating {record_count:,} HCP records...")
        
        # Generate 100 AI templates
        templates = self.generate_hcp_data(count=100, include_edge_cases=False)
        
        # Replicate with variations
        large_dataset = []
        for i in range(record_count):
            template = templates[i % len(templates)]
            
            # Create variation
            hcp = template.copy()
            hcp["npi"] = str(1000000000 + i)  # Unique NPI
            hcp["rx_volume_monthly"] = random.randint(0, 500)
            hcp["years_experience"] = random.randint(1, 40)
            
            large_dataset.append(hcp)
        
        print(f"✓ Generated {len(large_dataset):,} HCP records")
        return large_dataset
    
    def _ensure_unique_npis(self, hcp_data: List[Dict]):
        """Ensure all NPI numbers are unique"""
        seen_npis = set()
        for hcp in hcp_data:
            while hcp["npi"] in seen_npis:
                # Generate new NPI
                hcp["npi"] = str(random.randint(1000000000, 9999999999))
            seen_npis.add(hcp["npi"])
    
    def _generate_fallback_data(
        self, 
        count: int, 
        specialties: List[str],
        states: List[str]
    ) -> List[Dict]:
        """Fallback programmatic generation if AI fails"""
        first_names = ["John", "Sarah", "Michael", "Emily", "David", "Jennifer"]
        last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis"]
        
        hcp_data = []
        for i in range(count):
            hcp_data.append({
                "npi": str(1000000000 + i),
                "name": f"Dr. {random.choice(first_names)} {random.choice(last_names)}, M.D.",
                "specialty": random.choice(specialties),
                "state": random.choice(states),
                "city": "Test City",
                "institution": "Test Hospital",
                "rx_volume_monthly": random.randint(0, 500),
                "years_experience": random.randint(1, 40),
                "accepts_new_patients": random.choice([True, False]),
                "phone": f"(555) {random.randint(100,999)}-{random.randint(1000,9999)}",
                "email": f"doctor{i}@test.com"
            })
        
        return hcp_data


# Example usage
if __name__ == "__main__":
    generator = TestDataGenerator()
    
    # Generate 10 realistic HCPs
    hcps = generator.generate_hcp_data(
        count=10,
        specialties=["Cardiology", "Oncology"],
        states=["California", "New York"],
        include_edge_cases=True
    )
    
    print("GENERATED HCP TEST DATA:")
    print(json.dumps(hcps[:3], indent=2))  # Show first 3
    
    # Generate segment-specific test data
    segment_config = {
        "name": "High-Value CA Cardiologists",
        "filters": {
            "specialty": "Cardiology",
            "state": "California",
            "rx_volume_min": 100
        }
    }
    
    segment_data = generator.generate_segment_test_data(segment_config)
    print("\nSEGMENT TEST DATA:")
    print(f"Matching HCPs: {len(segment_data['matching_hcps'])}")
    print(f"Non-matching HCPs: {len(segment_data['non_matching_hcps'])}")
    print(f"Edge cases: {len(segment_data['edge_case_hcps'])}")
