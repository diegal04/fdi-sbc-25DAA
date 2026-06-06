#!/usr/bin/env bash

if [[ $# -lt 1 ]]; then
    echo "Uso: $0 GUION_TEST [Sí] [No] [prompt] [flags]"
    exit 1
fi

# parametros ejecucion
GUION="$1"         # el script de test
TRUE=${2:-"Sí"}    # lo que dice el programa para "top" (unificación única sin sustituciones)
FALSE=${3:-"No"}   # lo que dice el programa para "bottom" (fallo unificación)
PROMPT=${4:-">"}   # por si acaso el prompt es distinto
FLAGS="$5"         # banderas opcionales (ej. modo test)

# parametros internos
REPL_CMD="uv run python -u -m sbc.cli $FLAGS"
SLEEP=0.1
TIMEOUT=0.1

# fifo para comunicacion con proceso

IN=$(mktemp -u)
OUT=$(mktemp -u)
ERR=/dev/null
mkfifo "$IN" "$OUT"

# creamos proceso, redirigimos salida y limpiamos

$REPL_CMD <"$IN" >"$OUT" 2>"$ERR" &
REPL_PID=$!

exec 3>"$IN"
exec 4<"$OUT"

cleanup() {
    kill $REPL_PID 2>/dev/null
    rm -f "$IN" "$OUT"
}
trap cleanup EXIT

# funciones interaccion
send() {
    echo "$@" >&3
}

skip_all() {
    sleep $SLEEP
    while read -r -t $TIMEOUT line <&4; do
        :
    done
}

read_all() {
    sleep $SLEEP
    while read -r -t $TIMEOUT line <&4; do
        if [[ "$line" == "$PROMPT"* || "$line" == ""* ]]; then
            :
        else
            echo "$line"
        fi
    done
}

ignorar() {
    send $1
    skip_all
}

TOTAL=0
PUNTOS=0

comprobar() {
    send $1
    RET=$(read_all)
    if [[ "$2" == T ]]; then
        RESP=$TRUE
    elif [[ "$2" == F ]]; then
        RESP=$FALSE
    elif [[ "$2" == "!"* ]]; then
        echo -e "\n$RET\n$2\n"
        ((TOTAL++))
        return
    else
        RESP="$2"
    fi
    if [[ "$RET" != "$RESP"* ]]; then
        echo -e "\nError en '$1': se esperaba '$RESP', dio: $RET.\n"
    else
        echo -e "✔️ '$1' -> '$RET'"
        ((PUNTOS++))
    fi
    ((TOTAL++))
}

# bucle de correccion

echo -e "# CORRECCION\n"
echo -e "Las respuestas que empiezan por '!' tienen que ser corregidas manualmente. Los fallos serán revisados por si acaso es cuestión de formato.\n"

skip_all # mensajes de saludo etc.

while IFS= read -r line; do
    if [[ -z "$line" ]]; then
        if [[ -n "$pregunta" ]]; then
            ignorar "$pregunta"
        fi
        pregunta=""
    elif [[ "$line" == "#"* ]]; then
        :
    elif [[ -n "$pregunta" ]]; then
        comprobar "$pregunta" "$line"
    else
        pregunta="$line"
    fi
done <"$GUION"

echo -e "\n## TOTAL\n\n$PUNTOS/$TOTAL"