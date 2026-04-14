"""Lost Person Behavior (LPB) statistical distance database.

Based on Robert Koester's "Lost Person Behavior" research. Distances are
in kilometers from the Initial Planning Point (IPP) at 25th, 50th, 75th,
and 95th percentile confidence levels.

Each profile includes:
- Statistical travel distances by percentile
- Typical travel behaviors (tendencies when lost)
- Terrain factors that affect movement

Note: Values are representative composites from published SAR statistics.
Actual operational decisions should reference the full Koester dataset.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DistanceRing:
    """Distance percentile ring in kilometers from IPP."""

    p25: float
    p50: float
    p75: float
    p95: float


@dataclass(frozen=True)
class SubjectProfile:
    """Statistical profile for a lost person category."""

    category: str
    label: str
    description: str
    distances: DistanceRing
    behaviors: list[str]
    terrain_notes: str


# --- Subject Profile Database ---
# Distances in km from IPP

PROFILES: dict[str, SubjectProfile] = {
    # Children
    "child_1_3": SubjectProfile(
        category="child_1_3",
        label="Child (1-3 years)",
        description="Toddlers and very young children",
        distances=DistanceRing(p25=0.2, p50=0.5, p75=1.0, p95=2.4),
        behaviors=[
            "Limited mobility, usually found close to IPP",
            "May seek shelter under bushes, logs, or other cover",
            "Often unresponsive to calls when frightened",
            "Attracted to water features",
            "May follow animal paths",
        ],
        terrain_notes="Cannot cross significant terrain barriers. Water is a major hazard.",
    ),
    "child_4_6": SubjectProfile(
        category="child_4_6",
        label="Child (4-6 years)",
        description="Preschool to early school age",
        distances=DistanceRing(p25=0.3, p50=0.8, p75=1.6, p95=3.6),
        behaviors=[
            "Will wander but stay on paths when available",
            "Seek shelter when tired or frightened",
            "May hide from searchers (especially strangers)",
            "Attracted to interesting features (water, animals)",
            "Poor sense of direction",
        ],
        terrain_notes="Limited by terrain obstacles. Unlikely to cross waterways.",
    ),
    "child_7_12": SubjectProfile(
        category="child_7_12",
        label="Child (7-12 years)",
        description="School age children",
        distances=DistanceRing(p25=0.5, p50=1.2, p75=2.8, p95=5.6),
        behaviors=[
            "More mobile and may travel significant distances",
            "May attempt to find own way back",
            "Will follow trails and roads",
            "Can cross moderate terrain",
            "More likely to respond to searchers",
        ],
        terrain_notes="Can navigate moderate terrain. Rivers and cliffs are barriers.",
    ),
    "child_13_15": SubjectProfile(
        category="child_13_15",
        label="Child (13-15 years)",
        description="Adolescents",
        distances=DistanceRing(p25=0.8, p50=2.0, p75=3.8, p95=8.0),
        behaviors=[
            "Travel patterns similar to adults",
            "May travel at night",
            "May intentionally avoid detection",
            "Often follow trails then leave them",
            "Goal-directed movement",
        ],
        terrain_notes="Capable of crossing most terrain. May take risks.",
    ),
    # Adults
    "adult": SubjectProfile(
        category="adult",
        label="Adult (general)",
        description="Healthy adult, various activities",
        distances=DistanceRing(p25=1.0, p50=2.4, p75=4.8, p95=11.2),
        behaviors=[
            "Goal-directed travel initially, then confusion",
            "Tend to follow paths of least resistance",
            "Travel downhill when disoriented",
            "Seek ridgelines for visibility",
            "May backtrack on their own trail",
        ],
        terrain_notes="Can traverse most terrain. Dense vegetation slows progress significantly.",
    ),
    "elderly": SubjectProfile(
        category="elderly",
        label="Elderly",
        description="Older adults (65+), may have mobility issues",
        distances=DistanceRing(p25=0.3, p50=0.8, p75=1.6, p95=4.0),
        behaviors=[
            "Limited mobility, often found close to IPP",
            "May become confused and sit down",
            "Hypothermia risk even in mild weather",
            "May not respond to calls",
            "Often found near trails or roads",
        ],
        terrain_notes="Limited by steep terrain and obstacles. Falls are a significant risk.",
    ),
    # Activity-based
    "hiker": SubjectProfile(
        category="hiker",
        label="Hiker",
        description="Day hiker or backpacker",
        distances=DistanceRing(p25=1.4, p50=3.2, p75=6.4, p95=14.4),
        behaviors=[
            "Tend to stay on trails initially",
            "Travel downhill when lost",
            "May follow drainage features",
            "Seek high ground for visibility",
            "Continue moving rather than staying put",
        ],
        terrain_notes="Comfortable on trails. Off-trail progress varies with vegetation density.",
    ),
    "hunter": SubjectProfile(
        category="hunter",
        label="Hunter",
        description="Hunter pursuing game",
        distances=DistanceRing(p25=1.0, p50=2.8, p75=5.6, p95=12.0),
        behaviors=[
            "Comfortable off-trail",
            "Often travel to ridgelines and game trails",
            "May track game away from planned route",
            "Usually well-equipped for weather",
            "More likely to shelter in place",
        ],
        terrain_notes="Experienced in off-trail travel. May be in dense vegetation.",
    ),
    "berry_picker": SubjectProfile(
        category="berry_picker",
        label="Berry picker / Gatherer",
        description="Person gathering berries, mushrooms, or plants",
        distances=DistanceRing(p25=0.4, p50=1.2, p75=2.4, p95=5.2),
        behaviors=[
            "Focus on ground/vegetation, lose track of direction",
            "Wander gradually away from known area",
            "Head downhill when lost",
            "May be poorly equipped",
            "Often in dense vegetation areas",
        ],
        terrain_notes="Usually in forested areas with dense undergrowth.",
    ),
    "fisher": SubjectProfile(
        category="fisher",
        label="Fisher / Angler",
        description="Person fishing in streams, rivers, or lakes",
        distances=DistanceRing(p25=0.4, p50=1.0, p75=2.0, p95=5.6),
        behaviors=[
            "Follow waterways upstream or downstream",
            "Found near water features",
            "May wade into dangerous water",
            "Drowning is a primary hazard",
            "Equipment can help identify route",
        ],
        terrain_notes="Concentrated along waterways. Water crossings are high risk.",
    ),
    "climber": SubjectProfile(
        category="climber",
        label="Climber",
        description="Rock or mountain climber",
        distances=DistanceRing(p25=0.6, p50=1.6, p75=3.2, p95=7.2),
        behaviors=[
            "Vertical as well as horizontal movement",
            "May be stranded on cliffs or ledges",
            "Route finding through technical terrain",
            "Equipment may mark route",
            "Injury from falls is common",
        ],
        terrain_notes="Found in technical terrain. Vertical rescue may be needed.",
    ),
    "skier": SubjectProfile(
        category="skier",
        label="Skier / Snowboarder",
        description="Cross-country or backcountry skier",
        distances=DistanceRing(p25=1.2, p50=2.8, p75=5.2, p95=12.8),
        behaviors=[
            "High mobility on snow",
            "Travel downhill when lost",
            "Tracks visible in snow",
            "Avalanche terrain is a hazard",
            "Hypothermia risk increases rapidly",
        ],
        terrain_notes=(
            "Snow covers obstacles. Avalanche terrain must be mapped and avoided by searchers."
        ),
    ),
    "runner": SubjectProfile(
        category="runner",
        label="Runner",
        description="Trail runner or jogger",
        distances=DistanceRing(p25=1.6, p50=3.6, p75=7.2, p95=16.0),
        behaviors=[
            "High mobility, covers ground quickly",
            "Usually on trails or roads",
            "May deviate from planned route",
            "Lightly equipped, exposure risk",
            "Medical emergency possible (cardiac, heat, dehydration)",
        ],
        terrain_notes=(
            "Usually stays on established trails. Medical conditions can immobilize quickly."
        ),
    ),
    # Behavioral categories
    "dementia": SubjectProfile(
        category="dementia",
        label="Dementia patient",
        description="Person with Alzheimer's or other dementia",
        distances=DistanceRing(p25=0.4, p50=1.2, p75=2.8, p95=6.4),
        behaviors=[
            "Travel in a straight line until stopped by a barrier",
            "Do not respond to search calls",
            "May be found in dense brush or concealed locations",
            "Often head toward former home or familiar place",
            "Travel on roads when available",
            "Active at night, may wander after dark",
        ],
        terrain_notes=(
            "Travel is linear until blocked. Dense vegetation and water are traps, not barriers."
        ),
    ),
    "despondent": SubjectProfile(
        category="despondent",
        label="Despondent / Suicidal",
        description="Person in mental health crisis",
        distances=DistanceRing(p25=0.2, p50=0.8, p75=2.0, p95=5.6),
        behaviors=[
            "Seek concealment and isolation",
            "Often found near vehicle or last known point",
            "May travel to locations with personal significance",
            "Dense brush, water features, and heights are significant",
            "Often travel short distances then stop",
        ],
        terrain_notes="Search water features, cliffs, and dense concealment areas thoroughly.",
    ),
}


def get_profile(category: str) -> SubjectProfile | None:
    """Look up a subject profile by category key."""
    return PROFILES.get(category)


def get_all_categories() -> list[dict]:
    """Return a list of all available category keys and labels."""
    return [{"category": p.category, "label": p.label} for p in PROFILES.values()]


def get_distance_rings_km(category: str) -> dict[str, float] | None:
    """Get distance rings in km for a category."""
    profile = PROFILES.get(category)
    if profile is None:
        return None
    return {
        "p25": profile.distances.p25,
        "p50": profile.distances.p50,
        "p75": profile.distances.p75,
        "p95": profile.distances.p95,
    }
