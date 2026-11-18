#!/usr/bin/env bash
# OSRM uchun O'zbekiston xaritasini yuklab, qayta ishlaydi (ko'cha nomi uchun).
# Birinchi o'rnatishda va xaritani yangilash uchun (oyiga bir marta) ishga tushiring:
#   cd /opt/davomat/davomat && sudo bash deploy/osrm-prepare.sh && sudo docker compose restart osrm
set -euo pipefail

cd "$(dirname "$0")/.."
DATA_DIR="$(cd .. && pwd)/osrm-data"
IMAGE="ghcr.io/project-osrm/osrm-backend:v6.0.0"
PBF_URL="https://download.geofabrik.de/asia/uzbekistan-latest.osm.pbf"
NAME="uzbekistan-latest"

mkdir -p "$DATA_DIR"
TMP_DIR="$(mktemp -d "$DATA_DIR/.build.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT

echo ">> Xarita yuklanmoqda: $PBF_URL"
curl -fL --retry 3 -o "$TMP_DIR/$NAME.osm.pbf" "$PBF_URL"

run() { docker run --rm -v "$TMP_DIR:/data" "$IMAGE" "$@"; }

echo ">> osrm-extract"
run osrm-extract -p /opt/car.lua "/data/$NAME.osm.pbf"
echo ">> osrm-partition"
run osrm-partition "/data/$NAME.osrm"
echo ">> osrm-customize"
run osrm-customize "/data/$NAME.osrm"

# Tayyor fayllarni bir martada almashtiramiz (ishlab turgan osrm restartgacha eskisini ishlatadi)
rm -f "$TMP_DIR/$NAME.osm.pbf"
find "$DATA_DIR" -maxdepth 1 -type f -name "$NAME.osrm*" -delete
mv "$TMP_DIR"/"$NAME".osrm* "$DATA_DIR"/
echo ">> Tayyor: $DATA_DIR"
ls -lh "$DATA_DIR"
