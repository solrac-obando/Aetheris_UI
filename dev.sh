#!/bin/bash
# =============================================================================
# Aetheris UI - Script de Desarrollo
# Uso: ./dev.sh [comando]
# =============================================================================
set -e

# --- Forzar Docker nativo de Linux (NO Docker Desktop) ---
CURRENT_CONTEXT=$(docker context show 2>/dev/null)
if [ "$CURRENT_CONTEXT" != "default" ]; then
    echo "⚠️  Cambiando de Docker Desktop ($CURRENT_CONTEXT) → Docker nativo (default)..."
    docker context use default > /dev/null 2>&1
fi

COMPOSE_FILE="docker-compose.dev.yml"
PROJECT="aetheris-dev"

show_help() {
    echo ""
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║        Aetheris UI - Entorno de Desarrollo          ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo ""
    echo "Uso: ./dev.sh [comando]"
    echo ""
    echo "  build          Construir la imagen de desarrollo"
    echo "  up             Levantar el entorno (shell interactivo)"
    echo "  down           Detener y eliminar el contenedor"
    echo "  restart        Reiniciar el entorno limpio"
    echo "  test           Ejecutar tests rápidos (one-shot)"
    echo "  test-all       Ejecutar TODOS los tests"
    echo "  rust           Compilar el motor Rust (PyO3 → .so)"
    echo "  rust-test      Ejecutar tests de Rust"
    echo "  bench          Ejecutar benchmarks"
    echo "  mypy           Type checking con mypy"
    echo "  web            Iniciar servidor web Flask"
    echo "  plan           Ver archivos de mejora"
    echo "  logs           Ver logs del contenedor"
    echo "  exec [cmd]     Ejecutar comando dentro del contenedor"
    echo "  clean          Eliminar contenedores + caché"
    echo "  clean-all      Eliminar TODO (contenedores + imágenes + volúmenes)"
    echo "  status         Ver estado del entorno"
    echo ""
}

case "${1:-help}" in
    build)
        echo "🔨 Construyendo imagen de desarrollo..."
        docker-compose -f $COMPOSE_FILE build aetheris-dev
        echo "✅ Imagen construida."
        ;;
    up)
        echo "🚀 Levantando entorno de desarrollo..."
        docker-compose -f $COMPOSE_FILE up -d aetheris-dev
        echo "✅ Entorno listo. Conectando..."
        docker-compose -f $COMPOSE_FILE exec aetheris-dev bash
        ;;
    down)
        echo "⏹️  Deteniendo entorno..."
        docker-compose -f $COMPOSE_FILE down
        echo "✅ Entorno detenido."
        ;;
    restart)
        echo "🔄 Reiniciando entorno..."
        docker-compose -f $COMPOSE_FILE down
        docker-compose -f $COMPOSE_FILE up -d aetheris-dev
        echo "✅ Entorno reiniciado. Conectando..."
        docker-compose -f $COMPOSE_FILE exec aetheris-dev bash
        ;;
    test)
        echo "🧪 Ejecutando tests rápidos..."
        docker-compose -f $COMPOSE_FILE run --rm --profile test aetheris-test
        ;;
    test-all)
        echo "🧪 Ejecutando TODOS los tests..."
        docker-compose -f $COMPOSE_FILE run --rm aetheris-dev test
        ;;
    rust)
        echo "🦀 Compilando motor Rust..."
        docker-compose -f $COMPOSE_FILE run --rm --profile rust aetheris-rust-build
        ;;
    rust-test)
        echo "🦀 Tests de Rust..."
        docker-compose -f $COMPOSE_FILE run --rm aetheris-dev rust-test
        ;;
    bench)
        echo "📊 Benchmarks..."
        docker-compose -f $COMPOSE_FILE run --rm aetheris-dev bench
        ;;
    mypy)
        echo "🔍 Type checking..."
        docker-compose -f $COMPOSE_FILE run --rm aetheris-dev mypy
        ;;
    web)
        echo "🌐 Servidor web en http://localhost:8000..."
        docker-compose -f $COMPOSE_FILE run --rm -p 8000:8000 aetheris-dev web
        ;;
    plan)
        echo "📋 Archivos de mejora:"
        echo ""
        ls -1 planning/*.md 2>/dev/null | while read f; do
            title=$(head -1 "$f" | sed 's/^#\+ //')
            printf "  %-50s  %s\n" "$f" "$title"
        done
        echo ""
        ;;
    logs)
        docker-compose -f $COMPOSE_FILE logs -f aetheris-dev
        ;;
    exec)
        shift
        docker-compose -f $COMPOSE_FILE exec aetheris-dev "$@"
        ;;
    clean)
        echo "🧹 Limpiando contenedores..."
        docker-compose -f $COMPOSE_FILE down --remove-orphans
        echo "✅ Limpio."
        ;;
    clean-all)
        echo "🧹 Limpiando TODO (contenedores + imágenes + volúmenes)..."
        docker-compose -f $COMPOSE_FILE down --rmi all --volumes --remove-orphans
        echo "✅ Todo eliminado."
        ;;
    status)
        echo "📊 Estado del entorno:"
        echo ""
        echo "Docker context: $(docker context show)"
        echo "Docker daemon:  $(docker info --format '{{.ServerVersion}}' 2>/dev/null || echo 'No disponible')"
        echo ""
        docker-compose -f $COMPOSE_FILE ps 2>/dev/null || echo "No hay servicios activos."
        echo ""
        echo "Volúmenes de caché:"
        docker volume ls --filter name=aetheris 2>/dev/null
        ;;
    help|*)
        show_help
        ;;
esac
