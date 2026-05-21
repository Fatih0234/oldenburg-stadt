import re
from dataclasses import dataclass


EXPLICIT_BIKE_KEYWORDS = [
    r"radwe[gh]\w*",
    r"fahrradwe[gh]\w*",
    r"radspur\w*",
    r"radstreifen\w*",
    r"fahrradstraße\w*",
    r"radschutzstreifen\w*",
    r"schutzstreifen\w*",
    r"radroute\w*",
    r"fahrradroute\w*",
    r"radverkehr\w*",
    r"rad-?\s*und\s*-?gehweg\w*",
    r"geh-?\s*und\s*-?radweg\w*",
    r"rad/gehweg\w*",
    r"rad-?\s*und\s*-?fußweg\w*",
    r"fuß-?\s*und\s*-?radweg\w*",
    r"rad-?\s*und\s*-?wanderweg\w*",
    r"wander-?\s*und\s*-?radweg\w*",
    r"radüberweg\w*",
    r"fahrradständer\w*",
    r"anlehnbügel\w*",
    r"fahrradbügel\w*",
    r"radständer\w*",
    r"lastenrad\w*",
    r"radler\w*",
    r"radfahrer\w*",
    r"radlerin\w*",
    r"radfahrende\w*",
    r"\w*fahrrad\w*",
    r"\w*fahrr[aä]der\w*",
    r"\w*damenrad\w*",
    r"\w*herrenrad\w*",
    r"\w*lastenrad\w*",
    r"\bbike\b",
    r"\bbikes\b",
]

SOFT_BIKE_KEYWORDS = [
    r"\bschulweg\w*",
    r"\bschüler\w*",
    r"\brad\b",
    r"\bräder\b",
]

STRONG_NEG_KEYWORDS = [
    r"\bspielplatz\w*",
    r"\bspielgerät\w*",
    r"\bschaukel\w*",
    r"\brutsche\w*",
    r"\bsandkiste\w*",
    r"\bschulhof\w*",
    r"\bkleidercontainer\w*",
    r"\btextilcontainer\w*",
    r"\baltkleider\w*",
    r"\bhundekot\w*",
    r"\bhundehaufen\w*",
    r"\bhund\b",
    r"\bhunde\b",
    r"\bkatze\w*",
    r"\bkatzen\w*",
    r"\bglascontainer\w*",
    r"\baltglascontainer\w*",
    r"\bplakat\w*",
    r"\bgraffiti\w*",
    r"\baufkleber\w*",
    r"\bsticker\w*",
    r"\bparkanlage\w*",
    r"\bwaldstück\w*",
    r"\bwohnwagen\w*",
    r"\bmercedes\w*",
    r"\baudi\b",
    r"\bpkw\b",
    r"\bauto\b",
    r"\bparkplatz\w*",
    r"\bparkbucht\w*",
    r"\bparkstreifen\w*",
    r"\bmittelstreifen\w*",
    r"\bprivat\w*",
    r"\bgrundstück\w*",
    r"\bgarage\w*",
]

