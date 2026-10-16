import os
import json
import base64
import time
import random
import io

import requests
from PIL import Image

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "qwen/qwen3.8-27b"

MAX_IMAGE_SIZE = 1024
MAX_RETRIES = 2
REQUEST_TIMEOUT = 30


class ScannerError(Exception):
    """Raised when waste scanning fails."""
    pass


def _prepare_image(image_bytes, mime_type):
    """Resize and compress images to reduce upload size."""

    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()

        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        elif image.mode == "L":
            image = image.convert("RGB")

        image.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE))

        output = io.BytesIO()

        if mime_type == "image/png":
            image.save(output, format="PNG", optimize=True)
            output_type = "image/png"
        else:
            image.save(output, format="JPEG", quality=75, optimize=True)
            output_type = "image/jpeg"

        return output.getvalue(), output_type

    except Exception as error:
        raise ScannerError(
            f"Could not prepare image: {error}"
        ) from error


def _parse_result(content):
    """Parse the model response and validate required fields."""

    if isinstance(content, list):
        content = "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict)
        )

    if not isinstance(content, str) or not content.strip():
        raise ScannerError("The AI returned an empty response.")

    content = content.strip()

    if content.startswith("```"):
        content = content.split("\n", 1)[-1]
        if content.endswith("```"):
            content = content[:-3].strip()
        if content.lower().startswith("json"):
            content = content[4:].strip()

    start = content.find("{")
    end = content.rfind("}")

    if start == -1 or end == -1:
        raise ScannerError("The AI did not return valid JSON.")

    try:
        result = json.loads(content[start:end + 1])
    except json.JSONDecodeError as error:
        raise ScannerError(
            "The AI returned invalid JSON."
        ) from error

    if not isinstance(result, dict):
        raise ScannerError("The AI returned an unexpected result.")

    fields = (
        "item",
        "category",
        "reason",
        "disposal_advice",
    )

    for field in fields:
        result.setdefault(field, "Not available")

    return result


def scan_waste_bytes(image_bytes, mime_type="image/jpeg", *extra_args):
    """
    Analyze an image using Groq.
    Supports both two-argument and legacy three-argument calls.
    """

    if extra_args:
        mime_type = extra_args[-1]

    if not image_bytes:
        raise ScannerError("No image was received.")

    if mime_type not in (
        "image/jpeg",
        "image/png",
        "image/webp",
    ):
        raise ScannerError(f"Unsupported image format: {mime_type}")

    api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        raise ScannerError(
            "GROQ_API_KEY is missing. Configure your Groq API key."
        )

    image_bytes, mime_type = _prepare_image(
        image_bytes,
        mime_type,
    )

    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Classify this waste image. Return only a JSON "
                            "object with item, category, reason, and "
                            "disposal_advice. Categories: Plastic, Paper, "
                            "Cardboard, Glass, Metal, Organic, Electronic "
                            "waste, Textile, or Other. If uncertain, say so."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                f"data:{mime_type};base64,{encoded_image}"
                            )
                        },
                    },
                ],
            }
        ],
        "temperature": 0,
        "max_tokens": 250,
    }

    last_error = "Unknown error"

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 200:
                try:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    return _parse_result(content)
                except (ValueError, KeyError, TypeError, IndexError) as error:
                    raise ScannerError(
                        f"Could not process AI response: {error}"
                    ) from error

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")

                try:
                    delay = float(retry_after)
                except (TypeError, ValueError):
                    delay = min(2 ** (attempt + 1), 8)

                last_error = (
                    "Groq rate limit reached. Please retry shortly."
                )

                if attempt < MAX_RETRIES:
                    time.sleep(min(delay, 8) + random.uniform(0, 0.3))
                    continue

                break

            if response.status_code >= 500 and attempt < MAX_RETRIES:
                last_error = (
                    f"Groq server temporarily unavailable "
                    f"(HTTP {response.status_code})."
                )
                time.sleep(1 + attempt)
                continue

            try:
                details = response.json().get("error", {}).get(
                    "message", response.text
                )
            except (ValueError, AttributeError):
                details = response.text

            raise ScannerError(
                f"Groq API HTTP {response.status_code}: {details}"
            )

        except requests.Timeout:
            last_error = "The AI request timed out."

            if attempt < MAX_RETRIES:
                time.sleep(1 + attempt)
                continue

        except requests.RequestException as error:
            last_error = f"Network connection failed: {error}"

            if attempt < MAX_RETRIES:
                time.sleep(1 + attempt)
                continue

    raise ScannerError(
        f"{last_error} No reliable AI result was produced. "
        "Please try again later or review the item manually."
    )


def scan_waste(image_path):
    """Analyze a waste image using its file path."""

    try:
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
    except OSError as error:
        raise ScannerError(
            f"Could not read image: {error}"
        ) from error

    extension = os.path.splitext(image_path)[1].lower()

    mime_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(extension)

    if mime_type is None:
        raise ScannerError("Unsupported image format.")

    return scan_waste_bytes(image_bytes, mime_type)