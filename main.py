import asyncio
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
import edge_tts

app = FastAPI()

DEFAULT_VOICE = "ru-RU-DmitryNeural"
# От самого низкого тона к запасным; "" = без изменения тона.
PITCH_FALLBACKS = ["-55Hz", "-30Hz", "-15Hz", ""]


@app.get("/")
def read_root():
    return {"status": "ok", "service": "Edge TTS for SF Bot"}


async def synthesize(text: str, voice: str, pitch: str) -> bytes:
    if pitch:
        communicate = edge_tts.Communicate(text, voice, pitch=pitch)
    else:
        communicate = edge_tts.Communicate(text, voice)

    audio_data = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.extend(chunk["data"])
    if not audio_data:
        raise RuntimeError("empty audio")
    return bytes(audio_data)


@app.get("/tts")
async def generate_tts(text: str, voice: str = DEFAULT_VOICE, pitch: str = ""):
    candidates = []
    for p in ([pitch] if pitch else []) + PITCH_FALLBACKS:
        if p not in candidates:
            candidates.append(p)

    last_error = ""
    for candidate in candidates:
        for attempt in (1, 2):
            try:
                audio = await synthesize(text, voice, candidate)
                return Response(
                    content=audio,
                    media_type="audio/mpeg",
                    headers={"X-Pitch-Used": candidate or "none"},
                )
            except Exception as e:
                last_error = f"pitch={candidate or 'none'} try={attempt}: {e}"
                print("tts attempt failed:", last_error, flush=True)
                await asyncio.sleep(0.7)

    return JSONResponse(status_code=500, content={"error": last_error})
