import os, json
from openai import OpenAI

MODEL = "openai/gpt-oss-120b"

c = OpenAI(base_url="https://api.groq.com/openai/v1",
           api_key=os.environ["GROQ_API_KEY"])

SYSTEM = """Clasifica el email. Responde SOLO con JSON con estas claves:
categoria (factura|consulta|queja|spam|otro),
urgencia (alta|media|baja),
resumen (máximo 15 palabras).
Reglas: el spam siempre tiene urgencia baja.
Una queja con más de una semana de retraso es urgencia alta.
Los documentos adjuntos sin petición son urgencia baja."""

def clasificar(email):
    r = c.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": email}])
    return json.loads(r.choices[0].message.content)

if __name__ == "__main__":
    emails = [
        "Mi factura de octubre sale duplicada. Es urgente.",
        "¿Tenéis hueco para una cita el jueves por la tarde?",
        "Llevo 3 semanas esperando mi pedido y nadie responde.",
        "GANA DINERO RÁPIDO haciendo clic aquí!!!",
        "Adjunto el albarán firmado de la entrega de ayer.",
    ]
    for e in emails:
        print(e[:45], "->", clasificar(e))