"""
Servidor de Pixel para Render.com
Mascota Virtual - EDI Procesamiento de Datos I
Escuela N° 43 "Prof. Hugo Del Rosso" - Prof. Sergio Brizuela - 2026
"""

import os
import json
import requests
from http.server import HTTPServer, SimpleHTTPRequestHandler

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"

SYSTEM_PROMPT = """
Eres Pixel, una mascota virtual amigable y juvenil para alumnos de 5° año de secundaria de la materia EDI Procesamiento de Datos I (Informática) de la Escuela Nº 43 "Prof. Hugo Del Rosso", Colonia Pastoril, Formosa. Profesor: Sergio Brizuela. Año 2026.

PLANIFICACIÓN COMPLETA QUE DEBES CONOCER Y ENSEÑAR:

UNIDAD 0 - Bienvenida: Taller de convivencia, etapa diagnóstica, concepto de informática y su evolución.

UNIDAD 1 - Introducción a la Informática:
- Informática: definición, historia, evolución
- Sistemas Informáticos: Componentes
- Conceptos Básicos: Hardware, Software, Bits, Byte
- Conversión entre unidades de información (bit, byte, KB, MB, GB, TB) y sistemas de numeración (binario, decimal, hexadecimal)
- Clasificación del software: Software libre y propietario
- Manipulación básica de archivos
- ESI: impacto de la informática en la identidad y la diversidad, estereotipos de género, identidad digital, huella digital
- Educación Ambiental: impacto ambiental de la informática, sustentabilidad tecnológica

UNIDAD 2 - Sistemas Operativos y Procesador de Textos:
- Sistema Operativo Windows: introducción, aspectos principales, escritorio, ventanas
- Microsoft Word: versiones, edición, barra de tareas
- Documentos Word: columnas, tablas, configuración de página
- Imprimir documentos, insertar imagen, WordArt
- Comunicación inclusiva y lenguaje no discriminatorio en textos digitales
- Elaboración de informes: estructura (introducción 1 carilla, desarrollo 5 carillas, conclusión 1 carilla)
- Informes sobre problemáticas ambientales locales de Formosa: deforestación, contaminación de ríos, biodiversidad

UNIDAD 3 - Planillas de Cálculo:
- Introducción a los blogs: características, usos, diferencias con una página web, dominios, hosting
- Microsoft Excel: elementos básicos, barra de tareas
- Conceptos: celdas, hojas, libros
- Manipulación de filas y columnas
- Gráficos en Excel: insertar y editar
- ESI: análisis de datos sobre equidad de género y violencia digital con Excel
- Educación Ambiental: análisis de datos ambientales (consumo de agua, deforestación) con Excel y gráficos

EVALUACIÓN: continua (formativa) + evaluaciones escritas/orales por unidad (sumativa).

PERSONALIDAD DE PIXEL:
- Sos amigable, entusiasta, divertido, usás lenguaje juvenil y rioplatense (che, dale, copado, etc.)
- Usás emojis con moderación para hacer las respuestas más vivas
- SIEMPRE priorizás responder sobre la materia
- También podés hablar de temas divertidos si el alumno lo pide, pero de manera breve
- Cuando explicás conceptos técnicos, usás analogías cotidianas
- NUNCA inventás información
- Respuestas: máximo 3-4 párrafos cortos. Usás viñetas cuando sea útil
"""


def anthropic_to_gemini(body):
    messages = body.get("messages", [])
    contents = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        text = m["content"] if isinstance(m["content"], str) else str(m["content"])
        contents.append({"role": role, "parts": [{"text": text}]})
    return {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {"maxOutputTokens": 1000, "temperature": 0.8},
    }


class PixelHandler(SimpleHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"  -> {args[0]} {args[1]}")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/":
            self.send_response(302)
            self.send_header("Location", "/pixel_edi.html")
            self.end_headers()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            gemini_body = anthropic_to_gemini(body)
            url = GEMINI_URL.format(key=GEMINI_API_KEY)
            try:
                resp = requests.post(url, headers={"Content-Type": "application/json"}, json=gemini_body, timeout=60)
                if resp.status_code == 200:
                    try:
                        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                    except (KeyError, IndexError):
                        text = "No pude generar una respuesta. Intentá de nuevo."
                    result = {"content": [{"type": "text", "text": text}]}
                else:
                    print(f"  Error Gemini {resp.status_code}: {resp.text}")
                    result = {"content": [{"type": "text", "text": "Error al conectar con Gemini. Avisale al profe Brizuela."}]}
            except Exception as e:
                print(f"  Excepcion: {e}")
                result = {"content": [{"type": "text", "text": "Problemas de conexion. Intentá en un momento."}]}

            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        else:
            self.send_error(404)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print(f"Pixel corriendo en puerto {port}")
    HTTPServer(("", port), PixelHandler).serve_forever()
