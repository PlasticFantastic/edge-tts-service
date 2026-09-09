from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
import edge_tts

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "ok", "service": "Edge TTS for SF Bot"}

@app.get("/tts")
async def generate_tts(text: str, voice: str = "ru-RU-DmitryNeural", pitch: str = "-80Hz"):
    try:
        # Формируем генератор речи с заниженным тоном (pitch) для Эсефе
        communicate = edge_tts.Communicate(text, voice, pitch=pitch)
        
        # Собираем байты аудиофайла
        audio_data = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
                
        # Отдаем как MP3
        return Response(content=bytes(audio_data), media_type="audio/mpeg")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
