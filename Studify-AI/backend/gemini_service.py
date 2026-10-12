import json
import re
from google import genai
from google.genai import types
from .config import get_settings

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

settings = get_settings()

class GeminiService:
    def __init__(self):
        # We handle DUMMY_KEY gracefully in case the user hasn't set it yet
        self.client = genai.Client(api_key=settings.gemini_api_key) if settings.gemini_api_key != "DUMMY_KEY" else None
        self.model_name = "gemini-3.1-flash-lite"

    def _extract_json(self, text: str) -> dict | list:
        try:
            # Clean markdown code block if present
            if text.startswith("```json"):
                text = text.split("```json")[1].split("```")[0].strip()
            elif text.startswith("```"):
                text = text.split("```")[1].split("```")[0].strip()
            return json.loads(text)
        except Exception:
            # Fallback empty list/dict based on structure
            return [] if "[" in text else {}

    async def analyze_image(self, image_bytes: bytes, mime_type: str) -> str:
        if not self.client: return "OCR Metni (Demo)"
        content = [
            "Lütfen bu resimdeki tüm metinleri doğru ve tam olarak çıkar (OCR yap).",
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ]
        res = await self.client.aio.models.generate_content(model=self.model_name, contents=content)
        return res.text

    async def solve_question(self, image_bytes: bytes, mime_type: str) -> dict:
        if not self.client: return {"extracted_text": "Demo Soru", "solution": "Demo Çözüm"}
        content = [
            "Sen uzman bir öğretmen ve asistansın. Resimdeki soruyu (veya metni) oku ve adım adım, anlaşılır bir şekilde Türkçe olarak çöz. Markdown kullan.",
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ]
        res = await self.client.aio.models.generate_content(model=self.model_name, contents=content)
        return {"extracted_text": "Resimden okunan soru", "solution": res.text}

    async def generate_flashcards(self, notes_text: str, count: int = 5) -> list[dict]:
        if not self.client: return [{"front_text": "Soru 1", "back_text": "Cevap 1"}]
        prompt = f"""Şu ders notlarından {count} adet Soru-Cevap flashcard üret.
Yalnızca JSON formatında yanıt ver. Örnek format:
[ {{"front_text": "Soru", "back_text": "Cevap"}} ]

Notlar:
{notes_text}
"""
        res = await self.client.aio.models.generate_content(model=self.model_name, contents=prompt)
        return self._extract_json(res.text)

    def _extract_youtube_id(self, url: str) -> str:
        match = re.search(r'(?:v=|youtu\.be/|/v/|/embed/|/shorts/)([^&?/\s]{11})', url)
        if match:
            return match.group(1)
        return ""

    async def summarize_content(self, content: str, content_type: str = 'text') -> dict:
        if not self.client: return {"title": "Demo Özet", "content": "Bu bir demo özet metnidir."}
        
        actual_content = content
        if content_type == 'url':
            yt_id = self._extract_youtube_id(content)
            if yt_id and YouTubeTranscriptApi:
                try:
                    transcript_list = YouTubeTranscriptApi.get_transcript(yt_id, languages=['tr', 'en'])
                    transcript_text = " ".join([t['text'] for t in transcript_list])
                    actual_content = f"Video Altyazısı (Transkript):\n{transcript_text}"
                except Exception:
                    return {"error": "Video altyazısı alınamadı. Lütfen 'Metin' sekmesine geçip video açıklamasını veya ders notlarını manuel olarak yapıştırın."}
            else:
                return {"error": "YouTube altyazı kütüphanesi bulunamadı veya geçersiz video. Lütfen 'Metin' sekmesini kullanın."}

        prompt = f"Sen harika bir eğitmensin. Lütfen şu içeriği detaylı ve akademik olarak ancak çok anlaşılır şekilde özetle. Başlık ve içerik olarak ayır. Markdown kullan.\n\nİçerik:\n{actual_content}"
        res = await self.client.aio.models.generate_content(model=self.model_name, contents=prompt)
        # Basit ayırma: İlk satır başlık, kalanı içerik
        lines = res.text.split('\n')
        title = lines[0].replace('#', '').strip() if lines else "Özet"
        body = '\n'.join(lines[1:]).strip() if len(lines) > 1 else res.text
        return {"title": title, "content": body}

    async def generate_quiz(self, subject: str, grade_level: str, topic: str, count: int = 5) -> list[dict]:
        if not self.client: return [{"question": "Soru?", "options": ["A","B","C","D"], "correct_answer": 0, "explanation": "Çünkü"}]
        prompt = f"""Sen uzman bir sınav hazırlayıcısın. {grade_level} seviyesinde, {subject} dersinin {topic} konusuyla ilgili {count} soruluk çoktan seçmeli bir test hazırla.
Sadece JSON formatında çıktı ver. Format:
[ {{ "question": "Soru metni", "options": ["Şık A", "Şık B", "Şık C", "Şık D"], "correct_answer": 0, "explanation": "Doğru cevabın açıklaması" }} ]
correct_answer, 0 ile 3 arasında bir tam sayı olmalıdır.
"""
        res = await self.client.aio.models.generate_content(model=self.model_name, contents=prompt)
        return self._extract_json(res.text)

    async def chat_coach(self, message: str, history: list[dict] = []) -> str:
        if not self.client: return "Merhaba, ben Studify AI koçuyum! (Demo)"
        
        # History objesini Gemini formatına çevirebiliriz ama basitçe text'e eklemek de etkili
        hist_text = ""
        for h in history:
            role = "Öğrenci" if h.get("role") == "user" else "AI Koç"
            hist_text += f"{role}: {h.get('content')}\n"
            
        prompt = f"""Sen arkadaş canlısı, destekleyici, motive edici bir yapay zeka ders koçusun. Adın Studify AI Koç. 
Öğrencinin sorusunu akılda kalıcı, samimi ve Türkçe dilbilgisi kurallarına uyarak yanıtla. Markdown ile zenginleştir.
Önceki Konuşmalar:
{hist_text}

Öğrenci: {message}
AI Koç:"""
        res = await self.client.aio.models.generate_content(model=self.model_name, contents=prompt)
        return res.text

gemini_service = GeminiService()
