#!/usr/bin/env bash
# Regenerate the synthetic Massachusetts population and the MA facility extracts.
# You do NOT need this to run the demo: the extracts are already in ml/data/.
#
#   bash synthea/generate.sh            # 3,000 residents (~5 min)
#   POPULATION=20000 bash synthea/generate.sh   # tighter rural estimates (~25 min)
#
# Needs Java 17+ (java -version) and Python with ml/requirements.txt installed.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
POPULATION="${POPULATION:-3000}"
SEED="${SEED:-20261024}"
REFERENCE_DATE="${REFERENCE_DATE:-20261024}"   # keep in sync with REFERENCE_DATE in ml/src/massachusetts.py
JAR="$HERE/synthea-with-dependencies.jar"
OUT="$HERE/output"

if [ ! -f "$JAR" ]; then
  echo "Downloading Synthea (~200 MB)..."
  curl -L -o "$JAR" https://github.com/synthetichealth/synthea/releases/download/master-branch-latest/synthea-with-dependencies.jar
fi

echo "Generating $POPULATION living Massachusetts residents..."
java -jar "$JAR" -s "$SEED" -cs "$SEED" -r "$REFERENCE_DATE" -p "$POPULATION" Massachusetts \
  --exporter.baseDirectory="$OUT" \
  --exporter.csv.export=true \
  --exporter.csv.included_files=patients.csv,encounters.csv,conditions.csv,organizations.csv,payers.csv,providers.csv,payer_transitions.csv \
  --exporter.fhir.export=false --exporter.hospital.fhir.export=false --exporter.practitioner.fhir.export=false \
  --exporter.years_of_history=3

echo "Fetching Synthea's MA primary-care site list and MassGIS hospitals..."
curl -sSL -o "$HERE/primary_care_facilities.csv" \
  https://raw.githubusercontent.com/synthetichealth/synthea/master/src/main/resources/providers/primary_care_facilities.csv
curl -sSL -o "$HERE/massgis_hospitals.json" \
  "https://arcgisserver.digital.mass.gov/arcgisserver/rest/services/AGOL/Hospitals/MapServer/0/query?where=1%3D1&outFields=*&returnGeometry=true&outSR=4326&f=json"

python "$ROOT/ml/src/massachusetts.py" prepare \
  --synthea-dir "$OUT/csv" \
  --providers-csv "$HERE/primary_care_facilities.csv" \
  --massgis-json "$HERE/massgis_hospitals.json"
python "$ROOT/ml/src/massachusetts.py" analyze
echo "Done. Restart the backend and click 'Reset demo' to load the new patients."
