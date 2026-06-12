import os
import json
from datetime import date, timedelta
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint
from core.ai_client import AIClient
from core.profile import UserProfile, Schedule, Goal, save_profile, load_profile

console = Console()
client = AIClient()

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def load_prompt(filename: str) -> str:
    """Load a prompt file from core/prompts/"""
    path = os.path.join("core", "prompts", filename)
    with open(path, "r") as f:
        return f.read()


def build_context_summary(profile: UserProfile) -> str:
    """
    Build a short plain-English summary of what we know about
    the user so far. Injected into later phase system prompts
    so the AI remembers earlier parts of the conversation.
    This is what makes the conversation feel continuous rather
    than starting fresh each phase.
    """
    lines = [f"User name: {profile.name}"]

    if profile.personality_summary:
        lines.append(f"Personality: {profile.personality_summary}")
    if profile.energy_pattern:
        lines.append(f"Energy pattern: {profile.energy_pattern}")
    if profile.motivation_style:
        lines.append(f"Motivation style: {profile.motivation_style}")
    if profile.schedule.wake_time != "07:00":
        lines.append(f"Wake time: {profile.schedule.wake_time}")
    if profile.schedule.realistic_daily_hours != 1.0:
        lines.append(f"Realistic daily hours available: {profile.schedule.realistic_daily_hours}")
    if profile.schedule.avoidance_behaviours:
        lines.append(f"Avoidance behaviours: {', '.join(profile.schedule.avoidance_behaviours)}")
    if profile.goal.statement:
        lines.append(f"Goal: {profile.goal.statement}")
    if profile.goal.real_why:
        lines.append(f"Real why: {profile.goal.real_why}")

    return "\n".join(lines)


def extract_profile_data(transcript: list[dict], profile: UserProfile) -> dict:
    """
    Silent extraction call — completely separate from the visible conversation.
    Takes the full conversation transcript from all phases so far,
    sends it to the AI with the extraction prompt, gets back clean JSON.
    The user never sees this. It runs silently after each phase.
    
    This separation is the key design decision:
    - The conversation AI focuses entirely on being a good interviewer
    - The extraction AI focuses entirely on pulling structured data
    - They never interfere with each other
    """
    system_prompt = load_prompt("extract_profile.txt")
    
    # Format the transcript into a readable string for extraction
    transcript_text = ""
    for turn in transcript:
        role = "Gravity" if turn["role"] == "assistant" else profile.name
        transcript_text += f"{role}: {turn['content']}\n\n"
    
    extraction_messages = [{
        "role": "user",
        "content": f"Extract structured profile data from this onboarding conversation:\n\n{transcript_text}"
    }]
    
    response = client.complete(system_prompt, extraction_messages, max_tokens=1000)
    
    # Parse the JSON response
    try:
        # Strip any accidental markdown fences if the model adds them
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        return json.loads(clean.strip())
    except json.JSONDecodeError:
        # If extraction fails, return empty dict — profile keeps what it has
        console.print("[dim red]Note: extraction parse failed, continuing with partial data[/dim red]")
        return {}


def apply_extracted_data(profile: UserProfile, data: dict) -> UserProfile:
    """
    Write extracted JSON data into the correct profile fields.
    Uses .get() everywhere so missing fields never crash anything.
    """
    if not data:
        return profile

    # Identity fields
    if data.get("personality_summary"):
        profile.personality_summary = data["personality_summary"]
    if data.get("motivation_style"):
        profile.motivation_style = data["motivation_style"]
    if data.get("energy_pattern"):
        profile.energy_pattern = data["energy_pattern"]
    if data.get("self_awareness_level"):
        profile.self_awareness_level = data["self_awareness_level"]
    if data.get("failure_response"):
        profile.failure_response = data["failure_response"]
    if data.get("feedback_preference"):
        profile.feedback_preference = data["feedback_preference"]

    # Schedule
    schedule_data = data.get("schedule", {})
    if schedule_data.get("wake_time"):
        profile.schedule.wake_time = schedule_data["wake_time"]
    if schedule_data.get("sleep_time"):
        profile.schedule.sleep_time = schedule_data["sleep_time"]
    if schedule_data.get("peak_focus_windows"):
        profile.schedule.peak_focus_windows = schedule_data["peak_focus_windows"]
    if schedule_data.get("known_dead_zones"):
        profile.schedule.known_dead_zones = schedule_data["known_dead_zones"]
    if schedule_data.get("realistic_daily_hours"):
        profile.schedule.realistic_daily_hours = schedule_data["realistic_daily_hours"]
    if schedule_data.get("avoidance_behaviours"):
        profile.schedule.avoidance_behaviours = schedule_data["avoidance_behaviours"]

    # Goal
    goal_data = data.get("goal", {})
    if goal_data.get("statement"):
        profile.goal.statement = goal_data["statement"]
    if goal_data.get("real_why"):
        profile.goal.real_why = goal_data["real_why"]
    if goal_data.get("likelihood_score") is not None:
        profile.goal.likelihood_score = goal_data["likelihood_score"]
    if goal_data.get("milestone_structure"):
        profile.goal.milestone_structure = goal_data["milestone_structure"]
    if goal_data.get("risk_factors"):
        profile.goal.risk_factors = goal_data["risk_factors"]

    # Non-negotiables — cap at 5
    if data.get("non_negotiables"):
        profile.non_negotiables = data["non_negotiables"][:5]

    return profile


# ─────────────────────────────────────────────
# PHASE RUNNER
# ─────────────────────────────────────────────

