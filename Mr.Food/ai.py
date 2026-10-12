import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def generate_recipe(food_name: str, is_diet: bool = False):
    diet_instructions = ""
    if is_diet:
        diet_instructions = """DIET MODE IS ENABLED:
- Ensure the recipe is genuinely low calorie and low fat.
- Avoid deep frying. Use baking (fırınlama), boiling (haşlama), steaming (buharda pişirme), or air-frying.
- Keep portions small (1-2 servings). Reduce ingredient amounts accordingly.
- Use realistic healthy ingredients."""

    prompt = f"""You are Mr.Food, a professional AI chef.
The user wants a recipe for: {food_name}
{diet_instructions}

You MUST return a valid JSON object strictly matching this structure:
{{
  "name": "Name of the recipe in Turkish",
  "ingredients": ["ingredient 1 with its amount in Turkish (e.g., '2 adet yumurta', '1 su bardağı süt')", "ingredient 2 with its amount in Turkish"],
  "steps": ["step 1 in Turkish", "step 2 in Turkish"],
  "estimated_calories": "total estimated kcal as a string e.g. '450 kcal'" (estimated_calories MUST be the TOTAL calories of all ingredients combined, not calories per serving.)
}}

CRITICAL RULES:
1. Every ingredient MUST include a specific amount (grams, pieces, spoons, cups, etc.).
2. ALL text in the JSON MUST be in Turkish ONLY. No English words.
3. For salt/pepper/spices always write exact amounts like "1 çay kaşığı tuz".
4. estimated_calories: calculate based on ingredients. Be precise and realistic.
5. Do NOT output anything outside the JSON object.
6. Use ONLY real, existing Turkish culinary terms. Never invent or use made-up words. For example, use "kekik", "maydanoz", "ekmek kırıntısı" — never invent terms like "garnik" or "panopan".
7. Ingredient names must be real, commonly known foods available in Turkish markets.
"""

    try:
        response = gemini_client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt
        )

        text = response.text.strip()
        # JSON bloğu varsa temizle
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        recipe_data = json.loads(text)
        return recipe_data

    except Exception as e:
        print(f"Error calling Gemini API (recipe): {e}")
        return None


def analyze_food_photo(image_data: str, details: str = ""):
    import base64

    details_prompt = f"\n\nKullanıcının ek bilgileri: {details}" if details else ""

    prompt = f"""Sen bir yapay zeka diyetisyenisin. Fotoğraftaki yemeği analiz et ve sadece JSON döndür:

{{
  "food_name": "Yemeğin adı (Türkçe)",
  "total_calories": "Tahmini toplam kalori (ör: '450 kcal')",
  "protein": "Protein miktarı (ör: '25g')",
  "carbs": "Karbonhidrat miktarı (ör: '40g')",
  "fat": "Yağ miktarı (ör: '15g')",
  "portion_size": "Porsiyon büyüklüğü (ör: '1 porsiyon ~250g')",
  "description": "Besin değerlendirmesi ve sağlık notu (Türkçe, 2-3 cümle)"
}}{details_prompt}

KURALLAR:
- Sadece JSON döndür, başka metin yazma.
- Tüm değerler tahminidir, bunu description'da belirt.
- Türkçe yanıt ver.
- Fotoğrafta yemek/net bir şey yoksa {{"error": "Fotoğrafta yemek tespit edilemedi. Lütfen net bir yemek fotoğrafı yükleyin."}} döndür."""

    try:
        image_bytes = base64.b64decode(image_data)
        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

        response = gemini_client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=[prompt, image_part]
        )

        text = response.text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        result = json.loads(text)
        return result

    except Exception as e:
        print(f"Error calling Gemini API (food photo): {e}")
        return None
