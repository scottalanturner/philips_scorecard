import yaml
import os
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    server: str
    database: str
    username: str
    password: str

@dataclass
class APIConfig:
    api_key: str
    api_version: str
    azure_endpoint: str
    model: str

class ConfigurationError(Exception):
    """Raised when there's an error loading configuration"""
    pass

class ConfigLoader:
    def __init__(self):
        """
        Initialize the config loader using project root-relative paths
        """
        # Get project root directory (2 levels up from this file)
        self.project_root = Path(__file__).parent.parent.parent
        
        # Set paths relative to project root
        self.config_path = self.project_root / "config" / "config.yml"
        self.env_path = self.project_root / ".env"
        
        # Load environment variables
        load_dotenv(self.env_path)
    
    def load_database_config(self) -> DatabaseConfig:
        """Load database configuration from config file and environment variables"""
        try:
            # Load YAML config
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            db_config = config.get('db', {})
            
            # Get credentials from environment variables
            username = os.getenv('DB_USERNAME') or db_config.get('username')
            password = os.getenv('DB_PASSWORD')
            
            # Validate required fields
            required_fields = {
                'server': db_config.get('server'),
                'database': db_config.get('database'),
                'username': username,
                'password': password
            }
            
            missing_fields = [k for k, v in required_fields.items() if not v]
            if missing_fields:
                raise ConfigurationError(
                    f"Missing required configuration fields: {', '.join(missing_fields)}"
                )
            
            return DatabaseConfig(
                server=db_config['server'],
                database=db_config['database'],
                username=username,
                password=password
            )
            
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parsing YAML configuration: {str(e)}")

    def load_api_config(self) -> APIConfig:
        """Load API configuration from environment variables"""
        try:
            # Load YAML config
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            llm_config = config.get('llm', {})
            
            api_key = os.getenv('AZURE_OPENAI_API_KEY')
            api_version = llm_config.get('api_version')
            azure_endpoint = llm_config.get('endpoint')
            model = llm_config.get('model')
            
            # Validate required fields
            if not api_key:
                raise ConfigurationError("API key not found in environment variables.")
            
            return APIConfig(
                api_key=api_key,
                api_version=api_version,
                azure_endpoint=azure_endpoint,
                model=model
            )
        except Exception as e:
            raise ConfigurationError(f"Error loading API configuration: {e}")