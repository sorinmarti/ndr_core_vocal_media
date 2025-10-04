import csv
import os
import json
from collections import defaultdict

import pandas as pd
from PIL import Image

# Input and output paths
csv_path = "source_document_cards.csv"
output_dir = "manifests"
base_iiif_url = "https://bscc.philhist.unibas.ch/iiif/2/"

df = pd.read_csv(csv_path, sep=",")

os.makedirs(output_dir, exist_ok=True)
img_dir = "C:\\Users\\sorin\\PycharmProjects\\companycards\\images"
image_list = os.listdir(img_dir)

for index, row in df.iterrows():
    manifest = {
        "@context": "http://iiif.io/api/presentation/2/context.json",
        "@type": "sc:Manifest",
        "@id": f"{base_iiif_url}id-{row['id']}/manifest.json",
        "label": f"{row['year']}: {row['title']}",
        "sequences": [{
            "@type": "sc:Sequence",
            "canvases": []
        }]
    }

    images = [img for img in image_list if f"_{row['subcollection']}_" in img]
    images.sort(key=lambda x: int(x.split("_")[-1].split(".")[0]))

    iiif_manifest_page_id = 1
    for img in images:
        canvas_id = f"{base_iiif_url}{img}/canvas"
        image_id = f"{base_iiif_url}{img}/full/full/0/default.jpg"

        with Image.open(os.path.join(img_dir, img)) as img_obj:
            width, height = img_obj.size

        canvas = {
            "@type": "sc:Canvas",
            "@id": canvas_id,
            "label": f"Seite {iiif_manifest_page_id}",
            "height": height,
            "width": width,
            "images": [{
                "@type": "oa:Annotation",
                "motivation": "sc:painting",
                "on": canvas_id,
                "resource": {
                    "@type": "dctypes:Image",
                    "@id": image_id,
                    "format": "image/jpeg",
                    "height": height,
                    "width": width
                }
            }]
        }

        manifest["sequences"][0]["canvases"].append(canvas)
        iiif_manifest_page_id += 1

        output_path = os.path.join(output_dir, f"{row['id']}.manifest.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
