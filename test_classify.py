import contextlib
import importlib
import io
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import httpx
from openai import APIConnectionError, AuthenticationError, RateLimitError

import classify
from classify import ErrorClasificacion, clasificar, validar_resultado


def respuesta(contenido, motivo="stop"):
    return SimpleNamespace(choices=[SimpleNamespace(
        finish_reason=motivo, message=SimpleNamespace(content=contenido)
    )])


class ClasificadorTests(unittest.TestCase):
    def test_importar_no_necesita_clave(self):
        with patch.dict(os.environ, {}, clear=True):
            importlib.reload(classify)

    def test_falta_clave(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(classify.ErrorClasificacion):
                classify.crear_cliente()

    def test_entrada_invalida_no_llama_api(self):
        cliente = Mock()
        for email in (None, "", "   ", 3):
            with self.subTest(email=email), self.assertRaises(classify.ErrorClasificacion):
                clasificar(email, cliente=cliente)
        cliente.chat.completions.create.assert_not_called()

    def test_resultado_valido_y_normalizacion(self):
        cliente = Mock()
        cliente.chat.completions.create.return_value = respuesta(json.dumps({
            "categoria": "factura", "urgencia": "media", "resumen": "  Factura   duplicada  "
        }))
        self.assertEqual(clasificar("Factura duplicada", cliente=cliente), {
            "categoria": "factura", "urgencia": "media", "resumen": "Factura duplicada"
        })

    def test_spam_siempre_baja(self):
        self.assertEqual(validar_resultado(json.dumps({
            "categoria": "spam", "urgencia": "alta", "resumen": "Promoción sospechosa"
        }))["urgencia"], "baja")

    def test_rechaza_respuestas_invalidas(self):
        base = {"categoria": "otro", "urgencia": "baja", "resumen": "Documento recibido"}
        casos = [None, "", "no json", "[]", "null", "{}",
                 json.dumps({**base, "extra": True}),
                 json.dumps({**base, "categoria": "desconocida"}),
                 json.dumps({**base, "urgencia": "urgente"}),
                 json.dumps({**base, "categoria": []}),
                 json.dumps({**base, "resumen": None}),
                 json.dumps({**base, "resumen": " "}),
                 json.dumps({**base, "resumen": "palabra " * 16})]
        for caso in casos:
            with self.subTest(caso=caso), self.assertRaises(classify.ErrorClasificacion):
                validar_resultado(caso)

    def test_rechaza_respuesta_incompleta(self):
        cliente = Mock()
        for valor in (SimpleNamespace(choices=[]), respuesta("{}", "length")):
            cliente.chat.completions.create.return_value = valor
            with self.assertRaises(classify.ErrorClasificacion):
                clasificar("Hola", cliente=cliente)

    def test_errores_api_no_exponen_datos(self):
        request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
        errores = [APIConnectionError(request=request)]
        for tipo, codigo in ((AuthenticationError, 401), (RateLimitError, 429)):
            errores.append(tipo("SECRETO", response=httpx.Response(codigo, request=request), body=None))
        for error in errores:
            cliente = Mock()
            cliente.chat.completions.create.side_effect = error
            with self.subTest(error=type(error).__name__), self.assertRaises(classify.ErrorClasificacion) as capturado:
                clasificar("CORREO PRIVADO", cliente=cliente)
            self.assertNotIn("SECRETO", str(capturado.exception))
            self.assertNotIn("CORREO PRIVADO", str(capturado.exception))

    def test_cli_continua_tras_error_y_devuelve_fallo(self):
        with patch.object(classify, "crear_cliente"), patch.object(classify, "clasificar") as llamada:
            llamada.side_effect = [classify.ErrorClasificacion("Fallo"), *([{
                "categoria": "otro", "urgencia": "baja", "resumen": "Ejemplo"
            }] * 4)]
            salida, errores = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(salida), contextlib.redirect_stderr(errores):
                self.assertEqual(classify.main(), 1)
            self.assertEqual(len(salida.getvalue().splitlines()), 4)
            self.assertIn("Error en ejemplo 1", errores.getvalue())


if __name__ == "__main__":
    unittest.main()
