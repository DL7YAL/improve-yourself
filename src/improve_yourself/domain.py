from __future__ import annotations

from collections import defaultdict

from .model import Kill, Multikill


def round_multikills(kills: list[Kill], minimum: int = 3) -> list[Multikill]:
    """Return exactly one marker per player and round."""
    grouped: dict[tuple[int, str], list[Kill]] = defaultdict(list)
    for kill in kills:
        if kill.attacker:
            grouped[(kill.round_number, kill.attacker)].append(kill)

    result: list[Multikill] = []
    for (round_number, player), group in grouped.items():
        ordered = sorted(group, key=lambda item: item.tick)
        if len(ordered) < minimum:
            continue
        result.append(
            Multikill(
                round_number=round_number,
                player=player,
                kill_count=len(ordered),
                first_tick=ordered[0].tick,
                last_tick=ordered[-1].tick,
                victims=[item.victim for item in ordered],
            )
        )
    return sorted(result, key=lambda item: (item.round_number, item.first_tick, item.player))
