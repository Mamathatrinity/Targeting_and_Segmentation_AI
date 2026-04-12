"""
YAML Prompt Loader
Loads and parses YAML prompt files
Based on PDF recommendations (Page 271-272)
"""
import yaml
from pathlib import Path
from typing import Dict, Any


def load_prompt(file_path: str) -> Dict[str, Any]:
    """
    Load a YAML prompt file
    
    Args:
        file_path: Path to YAML prompt file (relative or absolute)
        
    Returns:
        Dictionary containing prompt configuration
        
    Example:
        >>> prompt = load_prompt("prompts/planner_prompt.yaml")
        >>> print(prompt['role'])
        'QA automation expert'
    """
    path = Path(file_path)
    
    # If relative path, look in ai_agent/prompts directory
    if not path.is_absolute():
        base_dir = Path(__file__).parent.parent / "prompts"
        path = base_dir / file_path
    
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        prompt_data = yaml.safe_load(f)
    
    # Validate prompt_data is not empty
    if not prompt_data:
        raise ValueError(f"Prompt file is empty: {path}")
    
    return prompt_data


def load_module_contexts(config_path: str = "config/modules.yaml") -> Dict[str, str]:
    """
    Load module context configuration
    
    Args:
        config_path: Path to modules config file
        
    Returns:
        Dictionary mapping module names to their context descriptions
        
    Example:
        >>> contexts = load_module_contexts()
        >>> print(contexts['authentication'])
        'Login, SSO, session validation, security'
    """
    path = Path(config_path)
    
    if not path.is_absolute():
        base_dir = Path(__file__).parent.parent
        path = base_dir / config_path
    
    if not path.exists():
        # Return default contexts if file doesn't exist
        return {
            'authentication': 'Login, SSO, session validation, security',
            'dashboard': 'Charts, filters, data display, KPIs',
            'segmentation': 'Rule engine, grouping, conditions, filters',
            'target_list': 'User targeting, list creation, filtering'
        }
    
    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Extract module contexts
    if 'module_patterns' in config:
        # New format with detailed patterns
        return {
            name: patterns.get('common_workflows', [name])[0] if isinstance(patterns.get('common_workflows'), list) else name
            for name, patterns in config.get('module_patterns', {}).items()
        }
    elif 'modules' in config:
        # Simple format with just contexts
        if isinstance(config['modules'], dict):
            return config['modules']
        elif isinstance(config['modules'], list):
            # List of module objects
            return {mod['name'].lower(): mod['context'] for mod in config['modules']}
    
    return {}