GENERIC_SURFACE_HAZARDS = [
    r"schlagloch\w*",
    r"schlaglöcher\w*",
    r"\bloch\b",
    r"\blöcher\b",
    r"uneben\w*",
    r"abgesackt\w*",
    r"absackung\w*",
    r"absenkung\w*",
    r"kante\w*",
    r"absatz\w*",
    r"bodenwelle\w*",
    r"pflasterstein\w*",
    r"pflastersteine\w*",
    r"gepflastert\w*",
    r"kopfsteinpflaster\w*",
    r"\bstein(e|en)?\s+(der\s+)?(fehlt|fehlen)\b",
    r"\bfehlende?\s+steine?\b",
    r"risse\w*",
    r"\briss\b",
    r"asphalt\w*",
    r"fahrbahn\w*",
    r"fahrbahnbelag\w*",
    r"straßenbelag\w*",
    r"aufriss\w*",
    r"aufgerissen\w*",
    r"schlaglos\w*",
    r"schl[aä]glöcher\w*",
    r"mangelhaft\w*",
    r"seitenstreifen\w*",
    r"reifenspur\w*",
    r"verschmutz\w*",
    r"aufbruch\w*",
    r"aufgebrochen\w*",
    r"hügel\w*",
    r"gull[yi]\w*",
    r"gullideckel\w*",
    r"regenwasser\w*",
    r"wasser\s+läuft\s+nicht\s+ab",
    r"läuft\s+nicht\s+ab",
    r"pfütze\w*",
    r"überflut\w*",
    r"nicht\s+begehbar",
    r"nicht\s+befahrbar",
    r"nicht\s+passierbar",
    r"marode\w*",
    r"beschädigt\w*",
    r"schad\w*",
    r"kaputt\w*",
    r"defekt\w*",
    r"sturzgefahr\w*",
    r"rutschgefahr\w*",
    r"unfallgefahr\w*",
    r"gefahrenstelle\w*",
]

CONTEXT_HAZARDS = [
    r"scherben\w*",
    r"glasscherben\w*",
    r"\bglas\b",
    r"hecke\w*",
    r"sträucher\w*",
    r"äste\b",
    r"zweige\b",
    r"überhang\w*",
    r"überhängend\w*",
    r"bewuchs\w*",
    r"zugewachsen\w*",
    r"zuparken\w*",
    r"zugeparkt\w*",
    r"blockiert\w*",
    r"versperrt\w*",
    r"hindernis\w*",
    r"poller\w*",
    r"pfosten\w*",
    r"sperrpfosten\w*",
    r"sperrpoller\w*",
    r"absperrpf[aä]hl\w*",
    r"sperrbalken\w*",
    r"absperrung\w*",
    r"blöcke\w*",
    r"\bblock\b",
    r"ampel\w*",
    r"ampelschaltung\w*",
    r"induktionsschleife\w*",
    r"sensor\w*",
    r"beleuchtung\w*",
    r"verdeckt\w*",
    r"schild\w*",
    r"beschilderung\w*",
    r"wegweiser\w*",
    r"\bvz\b",
    r"verkehrszeichen\w*",
    r"sicht\w*",
    r"kurve\w*",
    r"baum\s+liegt\s+quer",
    r"baum\w*",
    r"liegt\s+quer",
]

LOCATION_CONTEXT = [
    r"radwe[gh]\w*",
    r"fahrradwe[gh]\w*",
    r"radspur\w*",
    r"radstreifen\w*",
    r"fahrradstraße\w*",
    r"geh-?\s*und\s*-?radweg\w*",
    r"rad-?\s*und\s*-?gehweg\w*",
    r"kreuzung\w*",
    r"einmündung\w*",
    r"einfahrt\w*",
    r"querung\w*",
    r"überquer\w*",
    r"übergang\w*",
    r"verbindungsweg\w*",
    r"verkehrsinsel\w*",
    r"straße\w*",
    r"fahrbahn\w*",
    r"seitenstreifen\w*",
    r"\bweg\b",
    r"gehweg\w*",
    r"fußweg\w*",
    r"bürgersteig\w*",
    r"rinnstein\w*",
    r"wegesbreite\w*",
    r"tunnel\w*",
    r"unterführung\w*",
    r"brücke\w*",
]

WASTE_CONTEXT = [
    r"\bmüll\b",
    r"\babfall\b",
    r"sperrmüll\w*",
    r"unrat\w*",
    r"schutt\w*",
    r"renovierungsschutt\w*",
    r"bau-?\s*und\s+renov",
    r"bauschutt\w*",
    r"einkaufswagen\w*",
    r"weihnachtsb[aä]um\w*",
    r"spülbecken\w*",
    r"sessel\w*",
    r"farbeimer\w*",
    r"schrottfahrr[aä]der\w*",
    r"scherben\w*",
    r"glasscherben\w*",
    r"\bglas\b",
]

