"""
Prompt Formatter with Variable Injection
Formats YAML prompts with dynamic values
Based on PDF recommendations (Page 272)
"""
from typing import Dict, Any
import json


def format_prompt(prompt_yaml: Dict[str, Any], **kwargs) -> str:
    """
    Format a YAML prompt by injecting variables
    
    Args:
        prompt_yaml: Loaded YAML prompt dictionary
        **kwargs: Variables to inject into the prompt
        
    Returns:
        Formatted prompt string ready for LLM
    """
    # Build prompt from YAML sections
    prompt_parts = []
    
    # Add all top-level string fields
    for key, value in prompt_yaml.items():
        if isinstance(value, str) and value:
            # Replace variable placeholders
            formatted_value = value
            for var_name, var_value in kwargs.items():
                placeholder = f"{{{var_name}}}"
                formatted_value = formatted_value.replace(placeholder, str(var_value))
            
            prompt_parts.append(f"=== {key.upper().replace('_', ' ')} ===\n{formatted_value}")
        elif isinstance(value, dict):
            # Handle nested dictionaries
            section_text = f"=== {key.upper().replace('_', ' ')} ===\n"
            section_text += json.dumps(value, indent=2)
            prompt_parts.append(section_text)
        elif isinstance(value, list):
            # Handle lists
            section_text = f"=== {key.upper().replace('_', ' ')} ===\n"
            for item in value:
                if isinstance(item, dict):
                    section_text += json.dumps(item, indent=2) + "\n\n"
                else:
                    section_text += f"- {item}\n"
            prompt_parts.append(section_text)
    
    return "\n\n".join(prompt_parts)
