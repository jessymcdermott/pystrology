"""Daily horoscope generation: real ephemeris-computed transits, interpreted into
prose by Claude. The astronomy (exact transiting positions and their aspects to
the natal chart) is computed by chart.py, not guessed by the model — Claude's
job here is interpretation and writing, not calculating planetary positions.

Results are cached one-per-nickname-per-day so repeat visits don't re-generate
(and re-bill) the same reading.
"""
import json
import os
from pathlib import Path

import anthropic

MODEL = "claude-opus-5"

PLANET_ORDER = [
    "Moon", "Sun", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
]

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "astrology" / "horoscopes"

HOROSCOPE_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
        "overall_energy": {"type": "string"},
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "planet": {"type": "string"},
                    "transit": {"type": "string"},
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["planet", "transit", "title", "body"],
                "additionalProperties": False,
            },
        },
        "watch_out": {"type": "string"},
        "best_for": {"type": "string"},
        "summary": {"type": "string"},
    },
    "required": ["headline", "overall_energy", "sections", "watch_out", "best_for", "summary"],
    "additionalProperties": False,
}


def _describe_natal(natal_planets):
    lines = []
    for name in PLANET_ORDER + ["North Node"]:
        p = natal_planets.get(name)
        if p:
            lines.append(f"- {name}: {p['sign']} {p['degree']}°, House {p.get('house', '?')}")
    return "\n".join(lines)


def _describe_transits(transiting_planets):
    lines = []
    for name in PLANET_ORDER + ["North Node"]:
        p = transiting_planets.get(name)
        if p:
            retro = " (retrograde)" if p.get("retrograde") else ""
            lines.append(f"- {name}: {p['sign']} {p['degree']}°{retro}, currently transiting natal House {p.get('house', '?')}")
    return "\n".join(lines)


def _describe_aspects(aspects_to_natal):
    if not aspects_to_natal:
        return "No major transiting aspects to natal planets within orb today."
    return "\n".join(
        f"- Transiting {a['planet_a']} {a['aspect']} natal {a['planet_b']} (orb {a['orb']}°)"
        for a in aspects_to_natal
    )


def build_prompt(nickname, natal, transits, house_system):
    asc = natal["houses"]["ascendant"]
    house_label = house_system.replace("_", " ").title()

    return f"""You are a serious, technically precise astrologer writing a daily horoscope for {nickname}.

NATAL CHART ({house_label} houses):
Ascendant: {asc['sign']} {asc['degree']}°
{_describe_natal(natal['planets'])}

TODAY'S TRANSITS:
{_describe_transits(transits['transiting_planets'])}

TRANSITING ASPECTS TO NATAL CHART:
{_describe_aspects(transits['aspects_to_natal'])}

INSTRUCTIONS:
1. Write one section for every planet listed under TODAY'S TRANSITS, in this exact order: Moon, Sun, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto. Always lead with Moon — it moves fastest and sets the day's emotional tone.
2. For each planet, name its current sign/degree and the most significant transiting aspect to a natal placement (cite the exact aspect and orb from the data above). If nothing is within orb, describe the natal house it's currently transiting and the longer-term theme that implies.
3. Every section must be specific to this chart — reference the actual natal placements and houses given above, not generic sun-sign platitudes.
4. Tone: educated, direct, like a knowledgeable friend who has studied astrology seriously. No mystical fluff, no vague reassurances ("you may feel some energy today"), no fortune-telling cliches.
5. "watch_out" is one honest, specific caution tied to this chart today. "best_for" is a specific, actionable use of today's energy — not generic advice.
6. "summary" pulls the day's themes into one cohesive paragraph, synthesizing the sections rather than repeating them.
"""


def generate_horoscope(nickname, natal, transits, house_system="whole_sign"):
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set — add it to your .env file to use the daily horoscope feature."
        )

    client = anthropic.Anthropic()
    prompt = build_prompt(nickname, natal, transits, house_system)

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        output_config={"format": {"type": "json_schema", "schema": HOROSCOPE_SCHEMA}},
        messages=[{"role": "user", "content": prompt}],
    )

    if response.stop_reason == "refusal":
        raise RuntimeError("The model declined to generate this horoscope.")

    text = next(block.text for block in response.content if block.type == "text")
    return json.loads(text)


def _cache_path(nickname, date_str):
    return CACHE_DIR / f"{nickname}_{date_str}.json"


def get_cached_horoscope(nickname, date_str):
    path = _cache_path(nickname, date_str)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def save_cached_horoscope(nickname, date_str, horoscope):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(nickname, date_str).write_text(json.dumps(horoscope, indent=2))
