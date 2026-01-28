"""
Agricultural Discourse Classification Module

Classifies agricultural discourse into 4 categories based on keywords:
- PRODUCTIVISTE: Intensive/industrial agriculture focused on yield
- ALTERNATIF: Sustainable/bio/agroecology agriculture
- NEUTRE: General agricultural discourse
- AUTRE: Non-agricultural content
"""

from typing import List, Dict, Any


# Keywords for PRODUCTIVISTE (intensive/industrial agriculture)
KEYWORDS_PRODUCTIVISTE = {
    # Intensification & yield
    "rendement",
    "productivité",
    "production",
    "intensif",
    "intensive",
    "industriel",
    "industrielle",
    "agro-industrie",
    "agroindustrie",
    "usine",
    "exportation",
    "export",
    # Chemical inputs
    "pesticide",
    "pesticides",
    "herbicide",
    "herbicides",
    "fongicide",
    "fongicides",
    "insecticide",
    "insecticides",
    "engrais",
    "chimique",
    "chimiques",
    "phytosanitaire",
    "phytosanitaires",
    "traitement",
    "traitements",
    "glyphosate",
    "roundup",
    # Intensive practices
    "monoculture",
    "ogm",
    "transgénique",
    "mécanisation",
    "irrigation",
    "drainage",
    "remembrement",
    "concentré",
    "élevage intensif",
    "batterie",
    "feedlot",
    # Market economy
    "compétitivité",
    "concurrence",
    "mondialisation",
    "coopérative",
    "négoce",
    "subvention",
    "pac",
    "quota",
    "cours",
    "bourse",
    "spéculation",
    # Industrial actors
    "monsanto",
    "bayer",
    "syngenta",
    "lactalis",
    "bigard",
    "avril",
    "sofiprotéol",
}

# Keywords for ALTERNATIF (sustainable/organic agriculture)
KEYWORDS_ALTERNATIF = {
    # Organic agriculture
    "bio",
    "biologique",
    "biologiques",
    "organique",
    "organiques",
    "label",
    "certification",
    "ab",
    "agriculture biologique",
    "conversion",
    # Agroecology & permaculture
    "agroécologie",
    "agroécologique",
    "permaculture",
    "agroforesterie",
    "polyculture",
    "rotation",
    "association",
    "compagnonnage",
    "couvert",
    "couverts",
    "engrais vert",
    # Biodiversity & environment
    "biodiversité",
    "écosystème",
    "pollinisateur",
    "pollinisateurs",
    "abeille",
    "abeilles",
    "haie",
    "haies",
    "bocage",
    "mare",
    "zone humide",
    "sol vivant",
    "humus",
    # Short circuits & local
    "circuit court",
    "circuits courts",
    "local",
    "locaux",
    "proximité",
    "amap",
    "vente directe",
    "marché paysan",
    "ferme",
    "terroir",
    "artisanal",
    # Peasant agriculture
    "paysan",
    "paysanne",
    "paysans",
    "petit producteur",
    "semences paysannes",
    "autonomie",
    "autosuffisance",
    "souveraineté alimentaire",
    # Without inputs
    "sans pesticide",
    "zéro phyto",
    "naturel",
    "naturels",
    "compost",
    "fumier",
    "auxiliaire",
    "auxiliaires",
    "lutte biologique",
    "prédateur",
    "coccinelle",
    # Animal welfare
    "bien-être animal",
    "plein air",
    "pâturage",
    "extensif",
    "extensive",
    "herbe",
}

