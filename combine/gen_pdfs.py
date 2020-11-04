import json
import pdb
import pandas as pd
import os
from tqdm import tqdm


if __name__ == "__main__":
    img_folder = "/home/chris/SMAI2020/build/images/"
    output_path = "/home/chris/SMAI2020/combine/combined/"
    json_path = "/home/chris/SMAI2020/latex/"
    data = pd.read_csv("/home/chris/SMAI2020/smai_students2.csv")

    with open(os.path.join(json_path, "assignment.json")) as fobj:
        assignment_json = json.load(fobj)

    rolls = pd.Series(data["Roll No."].values, index=data["Email ID"]).to_dict()
    print_json = {}

    for q in assignment_json["questions"]:
        for s in q["students"]:
            if rolls[s] not in print_json:
                print_json[rolls[s]] = []
            print_json[rolls[s]].append(q["image"])

    with open("convert.sh", "w") as f:
        for pdf in print_json:
            imgs = sorted(print_json[pdf], key=lambda s: int(s.split("-")[2].strip(".pdf")))
            imgs = [os.path.join(img_folder, x) for x in imgs]
            output = "convert " + " ".join(imgs) + " " + os.path.join(output_path, str(pdf) + ".pdf")
            f.write(output + "\n")
