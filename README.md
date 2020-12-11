# Cobalt Build System
Simple, minimalistic build system for C projects which uses Modules for custom dependencies.

## How to use
1. Create a new project using:
```git
cobalt new my-awesome-game
```

2. Modify the project file, i.e Cobalt.json:
```json
{
    "id": "my-awesome-game",
    "type": "application",
    "src": [ "main.c", "game.c", "player.c", "evil_enemy.c" ]
}
```

3. And then built the project using:
```git
cobalt build
```
