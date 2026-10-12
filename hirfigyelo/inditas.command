#!/bin/bash
# ==============================================================================
# Hírfigyelő & Mutáció Tracker - Gyorsindító (macOS)
# Kattints duplán a Finderben az indításhoz!
# ==============================================================================

DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -d "$DIR/hirfigyelo" ]; then
    cd "$DIR/hirfigyelo" || exit 1
else
    cd "$DIR" || exit 1
fi

echo "============================================================"
echo "    Media Framing & Mutation Tracker - Indítópult"
echo "============================================================"
echo ""

# Webes Dashboard ellenőrzése és indítása port 8080-on
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo ">> A Webes Dashboard már fut a háttérben (http://localhost:8080)."
else
    echo ">> Webes Dashboard indítása a háttérben..."
    nohup ./.venv/bin/python3 src/web/app.py > logs/web_app.log 2>&1 &
    sleep 1.5
fi

# Böngésző automatikus megnyitása
echo ">> Webes felület megnyitása a böngészőben..."
open "http://localhost:8080"

echo ""
echo "------------------------------------------------------------"
echo "A webes dashboard megnyílt a böngésződben (http://localhost:8080)!"
echo "------------------------------------------------------------"
echo ""

while true; do
    echo "Válassz egy műveletet:"
    echo "  1) Frissítés futtatása most (Scraping + Matching + Google Sheet)"
    echo "  2) Webes felület újbóli megnyitása a böngészőben"
    echo "  3) Google Sheet megnyitása a böngészőben"
    echo "  4) Kilépés az ablakból (a dashboard szerver futva marad)"
    echo ""
    read -p "Választásod [1-4]: " choice
    case $choice in
        1)
            echo ""
            echo ">> Pipeline futtatása indul..."
            ./.venv/bin/python3 run_pipeline.py
            echo ">> Kész!"
            echo ""
            ;;
        2)
            open "http://localhost:8080"
            ;;
        3)
            open "https://docs.google.com/spreadsheets/d/1h1Or2v-4wayuVQDSO6DjNp90pjJZJvVb08xE9c9b_XY/edit?usp=sharing"
            ;;
        4)
            echo ""
            echo "Viszlát! A webes felület elérhető marad a böngésződben."
            exit 0
            ;;
        *)
            echo "Kérlek 1 és 4 közötti számot adj meg."
            ;;
    esac
done
