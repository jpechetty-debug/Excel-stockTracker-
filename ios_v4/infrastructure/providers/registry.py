"""
Provider Registry
Factory class enabling plugin-based instantiation of data providers.
"""

from typing import Dict, Type
from infrastructure.providers.base import MarketDataProvider
from infrastructure.logging.logger import logger


class ProviderRegistry:
    """Registry for managing and resolving MarketDataProviders."""
    
    _providers: Dict[str, Type[MarketDataProvider]] = {}

    @classmethod
    def register(cls, name: str):
        """Decorator to register a new provider."""
        def wrapper(provider_class: Type[MarketDataProvider]):
            if name in cls._providers:
                logger.warning(f"Overwriting existing provider registration for '{name}'")
            cls._providers[name] = provider_class
            logger.info(f"Registered provider: '{name}'")
            return provider_class
        return wrapper

    @classmethod
    def get_provider(cls, name: str, **kwargs) -> MarketDataProvider:
        """
        Instantiates and returns the requested provider.
        Raises ValueError if the provider is not registered.
        """
        if name not in cls._providers:
            raise ValueError(f"Provider '{name}' is not registered. Available providers: {list(cls._providers.keys())}")
        
        provider_class = cls._providers[name]
        return provider_class(**kwargs)
