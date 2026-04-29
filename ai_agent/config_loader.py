"""
Configuration Loader
Loads and validates YAML configuration files
"""
import os
from typing import Dict, List, Optional
from ai_agent.utils.prompt_loader import load_yaml_config


class ConfigLoader:
    """Loads YAML configuration for multi-module testing"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config.yaml"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        if not os.path.exists(self.config_path):
            print(f"⚠ Config file not found: {self.config_path}")
            print("Using default single-module configuration")
            return self._get_default_config()
        
        config = load_yaml_config(self.config_path)
        if config:
            print(f"✓ Loaded config from: {self.config_path}")
            return config
        print(f"❌ Error parsing YAML config: {self.config_path}")
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Return default configuration"""
        return {
            "app": {
                "base_url": "",
                "headless": False,
                "timeout": 30
            },
            "mode": "full-run",
            "modules": [],
            "agents": {
                "planner": {"max_tokens": 300, "temperature": 0},
                "designer": {"max_tokens": 500, "temperature": 0, "max_tests": 10},
                "validator": {"max_tokens": 200, "temperature": 0}
            },
            "limits": {
                "max_tests_total": 20,
                "max_iterations": 1,
                "timeout_minutes": 30
            },
            "observability": {
                "langfuse_enabled": True,
                "track_tokens": True,
                "track_costs": True
            }
        }
    
    def get_base_url(self) -> str:
        """Get application base URL"""
        return self.config.get("app", {}).get("base_url", "")
    
    def get_modules(self) -> List[Dict]:
        """Get enabled modules in order"""
        modules = self.config.get("modules", [])
        return [m for m in modules if m.get("enabled", True)]
    
    def get_mode(self) -> str:
        """Get execution mode"""
        return self.config.get("mode", "full-run")
    
    def get_agent_config(self, agent_name: str) -> Dict:
        """Get configuration for specific agent"""
        agents = self.config.get("agents", {})
        return agents.get(agent_name, {})
    
    def get_limits(self) -> Dict:
        """Get execution limits"""
        return self.config.get("limits", {
            "max_tests_total": 20,
            "max_iterations": 1,
            "timeout_minutes": 30
        })
    
    def get_browser_settings(self) -> Dict:
        """Get browser configuration"""
        app = self.config.get("app", {})
        return {
            "headless": app.get("headless", False),
            "timeout": app.get("timeout", 30)
        }
    
    def is_langfuse_enabled(self) -> bool:
        """Check if Langfuse tracking is enabled"""
        obs = self.config.get("observability", {})
        return obs.get("langfuse_enabled", True)


# Singleton instance
_config_loader = None


def get_config(config_path: Optional[str] = None) -> ConfigLoader:
    """Get global configuration loader instance"""
    global _config_loader
    if _config_loader is None or config_path:
        _config_loader = ConfigLoader(config_path)
    return _config_loader
