"""Domain Enums for Users, Projects, Milestones, and Tickets."""

from enum import Enum


class UserRole(str, Enum):
    CLIENT = "CLIENT"
    ADMIN = "ADMIN"


class ProjectStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


class MilestoneStatus(str, Enum):
    LOCKED = "LOCKED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    APPROVED = "APPROVED"


class TicketType(str, Enum):
    BUG = "BUG"
    REVISION = "REVISION"
    QUESTION = "QUESTION"


class TicketStatus(str, Enum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
