"""
YAML Prompt Loader
Loads and parses YAML prompt files
"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


def load_yaml_config(file_path: str) -> dict:
    """
    Load any YAML config file safely. Returns empty dict on error.
    Used by: executor.py, designer.py, planner.py
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def match_module(test_name: str, config: dict) -> Optional[dict]:
    """
    Return the first module config whose patterns match the test name.
    Used by: executor.py (_inject_config_steps), designer.py (match_queries_for_test)
    """
    test_lower = test_name.lower()
    for module_cfg in config.get("modules", {}).values():
        for pattern in module_cfg.get("patterns", []):
            if pattern.lower() in test_lower:
                return module_cfg
    return None


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
