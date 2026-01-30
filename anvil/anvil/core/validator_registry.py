"""
Validator Registry for managing and discovering validators.

This module provides a centralized registry for all validators, supporting
registration, discovery, and filtering of validators by language and configuration.
"""

from dataclasses import dataclass
from typing import Dict, List

from anvil.models.validator import Validator


@dataclass
class ValidatorMetadata:
    """
    Metadata about a registered validator.

    Attributes:
        name: Unique name of the validator
        language: Programming language the validator supports
        description: Human-readable description of what the validator does
    """

    name: str
    language: str
    description: str


class ValidatorRegistry:
    """
    Registry for managing and discovering validators.

    The registry maintains a collection of validators organized by language,
    supporting registration, retrieval, filtering, and metadata queries.
    Validators are stored in a deterministic order (alphabetically by name)
    for consistent behavior.

    Examples:
        >>> registry = ValidatorRegistry()
        >>> registry.register(my_validator)
        >>> validators = registry.get_validators_by_language("python")
        >>> if registry.is_available("flake8"):
        ...     flake8 = registry.get_validator("flake8")
    """

    def __init__(self):
        """Initialize an empty validator registry."""
        # Maps validator name -> validator instance
        self._validators: Dict[str, Validator] = {}
        # Maps language -> list of validator names (for efficient lookup)
        self._by_language: Dict[str, List[str]] = {}

    def register(self, validator: Validator) -> None:
        """
        Register a validator in the registry.

        Args:
            validator: The validator instance to register

        Raises:
            ValueError: If validator name is empty, language is empty,
                       or a validator with the same name already exists
        """
        # Validate inputs
        if not validator.name:
            raise ValueError("Validator name cannot be empty")
        if not validator.language:
            raise ValueError("Validator language cannot be empty")

        # Check for duplicates
        if validator.name in self._validators:
            raise ValueError(
                f"Validator '{validator.name}' is already registered for "
                f"language '{self._validators[validator.name].language}'"
            )

        # Register the validator
        self._validators[validator.name] = validator

        # Add to language index
        language = validator.language
        if language not in self._by_language:
            self._by_language[language] = []
        self._by_language[language].append(validator.name)

        # Keep language lists sorted for deterministic ordering
        self._by_language[language].sort()

    def unregister(self, name: str) -> None:
        """
        Unregister a validator from the registry.

        Args:
            name: Name of the validator to unregister

        Raises:
            KeyError: If no validator with the given name is found
        """
        if name not in self._validators:
            raise KeyError(f"Validator '{name}' not found in registry")

        validator = self._validators[name]
        language = validator.language

        # Remove from main dict
        del self._validators[name]

        # Remove from language index
        if language in self._by_language:
            self._by_language[language].remove(name)
            # Clean up empty language lists
            if not self._by_language[language]:
                del self._by_language[language]

    def get_validator(self, name: str) -> Validator:
        """
        Get a specific validator by name.

        Args:
            name: Name of the validator to retrieve

        Returns:
            The validator instance

        Raises:
            KeyError: If no validator with the given name is found
        """
        if name not in self._validators:
            raise KeyError(f"Validator '{name}' not found in registry")
        return self._validators[name]

    def get_validators_by_language(self, language: str) -> List[Validator]:
        """
        Get all validators for a specific language.

        Validators are returned in alphabetical order by name for
        deterministic behavior.

        Args:
            language: Programming language to filter by

        Returns:
            List of validators for the specified language (empty if none found)
        """
        if language not in self._by_language:
            return []

        # Return validators in sorted order (already sorted in _by_language)
        return [self._validators[name] for name in self._by_language[language]]

    def is_available(self, name: str) -> bool:
        """
        Check if a validator is available in the registry.

        Args:
            name: Name of the validator to check

        Returns:
            True if the validator is registered, False otherwise
        """
        return name in self._validators

    def list_all(self) -> List[Validator]:
        """
        List all registered validators.

        Validators are returned in alphabetical order by name for
        deterministic behavior.

        Returns:
            List of all registered validators (empty if none registered)
        """
        # Sort by name for deterministic ordering
        sorted_names = sorted(self._validators.keys())
        return [self._validators[name] for name in sorted_names]

    def get_metadata(self, name: str) -> ValidatorMetadata:
        """
        Get metadata for a specific validator.

        Args:
            name: Name of the validator

        Returns:
            Metadata for the validator

        Raises:
            KeyError: If no validator with the given name is found
        """
        validator = self.get_validator(name)  # Raises KeyError if not found
        return ValidatorMetadata(
            name=validator.name,
            language=validator.language,
            description=validator.description,
        )

    def list_all_metadata(self) -> List[ValidatorMetadata]:
        """
        List metadata for all registered validators.

        Returns:
            List of metadata for all validators (empty if none registered)
        """
        return [
            ValidatorMetadata(
                name=validator.name,
                language=validator.language,
                description=validator.description,
            )
            for validator in self.list_all()
        ]

    def filter_by_names(self, names: List[str]) -> List[Validator]:
        """
        Filter validators by a list of names.

        This is useful for filtering based on configuration (e.g., only
        enabled validators). Validators are returned in alphabetical order.

        Args:
            names: List of validator names to include

        Returns:
            List of validators matching the given names (excludes non-existent ones)
        """
        # Only include validators that exist, maintain sorted order
        result = []
        for name in sorted(names):
            if name in self._validators:
                result.append(self._validators[name])
        return result

    def clear(self) -> None:
        """
        Clear all validators from the registry.

        This is primarily useful for testing or resetting the registry state.
        """
        self._validators.clear()
        self._by_language.clear()