OBSTRUCTION_CONTEXT = [
    r"blockiert\w*",
    r"versperrt\w*",
    r"hindernis\w*",
    r"liegen",
    r"liegt",
    r"im\s+weg",
    r"nicht\s+passierbar",
    r"nicht\s+befahrbar",
    r"kein\s+durchkommen",
]

EXPLICIT_BIKE_RE = re.compile("|".join(EXPLICIT_BIKE_KEYWORDS), re.IGNORECASE)
SOFT_BIKE_RE = re.compile("|".join(SOFT_BIKE_KEYWORDS), re.IGNORECASE)
STRONG_NEG_RE = re.compile("|".join(STRONG_NEG_KEYWORDS), re.IGNORECASE)
GENERIC_SURFACE_RE = re.compile("|".join(GENERIC_SURFACE_HAZARDS), re.IGNORECASE)
CONTEXT_HAZARD_RE = re.compile("|".join(CONTEXT_HAZARDS), re.IGNORECASE)
LOCATION_CONTEXT_RE = re.compile("|".join(LOCATION_CONTEXT), re.IGNORECASE)
WASTE_CONTEXT_RE = re.compile("|".join(WASTE_CONTEXT), re.IGNORECASE)
OBSTRUCTION_CONTEXT_RE = re.compile("|".join(OBSTRUCTION_CONTEXT), re.IGNORECASE)


@dataclass(frozen=True)
class RuleDecision:
    is_cycling_related: bool
    is_regex_candidate: bool
    route: str
    directness: str
    subcategory: str
    confidence: float
    needs_llm_review: bool
    reason_de: str
    matches: dict[str, list[str]]


def _matches(patterns, text):
    return [pat for pat in patterns if re.search(pat, text, re.IGNORECASE)]


def _decision(
    is_cycling_related,
    is_regex_candidate,
    route,
    directness,
    subcategory,
    confidence,
    needs_llm_review,
    reason_de,
    text_lower,
):
    return RuleDecision(
        is_cycling_related=is_cycling_related,
        is_regex_candidate=is_regex_candidate,
        route=route,
        directness=directness,
        subcategory=subcategory,
        confidence=confidence,
        needs_llm_review=needs_llm_review,
        reason_de=reason_de,
        matches={
            "bike": _matches(EXPLICIT_BIKE_KEYWORDS + SOFT_BIKE_KEYWORDS, text_lower),
            "neg": _matches(STRONG_NEG_KEYWORDS, text_lower),
            "surface": _matches(GENERIC_SURFACE_HAZARDS, text_lower),
            "hazard": _matches(CONTEXT_HAZARDS, text_lower),
            "location": _matches(LOCATION_CONTEXT, text_lower),
        },
    )