def run_phase(
    phase: int,
    phase_file: str,
    profile: UserProfile,
    full_transcript: list[dict]
) -> list[dict]:
    """
    Run a single onboarding phase.
    
    How it works:
    1. Load the system prompt for this phase
    2. Inject what we already know about the user as context
    3. Get the AI opening message (no user trigger needed)
    4. Loop: display AI message -> get user input -> send to AI -> repeat
    5. Stop when AI outputs PHASE_COMPLETE
    6. Return the updated full transcript
    
    The full_transcript carries across all phases — so by Phase 3,
    the AI has context from Phases 1 and 2 if needed.
    Voice-ready: every AI response is plain text, no symbols.
    """
    phase_names = {
        1: "Who Are You",
        2: "Your Routine",
        3: "Your Goal",
        4: "Non-Negotiables",
        5: "Feedback Style"
    }

    # Load and augment the system prompt with what we know so far
    system_prompt = load_prompt(phase_file)
    context_summary = build_context_summary(profile)
    if context_summary:
        system_prompt += f"\n\nWhat you already know about this user:\n{context_summary}"

    console.print()
    console.print(f"[dim]— Phase {phase} of 5: {phase_names[phase]} —[/dim]")
    console.print()

    # Phase-local message history for this phase's conversation
    phase_messages = []

    # Get the opening message from the AI
    # We send a minimal system message so the AI produces its opening line
    # No "begin" hack — the AI just produces its first message naturally
    opening_response = client.complete(
        system_prompt,
        [{"role": "user", "content": "[start]"}],
        max_tokens=150
    )

    # Clean PHASE_COMPLETE marker if it appears in opening (shouldn't, but safety)
    opening_clean = opening_response.replace("PHASE_COMPLETE", "").strip()

    # Display and record
    console.print(Text(f"Gravity  {opening_clean}", style="white"))
    console.print()

    phase_messages.append({"role": "user", "content": "[start]"})
    phase_messages.append({"role": "assistant", "content": opening_response})
    full_transcript.append({"role": "assistant", "content": opening_clean})

    # Main conversation loop
    while True:
        try:
            user_input = console.input("[dim]You   [/dim]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Session interrupted. Progress saved.[/dim]")
            break

        if not user_input:
            continue

        # Add to both phase history and full transcript
        phase_messages.append({"role": "user", "content": user_input})
        full_transcript.append({"role": "user", "content": user_input})

        # Get AI response
        response = client.complete(system_prompt, phase_messages, max_tokens=200)

        # Check for phase completion signal
        phase_done = "PHASE_COMPLETE" in response

        # Clean the response before showing — remove the marker
        response_clean = response.replace("PHASE_COMPLETE", "").strip()

        # Display the response
        if response_clean:
            console.print()
            console.print(Text(f"Gravity  {response_clean}", style="white"))
            console.print()

        # Record to histories
        phase_messages.append({"role": "assistant", "content": response})
        full_transcript.append({"role": "assistant", "content": response_clean})

        if phase_done:
            break

    return full_transcript


# ─────────────────────────────────────────────
# MAIN ONBOARDING FLOW
# ─────────────────────────────────────────────

PHASES = [
    (1, "phase1_identity.txt"),
    (2, "phase2_routine.txt"),
    (3, "phase3_goal.txt"),
    (4, "phase4_nonneg.txt"),
    (5, "phase5_feedback.txt"),
]


def run_onboarding(resume_name: str = None) -> UserProfile:
    """
    Run the full 5-phase onboarding conversation.
    
    resume_name: if provided, loads existing profile and resumes
    from the last completed phase. Means interrupted sessions
    are never lost.
    """
    console.clear()
    console.print()
    console.print(Panel(
        Text("GRAVITY", justify="center", style="bold white"),
        style="white",
        expand=False
    ))
    console.print()

    # Resume or start fresh
    if resume_name:
        profile = load_profile(resume_name)
        if profile:
            console.print(f"[dim]Resuming session for {profile.name}...[/dim]")
            console.print()
        else:
            resume_name = None

    if not resume_name:
        console.print("[dim]This takes about 15 minutes. Answer honestly.[/dim]")
        console.print("[dim]The more real your answers, the better this works.[/dim]")
        console.print()
        name = console.input("What is your name?  ").strip()
        console.print()

        profile = UserProfile(
            name=name,
            cycle_start=str(date.today()),
            cycle_end=str(date.today() + timedelta(days=182)),
            onboarding_phase=0,
            onboarding_complete=False
        )
        save_profile(profile)

    # Full conversation transcript — carries across all phases
    # This is what gets sent to the silent extraction call
    # Also what will feed voice replay in future
    full_transcript = []

    # Run each phase, skipping ones already completed
    for phase_num, phase_file in PHASES:
        if profile.onboarding_phase >= phase_num:
            console.print(f"[dim]Phase {phase_num} already complete, skipping.[/dim]")
            continue

        full_transcript = run_phase(phase_num, phase_file, profile, full_transcript)

        # Silent extraction after each phase
        # The user sees nothing — this runs and updates the profile quietly
        console.print("[dim]...[/dim]")
        extracted = extract_profile_data(full_transcript, profile)
        profile = apply_extracted_data(profile, extracted)
        profile.onboarding_phase = phase_num

        # Save after every phase — progress never lost
        save_profile(profile)

    # Mark complete
    profile.onboarding_complete = True
    save_profile(profile)

    console.print()
    console.print(Panel(
        f"[bold white]Setup complete.[/bold white]\n\n"
        f"Goal: {profile.goal.statement}\n"
        f"Likelihood: {int(profile.goal.likelihood_score * 100)}%\n"
        f"Non-negotiables: {len(profile.non_negotiables)}\n"
        f"Cycle ends: {profile.cycle_end}",
        style="white",
        expand=False
    ))

    return profile


if __name__ == "__main__":
    import sys
    resume = sys.argv[1] if len(sys.argv) > 1 else None
    run_onboarding(resume_name=resume)
