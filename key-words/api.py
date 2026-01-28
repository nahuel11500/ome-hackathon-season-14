from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict
import uvicorn
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rake_nltk.rake import Rake
import nltk
import pandas as pd
import spacy


class GenerateRequest(BaseModel):
    """Request model for sentiment prediction"""

    texts: list[str]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "texts": ["C'est un excellent reportage sur l'agriculture durable."]
            }
        }
    )


class GenerateResponse(BaseModel):
    """Response model for keyword generation"""

    keywords_filtered: list[str]
    nouns_found: list[str]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "keywords_filtered": [
                    "agriculture durable",
                    "réchauffement climatique",
                ],
                "nouns_found": ["agriculture", "réchauffement"],
            }
        }
    )


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Keyword Generator service",
    description="Microservice to generate keywords",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "keywords",
    }


@app.post("/predict")
async def generate_keywords(request: GenerateRequest):
    nltk.download("stopwords", quiet=True)
    nltk.download("punkt_tab", quiet=True)

    # Charger les stop words français
    from nltk.corpus import stopwords

    french_stopwords = set(stopwords.words("french"))

    rake = Rake(language="french")

    df = pd.DataFrame(request.texts, columns=["report_text"])

    df["keywords"] = df["report_text"].apply(
        lambda text: extract_keywords_row(text, rake, french_stopwords)
    )

    # Load French NER model
    nlp = spacy.load("fr_core_news_sm")

    df["keywords_nouns_analysis"] = df["keywords"].apply(
        lambda kw_list: filter_keywords_by_nouns(kw_list, nlp)
    )

    # Return list of results
    results = []
    for result in df["keywords_nouns_analysis"]:
        results.append(
            {
                "keywords_filtered": result.get("keywords_filtered", []),
                "nouns_found": result.get("nouns_found", []),
            }
        )

    return results


def extract_keywords_row(text: str, rake_extractor, stopwords_set: set) -> list:
    """
    Extrait les keywords filtrés d'un texte donné
    Retourne une liste de keywords nettoyés et validés
    """
    if not isinstance(text, str) or not text.strip():
        return []

    # Extraire les keywords avec RAKE
    rake_extractor.extract_keywords_from_text(text)
    keywords = rake_extractor.get_ranked_phrases()

    filtered_keywords = []
    unique_keywords = set(keywords)

    for keyword in unique_keywords:
        # Nettoyer le keyword
        keyword_clean = keyword.strip().lower()

        # Ignorer les keywords vides ou trop courts
        if len(keyword_clean) < 3:
            continue

        words_in_keyword = keyword_clean.split()

        # Si c'est un mot unique
        if len(words_in_keyword) == 1:
            if keyword_clean in stopwords_set or keyword_clean.isdigit():
                continue
        else:
            # Pour les phrases, vérifier qu'au moins un mot n'est pas un stop word
            significant_words = [
                w for w in words_in_keyword if w not in stopwords_set and len(w) >= 3
            ]
            if len(significant_words) == 0:
                continue

        filtered_keywords.append(keyword_clean)

    return filtered_keywords


# Traiter les keywords avec spaCy pour détecter les noms communs
def filter_keywords_by_nouns(keywords_list: list, nlp_model) -> dict:
    """
    Filtre les keywords en gardant seulement ceux contenant au least un nom commun
    Retourne un dict avec les keywords filtrés et leurs noms communs associés
    """
    if not keywords_list:
        return {"keywords_filtered": [], "nouns_found": []}

    filtered_kw = []
    all_nouns = []

    for keyword in keywords_list:
        doc = nlp_model(keyword)
        nouns_in_kw = [tok.text for tok in doc if tok.pos_ == "NOUN"]

        # Garder le keyword seulement s'il contient au moins un nom commun
        if nouns_in_kw:
            filtered_kw.append(keyword)
            all_nouns.extend(nouns_in_kw)

    return {"keywords_filtered": filtered_kw, "nouns_found": list(set(all_nouns))}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
