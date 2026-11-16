# IMPERIO CALAVERIIX LIVE

Integración de OBS Studio con el bot de Discord.

## Qué hace

- Consulta OBS Studio por WebSocket cada 20 segundos.
- Detecta el inicio y el fin de una transmisión.
- Publica un embed de inicio y otro de cierre en el canal configurado.
- Puede mencionar un rol al comenzar.
- Incluye los comandos slash `/liveestado` y `/liveanunciar`.
- Si OBS no está disponible, el resto del bot puede seguir funcionando.

## 1. OBS Studio

En OBS abre **Herramientas → Ajustes del servidor WebSocket** (el nombre puede variar según versión):

1. Activa el servidor WebSocket.
2. Usa el puerto `4455` o el que hayas configurado.
3. Define una contraseña y guárdala como variable `OBS_PASSWORD`.
4. Permite conexiones desde el equipo donde se ejecuta el bot.

**Importante:** si el bot está alojado fuera de tu PC (por ejemplo, Wispbyte), `127.0.0.1` apunta al servidor del bot, no a tu ordenador. En ese caso OBS no será accesible directamente por localhost. Necesitarás una conexión privada segura entre ambos equipos (VPN/túnel privado); no expongas el puerto 4455 directamente a Internet.

## 2. Variables de entorno del hosting

Añade estas variables en el panel del hosting. No publiques la contraseña ni la pegues en Discord.

```env
OBS_HOST=127.0.0.1
OBS_PORT=4455
OBS_PASSWORD=TU_CONTRASENA_WEBSOCKET
LIVE_ANNOUNCE_CHANNEL_ID=ID_DEL_CANAL_DE_ANUNCIOS
LIVE_ROLE_ID=ID_DEL_ROL_OPCIONAL
TWITCH_URL=https://twitch.tv/TU_USUARIO
KICK_URL=
YOUTUBE_URL=
```

- `LIVE_ANNOUNCE_CHANNEL_ID`: canal donde se publican los avisos.
- `LIVE_ROLE_ID`: opcional; rol que se menciona al comenzar.
- Las URLs de plataformas son opcionales; deja vacías las que no uses.
- Si no quieres mencionar un rol, deja `LIVE_ROLE_ID` vacío.

## 3. Discord

El bot necesita permiso para ver el canal, enviar mensajes, insertar enlaces y mencionar el rol (si se usa). El rol del bot debe estar autorizado para mencionar ese rol.

## 4. Comandos

- `/liveestado`: comprueba la conexión con OBS e indica si está transmitiendo.
- `/liveanunciar`: publica manualmente el aviso; requiere permiso **Administrar servidor**.

## 5. Instalación

La dependencia `obsws-python` ya está añadida a `requirements.txt`. Al desplegar esta rama, el hosting debe reinstalar dependencias y reiniciar el bot. Los comandos slash se sincronizan al iniciar.

## Limitación conocida

Esta primera versión detecta el estado de transmisión de OBS. No lee eventos de chat de Twitch/Kick/YouTube ni controla escenas de OBS. Social Stream Ninja (puerto 4456) queda para una segunda fase.

## 6. Social Stream Ninja -> Discord

El puente recibe los mensajes de chat por el WebSocket alojado oficial de Social Stream Ninja y los reenvía a un canal de Discord dedicado. El bot puede estar en Wispbyte; no necesita abrir el puerto local 4456.

### Configuración en Social Stream Ninja

1. Abre Social Stream Ninja y entra en **Global settings and tools → Mechanics - Connections & Integrations**.
2. Activa **Enable remote API control of extension**.
3. Activa **Send chat messages to API server** (tercer interruptor).
4. Copia el Session ID de tu URL generada de Dock/overlay. Trátalo como secreto: no lo publiques.

### Variables del hosting

```env
SSN_SESSION_ID=TU_SESSION_ID
SSN_DISCORD_CHANNEL_ID=ID_DEL_CANAL_CHAT
```

El canal debe ser un canal de texto privado o dedicado, con permisos de ver canal y enviar mensajes para el bot. Usa un canal separado del canal de anuncios para no mezclar mensajes.

### Comando de diagnóstico

- `/ssnestado`: indica si el puente está conectado. Si pierde conexión, intenta reconectar automáticamente cada 10 segundos.

### Seguridad y comportamiento

- El puente solo escucha mensajes (canal 4); no envía comandos ni mensajes a tus plataformas.
- Los mensajes se publican como embeds y las menciones de Discord están desactivadas para evitar pings maliciosos.
- Se limita la longitud de los mensajes y se evita reenviar IDs duplicados recientes.
- No compartas el Session ID en capturas, repositorios o chats públicos.
- No necesitas habilitar el servidor local de SSN ni abrir el puerto 4456 para este modo: utiliza el WebSocket alojado oficial.

Documentación oficial: https://socialstream.ninja/docs/commands.html (sección Server API / Receiving Chat Messages).
