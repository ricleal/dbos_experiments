"""
Data models and generation utilities for the ELT pipeline.

This module provides:
- Data classes for User and ConnectedIntegration
- Fake data generation using Faker
- Stable UUID generation based on external IDs
"""

from dataclasses import dataclass
from typing import List
from uuid import NAMESPACE_DNS, UUID, uuid5

from faker import Faker

# ============================================================================
# Data Models
# ============================================================================


@dataclass
class ConnectedIntegration:
    """Represents a connected integration for an organization."""

    id: UUID
    organization_id: str
    provider: str
    provider_data: dict  # Contains permission_source_name and other info


@dataclass
class User:
    """Represents a user from an external API."""

    id: UUID  # Internal stable UUID
    external_id: str  # External system ID
    organization_id: str
    connected_integration_id: UUID
    name: str
    email: str


@dataclass
class ExtendedUser:
    """User with additional database fields."""

    id: UUID
    workflow_id: str
    external_id: str
    organization_id: str
    connected_integration_id: UUID
    name: str
    email: str
    created_at: str


# ============================================================================
# Data Generation Functions
# ============================================================================


def generate_fake_users(
    organization_id: str,
    connected_integration_id: UUID,
    seed: int,
    size: int = 10,
) -> List[User]:
    """Generate a list of fake users for a specific org/integration.

    Uses Faker to generate realistic user data. The internal UUID is stable
    based on the external_id using UUID5.

    Args:
        organization_id: The organization ID
        connected_integration_id: The connected integration ID
        seed: Random seed for reproducibility
        size: Number of users to generate

    Returns:
        List of User objects
    """
    fake = Faker()
    fake.seed_instance(seed)

    users = []
    for _ in range(size):
        external_id = fake.uuid4()
        name = fake.name()
        email = fake.email()

        # Create stable internal UUID based on external_id
        internal_id = uuid5(NAMESPACE_DNS, external_id)

        users.append(
            User(
                id=internal_id,
                external_id=external_id,
                organization_id=organization_id,
                connected_integration_id=connected_integration_id,
                name=name,
                email=email,
            )
        )

    return users
