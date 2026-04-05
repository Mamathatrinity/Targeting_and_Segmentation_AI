"""
Prompt Formatter with Variable Injection
Formats YAML prompts with dynamic values
Based on PDF recommendations (Page 272)
"""
from typing import Dict, Any


def format_prompt(prompt_yaml: Dict[str, Any], **kwargs) -> str:
    """
    Format a YAML prompt by injecting variables
    
    Args:
        prompt_yaml: Loaded YAML prompt dictionary
        **kwargs: Variables to inject into the prompt
        
    Returns:
        Formatted prompt string ready for LLM
        
    Example:
        >>> prompt = load_prompt("planner_prompt.yaml")
        >>> formatted = format_prompt(
        ...     prompt,
        ...     module_name="Authentication",
        ...     module_context="Login, SSO, security",
        ...     ui_data='{"buttons": ["Login", "Register"]}'
        ... )
    """
    # Extract prompt sections
    role = prompt_yaml.get('role', '')
    task = prompt_yaml.get('task', '')
    instructions = prompt_yaml.get('instructions', [])
    rules = prompt_yaml.get('rules', [])
    constraints = prompt_yaml.get('constraints', [])
    output_format = prompt_yaml.get('output_format', '')
    
    # Convert lists to strings
    if isinstance(instructions, list):
        instructions_str = '\n'.join(f"- {item}" for item in instructions)
    else:
        instructions_str = str(instructions)
    
    if isinstance(rules, list):
        rules_str = '\n'.join(f"- {item}" for item in rules)
    else:
        rules_str = str(rules)
    
    if isinstance(constraints, list):
        constraints_str = '\n'.join(f"- {item}" for item in constraints)
    else:
        constraints_str = str(constraints)
    
    # Replace placeholders in all sections
    for key, value in kwargs.items():
        placeholder = f"{{{key}}}"
        str_value = str(value)
        
        role = role.replace(placeholder, str_value)
        task = task.replace(placeholder, str_value)
        instructions_str = instructions_str.replace(placeholder, str_value)
        rules_str = rules_str.replace(placeholder, str_value)
        constraints_str = constraints_str.replace(placeholder, str_value)
        output_format = output_format.replace(placeholder, str_value)
    
    # Build final prompt
    formatted_prompt = f"""Role: {role}

Task:
{task}"""
    
    if instructions_str and instructions_str.strip():
        formatted_prompt += f"""

Instructions:
{instructions_str}"""
    
    if rules_str and rules_str.strip():
        formatted_prompt += f"""

Rules:
{rules_str}"""
    
    if constraints_str and constraints_str.strip():
        formatted_prompt += f"""

Constraints:
{constraints_str}"""
    
    if output_format and output_format.strip():
        formatted_prompt += f"""

Output Format:
{output_format}"""
    
    return formatted_prompt.strip()


def inject_variables(text: str, **kwargs) -> str:
    """
    Simple variable injection into text
    
    Args:
        text: Text with {variable} placeholders
        **kwargs: Variables to inject
        
    Returns:
        Text with variables replaced
        
    Example:
        >>> inject_variables("Module: {name}", name="Login")
        'Module: Login'
    """
    result = text
    for key, value in kwargs.items():
        placeholder = f"{{{key}}}"
        result = result.replace(placeholder, str(value))
    return result
