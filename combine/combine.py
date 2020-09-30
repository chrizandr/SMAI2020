"""Combine parts of assignment into a big assignment."""
import json
import pdb
import os
from tqdm import tqdm


folders = ["quiz_1_part_3_2020-09-23T17:36:05+05:30", "quiz_1_part_4_2020-09-30T14:52:55+05:30",
           "quiz_1_part_1_2020-09-30T14:41:06+05:30", "quiz_1_part_2_2020-09-30T14:51:58+05:30"]

start_time = "2020-09-30T18:30:15+05:30"
end_time = "2020-09-30T19:30:15+05:30"

if __name__ == "__main__":
    final_json = {
                      "title": "Quiz",
                      "code": "quiz1",
                      "number": 1,
                      "description": "Quiz ",
                      "questions": [],
                      "quiz": True
    }

    q_count = []
    for i, f in enumerate(folders):
        with open(os.path.join(f, "assignment.json")) as fobj:
            assignment_json = json.load(fobj)
        zero_flag = 0
        for q in tqdm(assignment_json["questions"]):

            vals = q["image"].strip(".png").split("-")
            version, number = int(vals[2].strip(".pdf")), int(vals[3]) + 1
            q_code = "q-{}-{}-{}".format(i, version, number)
            new_name = q_code + ".png"
            if version == 0 and i == 0:
                if zero_flag != 0:
                    continue
                zero_flag = 1
            # Move image file from quiz to combined
            os.rename(os.path.join(f, q["image"]), os.path.join("combined/", new_name))

            q["title"] = "Quiz 1, Question"
            q["number"] = (i*5) + number
            q["description"] = "Quiz 1, Question {}".format((i*5) + number)
            q["start_time"] = start_time
            q["end_time"] = end_time
            q["code"] = q_code
            q["image"] = new_name

            final_json["questions"].append(q)

        with open(os.path.join("combined/", "assignment.json"), "w") as fobj:
            fobj.write(json.dumps(final_json, indent=4, sort_keys=True))
