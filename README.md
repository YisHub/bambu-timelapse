# 📸 Bambu Timelapse

Dispara automáticamente la cámara de tu celular Android en cada cambio de capa de tu Bambu Lab — sin hardware adicional.

![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker) ![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python) ![License](https://img.shields.io/badge/license-MIT-green)

---

## ¿Cómo funciona?

```
Bambu Lab  ──MQTT local──▶  Script (Docker)  ──HTTP POST──▶  Celular (MacroDroid)  ──▶  📷
 (LAN)       capa nueva        detecta                          dispara foto
```

La impresora expone un servidor MQTT local que transmite el estado en tiempo real. El script se conecta y cada vez que detecta un cambio de capa envía una señal HTTP al celular para sacar una foto.

> No hace falta activar el modo "Solo LAN" — la impresora corre MQTT local y cloud simultáneamente.

---

## Requisitos

**PC / servidor:**
- [Docker](https://docs.docker.com/engine/install/) instalado y corriendo
- En la misma red WiFi que la impresora

**Celular:**
- Android (probado con Samsung Galaxy A53)
- App [MacroDroid](https://play.google.com/store/apps/details?id=com.arlosoft.macrodroid) (gratis)
- En la misma red WiFi que la PC

> **Windows**: ver [sección Windows](#windows-wsl2) al final.

---

## Paso 1 — Datos de la impresora

En la pantalla táctil de la Bambu anotá tres datos:

### Serial Number
**Settings → Dispositivo → SN de la Impresora**
```
Ej: 03919D573008914
```

### IP y Access Code
**Settings → Red → Sólo LAN**
```
IP:               192.168.2.48
Código de acceso: 28957881
```
> El toggle "Modo solo LAN" puede quedar apagado — no es necesario activarlo.

---

## Paso 2 — MacroDroid en el celular

### Habilitar servidor HTTP
1. Abrí MacroDroid
2. Menú **☰ → Sistema → Servidor HTTP** → activar toggle
3. Anotá el puerto (por defecto `8080`)

### Crear la macro
1. Tap **+** → nombre: `timelapse`
2. **Trigger → Conectividad → HTTP Server Request**
   - Method: `Any`
   - Path: `/timelapse`
3. **Action → Cámara → Tomar Foto**
   - Cámara: trasera · Flash: off · Guardar: DCIM
4. Guardar → toggle en verde ✅

### Evitar que Android mate la app
**Ajustes del celu → Aplicaciones → MacroDroid → Batería → Sin restricciones**

### Obtener la IP del celular
**Ajustes → WiFi → (tu red) → Detalles → Dirección IP**
```
Ej: 192.168.2.150
```

---

## Paso 3 — Configuración

```bash
git clone https://github.com/YisHub/bambu-timelapse.git
cd bambu-timelapse

cp .env.example .env
nano .env
```

```env
PRINTER_IP=192.168.2.48         # IP de la impresora
SERIAL_NUMBER=03919D573008914   # Serial (Settings → Dispositivo)
ACCESS_CODE=28957881            # Código de acceso (Settings → Red → Sólo LAN)

PHONE_IP=192.168.2.150          # IP del celular
MACRODROID_PORT=8080
MACRODROID_PATH=/timelapse

LAYER_DELAY_SEC=1.5             # Segundos a esperar antes de disparar
```

**`LAYER_DELAY_SEC`**: tiempo entre el cambio de capa y la foto. Con `1.5` la cabeza suele haberse movido al borde. Aumentalo si tu impresora es lenta o si querés más margen.

---

## Paso 4 — Probar antes de imprimir

```bash
# Verificá que MacroDroid responda
curl -X POST http://192.168.2.150:8080/timelapse
```

Si el celular saca una foto → ✅ todo listo.

---

## Paso 5 — Ejecutar

```bash
# Construir imagen (solo la primera vez)
docker compose build

# Correr (dejá la terminal abierta mientras imprimís)
docker compose up
```

Verás los logs en tiempo real:
```
10:23:01  INFO  Conectado al MQTT de la Bambu Lab
10:25:14  INFO  Nueva capa: 1/142
10:25:16  INFO  Foto disparada — capa 1/142  (HTTP 200)
10:27:33  INFO  Nueva capa: 2/142
10:27:34  INFO  Foto disparada — capa 2/142  (HTTP 200)
```

Para detener: `Ctrl+C`

```bash
# Alternativa: correr en background
docker compose up -d
docker compose logs -f   # ver logs
docker compose down      # detener
```

---

## Tip: Park nozzle en Bambu Studio

Para timelapse más limpio, activá en el slicer:  
**Perfil de impresión → Timelapse → "Park nozzle when taking timelapse"**

La cabeza se mueve a una posición fija antes de cada capa — las fotos quedan sin el nozzle tapando la pieza.

---

## Armar el video

Las fotos quedan en la galería del celular (DCIM). Para convertirlas a video:

**FFmpeg (recomendado):**
```bash
# Copiar fotos al equipo, luego:
ffmpeg -framerate 24 -pattern_type glob -i '*.jpg' \
       -c:v libx264 -pix_fmt yuv420p timelapse.mp4
```

**Apps mobile:** CapCut · VN · InShot → importar como secuencia de imágenes.

**Desktop:** DaVinci Resolve → File → Import → Image Sequence.

---

## Solución de problemas

| Problema | Causa probable | Solución |
|---|---|---|
| `curl: (7) Failed to connect` | Servidor HTTP de MacroDroid apagado | Menú ☰ → Sistema → Servidor HTTP → activar |
| Fotos sin respuesta después de un rato | Samsung mató MacroDroid | Batería → Sin restricciones |
| `Error de conexión MQTT: código 5` | Access code incorrecto | Verificarlo en Settings → Red → Sólo LAN |
| `Error de conexión MQTT: código 4` | IP incorrecta o impresora apagada | `ping 192.168.2.48` para verificar |
| La cabeza aparece en las fotos | Delay muy corto | Aumentar `LAYER_DELAY_SEC` a `3.0` |

---

## Estructura del proyecto

```
bambu-timelapse/
├── bambu_timelapse.py          # Script principal
├── Dockerfile
├── docker-compose.yml
├── requirements_timelapse.txt
├── .env.example                # Plantilla ← compartir esto
└── .env                        # Tu config  ← NO subir a git
```

---

## Windows (WSL2)

<details>
<summary>Expandir instrucciones para Windows</summary>

1. Instalá [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Docker Desktop → Settings → Resources → WSL Integration → activá tu distro
3. Abrí una terminal WSL:

```bash
cd /mnt/c/Users/TuUsuario/ruta/bambu-timelapse
```

4. Todos los comandos son idénticos a Linux.

</details>
