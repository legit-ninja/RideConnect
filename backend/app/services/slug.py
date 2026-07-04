import random
import re
import secrets

BASE32 = "abcdefghijklmnopqrstuvwxyz234567"


def kebab_case(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "listing"


def random_suffix(length: int = 6) -> str:
    return "".join(secrets.choice(BASE32) for _ in range(length))


def generate_listing_slug(animal_name: str) -> str:
    return f"{kebab_case(animal_name)}-{random_suffix()}"
