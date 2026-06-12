import json
import os
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# --- Sub-models --- #
# These are nested objects inside the main profile
# Breaking them out makes the structure cleaner and easier to work with

class Schedule(BaseModel):
    """Everything about how the user actually spends their time"""
    wake_time: str = "07:00"                    # e.g. "07:00"
    sleep_time: str = "23:00"                   # e.g. "23:00"
    peak_focus_windows: list[str] = []          # e.g. ["09:00-11:00", "20:00-22:00"]
    known_dead_zones: list[str] = []            # e.g. ["14:00-15:00"] - low energy periods
    realistic_daily_hours: float = 1.0          # honest hours available for goal work
    avoidance_behaviours: list[str] = []        # what they do when procrastinating


class Goal(BaseModel):
    """The users 6 month goal and everything around it"""
    statement: str = ""                         # what they said they want to achieve
    real_why: str = ""                          # the deeper motivation behind the goal
    likelihood_score: float = 0.0              # 0.0 - 1.0, how likely they are to achieve it
    milestone_structure: list[str] = []         # broken down milestones
    risk_factors: list[str] = []               # what could derail them


class UserProfile(BaseModel):
    """
    The complete model of a Gravity user.
    Built during onboarding, refined over time.
    Every AI call in the system uses this as its core context.
    """

    # --- Identity ---
    name: str = ""
    personality_summary: str = ""              # 2-3 sentence AI-generated summary
    motivation_style: str = ""                 # intrinsic / extrinsic / mixed
    energy_pattern: str = ""                   # morning / evening / variable
    self_awareness_level: str = ""             # high / moderate / low
    failure_response: str = ""                 # catastrophise / rationalise / analyse
    feedback_preference: str = ""              # direct / factual / questioning / gentle

    # --- Schedule ---
    schedule: Schedule = Field(default_factory=Schedule)

    # --- Goal ---
    goal: Goal = Field(default_factory=Goal)

    # --- Non-negotiables ---
    # Things they want to do every single day no matter what
    # Capped at 5 - enforced at onboarding
    non_negotiables: list[str] = []

    # --- Cycle ---
    cycle_start: Optional[str] = None          # YYYY-MM-DD
    cycle_end: Optional[str] = None            # YYYY-MM-DD

    # --- Onboarding state ---
    # Tracks which phase of onboarding has been completed
    # So we can resume if interrupted
    onboarding_complete: bool = False
    onboarding_phase: int = 0                  # 0-5


def save_profile(profile: UserProfile, profiles_dir: str = "profiles") -> str:
    """
    Save a profile to disk as a JSON file.
    Returns the path it was saved to.
    Profiles are gitignored - they never get committed.
    """
    os.makedirs(profiles_dir, exist_ok=True)
    filename = f"{profile.name.lower().replace(' ', '_')}.json"
    filepath = os.path.join(profiles_dir, filename)

    with open(filepath, "w") as f:
        json.dump(profile.model_dump(), f, indent=2)

    return filepath


def load_profile(name: str, profiles_dir: str = "profiles") -> Optional[UserProfile]:
    """
    Load a profile from disk by name.
    Returns None if no profile exists for that name.
    """
    filename = f"{name.lower().replace(' ', '_')}.json"
    filepath = os.path.join(profiles_dir, filename)

    if not os.path.exists(filepath):
        return None

    with open(filepath, "r") as f:
        data = json.load(f)

    return UserProfile(**data)


# Test the profile system when run directly
if __name__ == "__main__":
    # Create a test profile
    profile = UserProfile(
        name="Michael",
        personality_summary="Self-driven, building-oriented, learns by doing.",
        motivation_style="intrinsic",
        energy_pattern="morning",
        feedback_preference="direct",
        non_negotiables=["exercise", "read 20 pages", "no phone before 9am"],
        cycle_start=str(date.today()),
        onboarding_phase=1
    )

    # Save it
    path = save_profile(profile)
    print(f"Profile saved to: {path}")

    # Load it back
    loaded = load_profile("Michael")
    print(f"Profile loaded: {loaded.name}")
    print(f"Non-negotiables: {loaded.non_negotiables}")
    print(f"Motivation style: {loaded.motivation_style}")
    print("Profile system working correctly.")
