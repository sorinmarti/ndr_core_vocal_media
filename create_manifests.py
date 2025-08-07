import csv
import os
import json
from collections import defaultdict

# Input and output paths
csv_path = "Akten_Gesamtübersicht.csv"
output_dir = "mmma_manifests"
base_iiif_url = "https://dhlab-mmma.dhlab.unibas.ch/iiif/iiif/2/"

os.makedirs(output_dir, exist_ok=True)

# Step 1: Group scans by AkteNummer
grouped = defaultdict(list)

with open(csv_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=';')
    for row in reader:
        akte = row['AkteNummer'].strip()
        scan = row['Akte_Scan'].strip()
        grouped[akte].append(scan)

# Step 2: Create IIIF manifests
for akte_nummer, scans in grouped.items():
    manifest = {
        "@context": "http://iiif.io/api/presentation/2/context.json",
        "@type": "sc:Manifest",
        "@id": f"{base_iiif_url}akte_{akte_nummer}/manifest.json",
        "label": f"Akte {akte_nummer}",
        "sequences": [{
            "@type": "sc:Sequence",
            "canvases": []
        }]
    }

    for idx, scan in enumerate(scans, 1):
        canvas_id = f"{base_iiif_url}{scan}/canvas"
        image_id = f"{base_iiif_url}{scan}/full/full/0/default.jpg"

        canvas = {
            "@type": "sc:Canvas",
            "@id": canvas_id,
            "label": f"Seite {idx}",
            "height": 1000,  # Adjust as needed
            "width": 700,    # Adjust as needed
            "images": [{
                "@type": "oa:Annotation",
                "motivation": "sc:painting",
                "on": canvas_id,
                "resource": {
                    "@type": "dctypes:Image",
                    "@id": image_id,
                    "format": "image/jpeg",
                    "height": 1000,
                    "width": 700
                }
            }]
        }

        manifest["sequences"][0]["canvases"].append(canvas)

    output_path = os.path.join(output_dir, f"{akte_nummer}.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
