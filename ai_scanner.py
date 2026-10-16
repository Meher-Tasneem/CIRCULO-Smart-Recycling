from PIL import Image
from transformers import pipeline

# CIRCULO waste image classifier
MODEL_NAME = "openai/clip-vit-base-patch32"

WASTE_CATEGORIES = [
    "a photo of a plastic bottle or plastic waste",
    "a photo of cardboard waste",
    "a photo of paper waste",
    "a photo of a metal can or metal waste",
    "a photo of a glass bottle or glass waste",
    "a photo of organic food waste",
    "a photo of electronic waste",
    "a photo of textile or fabric waste",
    "a photo of other mixed waste",
]
# Load the model only when classification is requested.
_classifier = None


def get_classifier():
    global _classifier

    if _classifier is None:
        _classifier = pipeline(
            task="zero-shot-image-classification",
            model=MODEL_NAME
        )

    return _classifier


def classify_waste_image(image):
    """
    Input: a PIL image.
    Output: predicted category, relative model score,
    and the ranked candidate categories.
    """
    if not isinstance(image, Image.Image):
        raise TypeError("Please provide a valid PIL image.")

    image = image.convert("RGB")
    model = get_classifier()

    results = model(
        image,
        candidate_labels=WASTE_CATEGORIES
    )

    if not results:
        raise RuntimeError("The model returned no predictions.")

    top = results[0]

    category_names = {
        "a photo of a plastic bottle or plastic waste": "Plastic",
        "a photo of cardboard waste": "Cardboard",
        "a photo of paper waste": "Paper",
        "a photo of a metal can or metal waste": "Metal",
        "a photo of a glass bottle or glass waste": "Glass",
        "a photo of organic food waste": "Organic",
        "a photo of electronic waste": "Electronic Waste",
        "a photo of textile or fabric waste": "Textile",
        "a photo of other mixed waste": "Mixed / Other",
    }

    return {
        "category": category_names.get(top["label"], "Mixed / Other"),
        "score": float(top["score"]),
        "method": "CLIP zero-shot image classification",
        "ranked_results": [
            {
                "category": category_names.get(
                    item["label"], "Mixed / Other"
                ),
                "score": float(item["score"])
            }
            for item in results
        ]
    }