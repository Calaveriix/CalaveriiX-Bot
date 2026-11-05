# CalaveriiX Bot MAX

Bot Discord con utilidades, moderación, economía, tickets y música con botones.

## Música
Comandos slash:
- `/play cancion:` busca/reproduce o agrega a la cola
- `/skip`
- `/queue`
- `/musicpanel` publica controles Pausar / Seguir / Saltar / Detener

La música requiere un servidor **Lavalink v4** independiente y las variables:
- `LAVALINK_URI` (ej. dirección de tu servidor Lavalink)
- `LAVALINK_PASSWORD`

Para búsquedas de YouTube, Lavalink debe tener instalado y configurado el plugin de YouTube compatible. Lavalink no viene incluido en este repositorio ni se ejecuta automáticamente en Railway.

## Variables del bot
- `DISCORD_TOKEN` obligatoria
- `BOT_PREFIX` opcional (por defecto `!`)
- `PORT` opcional (por defecto `8080`)
- `DATABASE_PATH` opcional

## Ejecutar
`pip install -r requirements.txt`
`python main.py`

Los comandos slash se sincronizan al iniciar; la propagación global de Discord puede tardar un poco.

## Funciones
Utilidad, encuestas, economía, tienda/inventario, juegos, tickets/transcripts, moderación, warnings, welcome/logs, autorole, niveles/leaderboard, sorteos, sugerencias, automod, reaction roles, panel admin, SQLite y healthcheck.
