from dataclasses import dataclass
from uuid import NAMESPACE_DNS, UUID, uuid5

from faker import Faker


@dataclass
class User:
    id: UUID
    external_id: str
    name: str


def get_fake_users(seed: int = 123, size: int = 100) -> list[User]:
    """Generate a list of fake users."""

    fake = Faker()
    fake.seed_instance(seed)

    users = []
    for _ in range(size):
        external_id = fake.uuid4()
        name = fake.name()
        # Create unique ID based on external_id and name
        combined_string = f"{external_id}:{name}"
        unique_id = uuid5(NAMESPACE_DNS, combined_string)

        users.append(
            User(
                id=unique_id,
                external_id=external_id,
                name=name,
            )
        )
    return users