def classify_report_rules(text, category_id):
    text_lower = (text or "").lower()
    has_explicit_bike = bool(EXPLICIT_BIKE_RE.search(text_lower))
    has_soft_bike = bool(SOFT_BIKE_RE.search(text_lower))
    has_strong_neg = bool(STRONG_NEG_RE.search(text_lower))
    has_surface_hazard = bool(GENERIC_SURFACE_RE.search(text_lower))
    has_context_hazard = bool(CONTEXT_HAZARD_RE.search(text_lower))
    has_location_context = bool(LOCATION_CONTEXT_RE.search(text_lower))
    has_obstruction = bool(OBSTRUCTION_CONTEXT_RE.search(text_lower))

    if category_id == 7:
        has_bike_object = has_explicit_bike or re.search(r"\b(scooter|roller|laufrad|moped)\w*", text_lower)
        has_vehicle_or_trash = re.search(
            r"\b(auto|pkw|fahrzeug|mercedes|audi|wohnwagen|müll|abfall|sperrmüll|möbel|einkaufswagen)\w*",
            text_lower,
        )
        if has_vehicle_or_trash and not has_bike_object:
            return _decision(
                False,
                False,
                "auto_fail",
                "unrelated",
                "unrelated",
                0.9,
                False,
                "Automatisch ausgeschlossen: Fundmeldung ohne Fahrradbezug.",
                text_lower,
            )
        if has_bike_object:
            direct = "direct" if has_obstruction else "indirect"
            return _decision(
                True,
                True,
                "auto_pass",
                direct,
                "bike_parking",
                0.86 if has_obstruction else 0.78,
                not has_obstruction,
                "Automatisch als fahrradbezogen erkannt: Fundrad oder Fahrradobjekt.",
                text_lower,
            )

    if has_explicit_bike:
        return _decision(
            True,
            True,
            "auto_pass",
            "direct",
            _subcategory_for_context(text_lower, category_id),
            0.9,
            False,
            "Automatisch als fahrradbezogen erkannt: expliziter Fahrradbezug im Text.",
            text_lower,
        )

    if category_id == 3 and has_surface_hazard:
        if has_location_context and not has_strong_neg:
            return _decision(
                False,
                True,
                "llm_review",
                "nearby_only",
                "unrelated",
                0.45,
                True,
                "LLM-Prüfung empfohlen: Straßenschaden ohne eindeutigen Fahrradflächenbezug.",
                text_lower,
            )
        return _decision(
            False,
            True,
            "llm_review",
            "nearby_only",
            "unrelated",
            0.35,
            True,
            "LLM-Prüfung empfohlen: generischer Oberflächenschaden ohne Ortskontext.",
            text_lower,
        )

    if category_id == 3 and has_location_context and not has_strong_neg:
        return _decision(
            False,
            True,
            "llm_review",
            "nearby_only",
            "unrelated",
            0.4,
            True,
            "LLM-Prüfung empfohlen: Straßen- oder Wegekontext ohne eindeutigen Fahrradbezug.",
            text_lower,
        )

    if category_id == 3 and has_context_hazard:
        return _decision(
            False,
            True,
            "llm_review",
            "nearby_only",
            "unrelated",
            0.42,
            True,
            "LLM-Prüfung empfohlen: mögliches Hindernis oder Sicherheitsproblem im Straßenraum.",
            text_lower,
        )

    if category_id in [4, 6] and has_context_hazard and not has_strong_neg:
        return _decision(
            False,
            True,
            "llm_review",
            "nearby_only",
            "unrelated",
            0.5,
            True,
            "LLM-Prüfung empfohlen: Verkehrszeichen- oder Ampelproblem ohne eindeutigen Fahrradbezug.",
            text_lower,
        )

    if category_id in [4, 6] and has_context_hazard:
        return _decision(
            False,
            True,
            "llm_review",
            "nearby_only",
            "unrelated",
            0.45,
            True,
            "LLM-Prüfung empfohlen: Verkehrszeichen- oder Ampelproblem mit möglicher Verkehrswirkung.",
            text_lower,
        )

    if category_id == 5 and has_context_hazard:
        return _decision(
            False,
            True,
            "llm_review",
            "nearby_only",
            "unrelated",
            0.45,
            True,
            "LLM-Prüfung empfohlen: Beleuchtungsproblem mit möglicher Relevanz für den Radverkehr.",
            text_lower,
        )

    if category_id == 8 and (
        (WASTE_CONTEXT_RE.search(text_lower) and has_location_context)
        or (has_surface_hazard and has_location_context)
    ):
        return _decision(
            False,
            True,
            "llm_review",
            "nearby_only",
            "unrelated",
            0.45,
            True,
            "LLM-Prüfung empfohlen: Abfall, Gegenstand oder Schaden auf möglichem Wegekontext.",
            text_lower,
        )

    if category_id == 13 and (has_location_context or has_context_hazard):
        return _decision(
            False,
            True,
            "llm_review",
            "nearby_only",
            "unrelated",
            0.45,
            True,
            "LLM-Prüfung empfohlen: Verkehrsidee mit möglichem Sicherheitsbezug.",
            text_lower,
        )

    if has_strong_neg and not has_soft_bike and not has_context_hazard and not has_surface_hazard:
        return _decision(
            False,
            False,
            "auto_fail",
            "unrelated",
            "unrelated",
            0.88,
            False,
            "Automatisch ausgeschlossen: starker Hinweis auf nicht fahrradbezogenen Kontext.",
            text_lower,
        )

    if category_id in [8, 10, 11] and has_context_hazard and not has_strong_neg:
        if category_id == 8 and WASTE_CONTEXT_RE.search(text_lower) and not has_obstruction:
            return _decision(
                False,
                False,
                "auto_fail",
                "unrelated",
                "unrelated",
                0.75,
                False,
                "Automatisch ausgeschlossen: Müllmeldung ohne Blockade oder Fahrradbezug.",
                text_lower,
            )
        return _decision(
            False,
            True,
            "llm_review",
            "nearby_only",
            "unrelated",
            0.5,
            True,
            "LLM-Prüfung empfohlen: möglicher Wege- oder Sichtlinienkonflikt ohne klaren Fahrradbezug.",
            text_lower,
        )

    if category_id in [10, 11] and (has_surface_hazard or has_context_hazard) and has_location_context:
        return _decision(
            False,
            True,
            "llm_review",
            "nearby_only",
            "unrelated",
            0.45,
            True,
            "LLM-Prüfung empfohlen: Grün- oder Wegeproblem mit möglicher Relevanz für den Radverkehr.",
            text_lower,
        )

    if category_id == 8 and WASTE_CONTEXT_RE.search(text_lower) and has_location_context:
        return _decision(
            False,
            True,
            "llm_review",
            "nearby_only",
            "unrelated",
            0.45,
            True,
            "LLM-Prüfung empfohlen: Abfall oder Gegenstand auf möglichem Wegekontext.",
            text_lower,
        )

    if has_soft_bike or (has_context_hazard and has_location_context and not has_strong_neg):
        return _decision(
            False,
            True,
            "llm_review",
            "nearby_only",
            "unrelated",
            0.45,
            True,
            "LLM-Prüfung empfohlen: schwacher Fahrrad- oder Infrastrukturhinweis.",
            text_lower,
        )

    return _decision(
        False,
        False,
        "auto_fail",
        "unrelated",
        "unrelated",
        0.82,
        False,
        "Automatisch ausgeschlossen: kein Fahrradbezug und kein prüfpflichtiges Gefahrenmuster.",
        text_lower,
    )


