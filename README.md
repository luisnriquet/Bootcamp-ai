# Bootcamp IA

## Proyecto 0: Clasificador de emails con IA

Recibe el texto de un email y devuelve `categoria`, `urgencia` y un `resumen` de hasta 15 palabras. Usa Python y la API de Groq mediante el SDK de OpenAI.

Esta primera fase procesa cinco ejemplos incluidos en `classify.py`. Todavía no lee Gmail, aplica etiquetas ni guarda correos.

### 1. Preparar el entorno

Necesitas Python 3.9 o posterior y una clave de Groq.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

En Windows PowerShell, activa el entorno con `.venv\Scripts\Activate.ps1`.

### 2. Configurar la clave

En macOS/Linux, introduce la clave sin escribirla en el historial:

```bash
read -rs -p "GROQ_API_KEY: " GROQ_API_KEY
export GROQ_API_KEY
echo
```

En PowerShell:

```powershell
$env:GROQ_API_KEY = Read-Host "GROQ_API_KEY" -MaskInput
```

`-MaskInput` requiere PowerShell 7.1 o posterior. También puedes configurar la variable desde los ajustes de tu entorno de desarrollo. No incluyas la clave en el código ni en GitHub. Los archivos `.env` están ignorados, pero este programa no los carga automáticamente.

### 3. Ejecutar los ejemplos

```bash
python classify.py
```

Cada ejemplo genera una línea JSON. Por ejemplo, el formato de salida es:

```json
{"categoria": "queja", "urgencia": "alta", "resumen": "Pedido pendiente desde hace tres semanas"}
```

Categorías admitidas: `factura`, `consulta`, `queja`, `spam`, `otro`.
Urgencias admitidas: `alta`, `media`, `baja`.

El programa comprueba los campos, sus valores y la longitud del resumen. Si la categoría es spam, fuerza la urgencia baja. Las reglas sobre quejas con más de una semana de retraso y adjuntos sin petición se solicitan en el prompt; su interpretación aún debe comprobarse con el modelo real. La instrucción de ignorar órdenes dentro del email reduce el riesgo de manipulación, pero no garantiza que la IA nunca se equivoque.

La conexión usa un timeout de 30 segundos por intento y hasta dos reintentos del SDK para fallos transitorios. Si un ejemplo falla, muestra un mensaje en stderr, continúa con los siguientes y termina con código 1. No muestra el contenido del correo ni los detalles de la API en esos errores.

### 4. Probar sin consumir la API

```bash
python -m unittest discover -v
```

Estas pruebas simulan las respuestas de Groq. Verifican validación, corrección de urgencia del spam, errores de conexión/autenticación/cuota y continuidad del procesamiento. No demuestran la precisión semántica del modelo.

Para probar con Groq, ejecuta los cinco ejemplos y revisa especialmente:

| Ejemplo | Comprobación esperada |
| --- | --- |
| Factura duplicada | Categoría factura |
| Solicitud de cita | Categoría consulta |
| Pedido con tres semanas de retraso | Categoría queja y urgencia alta |
| Promoción sospechosa | Categoría spam y urgencia baja |
| Albarán sin petición | Urgencia baja |

Las llamadas reales envían el texto a Groq y pueden consumir cuota. Empieza con ejemplos ficticios. El modelo por defecto es `openai/gpt-oss-120b`; puedes cambiarlo mediante `GROQ_MODEL` a uno compatible con salida JSON disponible en tu cuenta.

### 5. Reutilizar la función

```python
from classify import clasificar

resultado = clasificar("Llevo tres semanas esperando mi pedido.")
print(resultado)
```

Para un lote, crea un solo cliente con `crear_cliente()` y pásalo como `clasificar(texto, cliente=cliente)`.

### Próxima fase: Gmail

1. Leer un lote pequeño con acceso de solo lectura.
2. Clasificar asunto y cuerpo, sin procesar adjuntos.
3. Guardar el identificador del mensaje y el resultado para evitar duplicados.
4. Revisar la precisión antes de aplicar etiquetas o programar ejecuciones.
