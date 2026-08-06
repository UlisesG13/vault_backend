"""Enumeraciones del dominio."""
from enum import Enum


class Platform(str, Enum):
    gmail = "gmail"
    facebook = "facebook"
    twitter = "twitter"


class AccountStatus(str, Enum):
    active = "active"
    suspended = "suspended"
    banned = "banned"


class UserRole(str, Enum):
    admin = "admin"
    operator = "operator"