def _subcategory_for_context(text_lower, category_id):
    if re.search(r"scherben\w*|glasscherben\w*|\bglas\b|müll|abfall|verschmutz", text_lower):
        return "glass_debris"
    if re.search(r"hecke|sträucher|äste|zweige|bewuchs|zugewachsen|baum", text_lower):
        return "vegetation_block"
    if re.search(r"zuparken|zugeparkt|blockiert|versperrt|hindernis", text_lower):
        return "illegal_parking_obstruction"
    if re.search(r"ampel|schaltung|induktionsschleife|sensor", text_lower) or category_id == 6:
        return "signal_light_timing"
    if re.search(r"schild|beschilderung|wegweiser", text_lower) or category_id == 4:
        return "signage_detours"
    if re.search(r"kreuzung|einmündung|querung|überquer|sicht", text_lower):
        return "crossing_safety"
    if re.search(r"ständer|bügel|stellplatz|fundrad", text_lower) or category_id == 7:
        return "bike_parking"
    if GENERIC_SURFACE_RE.search(text_lower) or category_id == 3:
        return "pothole_damage"
    return "other_cycling"


def classify_regex(text, category_id):
    return classify_report_rules(text, category_id).is_regex_candidate


def should_route_to_llm(text, category_id):
    return classify_report_rules(text, category_id).route == "llm_review"