# Keywords for NEUTRE (general agriculture)
KEYWORDS_AGRICULTURE_NEUTRE = {
    # General agriculture terms
    "agriculture",
    "agricole",
    "agricoles",
    "agriculteur",
    "agriculteurs",
    "agricultrice",
    "exploitation",
    "exploitant",
    "cultivateur",
    "producteur",
    "producteurs",
    # Crops & livestock
    "culture",
    "cultures",
    "récolte",
    "récoltes",
    "moisson",
    "semis",
    "plantation",
    "céréale",
    "céréales",
    "blé",
    "maïs",
    "orge",
    "colza",
    "tournesol",
    "betterave",
    "légume",
    "légumes",
    "fruit",
    "fruits",
    "vigne",
    "vignoble",
    "vin",
    "olive",
    "élevage",
    "éleveur",
    "bétail",
    "vache",
    "vaches",
    "bovin",
    "bovins",
    "lait",
    "porc",
    "porcs",
    "volaille",
    "volailles",
    "poulet",
    "mouton",
    "moutons",
    "ovin",
    # Infrastructure
    "ferme",
    "grange",
    "silo",
    "tracteur",
    "machine",
    "matériel",
    "terrain",
    "parcelle",
    "champ",
    "champs",
    "prairie",
    "pré",
    "verger",
    "serre",
    # Seasons & weather
    "saison",
    "printemps",
    "été",
    "automne",
    "hiver",
    "sécheresse",
    "gel",
    "grêle",
    "pluie",
    "météo",
    "climat",
    "température",
    # Agricultural economy
    "marché",
    "prix",
    "vente",
    "achat",
    "revenu",
    "aide",
    "filière",
}


def classify_discourse(keywords: List[str]) -> Dict[str, Any]:
    """
    Classify a discourse based on its keywords.

    Args:
        keywords: List of keywords (nouns) extracted from the discourse

    Returns:
        dict with:
            - category: the main category (productiviste/alternatif/neutre/autre)
            - scores: the scores for each category
            - matched_keywords: the keywords matched by category
    """
    if not keywords:
        return {
            "category": "autre",
            "scores": {"productiviste": 0, "alternatif": 0, "neutre": 0, "autre": 1},
            "matched_keywords": {"productiviste": [], "alternatif": [], "neutre": []},
        }

    # Normalize keywords (lowercase)
    keywords_lower = [k.lower().strip() for k in keywords if k]

    # Count matches for each category
    matched = {"productiviste": [], "alternatif": [], "neutre": []}

    for kw in keywords_lower:
        # Check productiviste
        if kw in KEYWORDS_PRODUCTIVISTE or any(p in kw for p in KEYWORDS_PRODUCTIVISTE):
            matched["productiviste"].append(kw)
        # Check alternatif
        if kw in KEYWORDS_ALTERNATIF or any(a in kw for a in KEYWORDS_ALTERNATIF):
            matched["alternatif"].append(kw)
        # Check neutre (general agriculture)
        if kw in KEYWORDS_AGRICULTURE_NEUTRE or any(
            n in kw for n in KEYWORDS_AGRICULTURE_NEUTRE
        ):
            matched["neutre"].append(kw)

    # Calculate scores (weighted)
    # Productiviste and Alternatif have more weight as they are more specific
    score_prod = len(matched["productiviste"]) * 2
    score_alt = len(matched["alternatif"]) * 2
    score_neutre = len(matched["neutre"])

    total_agri = score_prod + score_alt + score_neutre

    # If no agricultural term, it's "autre"
    if total_agri == 0:
        return {
            "category": "autre",
            "scores": {"productiviste": 0, "alternatif": 0, "neutre": 0, "autre": 1},
            "matched_keywords": matched,
        }

    # Determine the category
    scores = {
        "productiviste": score_prod / total_agri if total_agri > 0 else 0,
        "alternatif": score_alt / total_agri if total_agri > 0 else 0,
        "neutre": score_neutre / total_agri if total_agri > 0 else 0,
        "autre": 0,
    }

    # If productiviste or alternatif clearly dominate
    if score_prod > score_alt and score_prod > score_neutre * 0.5:
        category = "productiviste"
    elif score_alt > score_prod and score_alt > score_neutre * 0.5:
        category = "alternatif"
    elif total_agri > 0:
        category = "neutre"
    else:
        category = "autre"

    return {"category": category, "scores": scores, "matched_keywords": matched}


def classify_from_keywords(keywords: List[str]) -> str:
    """
    Simple function to get only the category from keywords.

    Args:
        keywords: List of keywords (nouns)

    Returns:
        str: Category (productiviste/alternatif/neutre/autre)
    """
    result = classify_discourse(keywords)
    return result["category"]
