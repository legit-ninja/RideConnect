import enum


class RiderSkillLevel(int, enum.Enum):
    BEGINNER = 1
    ADVANCED_BEGINNER = 2
    INTERMEDIATE = 3
    ADVANCED_INTERMEDIATE = 4
    PROFESSIONAL = 5

    @classmethod
    def label(cls, level: int | None) -> str | None:
        if level is None:
            return None
        try:
            member = cls(level)
        except ValueError:
            return None
        names = {
            cls.BEGINNER: "Beginner",
            cls.ADVANCED_BEGINNER: "Advanced Beginner",
            cls.INTERMEDIATE: "Intermediate",
            cls.ADVANCED_INTERMEDIATE: "Advanced Intermediate",
            cls.PROFESSIONAL: "Professional",
        }
        return names[member]

    @classmethod
    def self_reported_label(cls, level: int | None) -> str | None:
        label = cls.label(level)
        if label is None:
            return None
        return f"Self-reported: {label}"

    @classmethod
    def minimum_label(cls, level: int | None) -> str | None:
        label = cls.label(level)
        if label is None:
            return None
        return f"{label} riders and up"

    @classmethod
    def meets_minimum(cls, rider_level: int | None, min_level: int | None) -> bool:
        if min_level is None or rider_level is None:
            return True
        return rider_level >= min_level
