import pdb
import argparse
import os
import random
import string
import json
import pandas as pd
import numpy as np


class Assignment(object):
    def __init__(self, question_file, id_, output, start_time, end_time, roll_nums):
        self.content = open(question_file, "r").read()
        self.id_ = id_
        self.questions = []
        self.output = output
        self.start_time = start_time
        self.end_time = end_time
        self.roll_nums = roll_nums
        self._parse_doc()

    def _parse_doc(self):
        frame_flag = False
        enum_flag = False
        q_obj = None

        for l in self.content.split("\n"):
            if "\\section{}" in l:
                continue

            elif "\\begin{frame}" in l:
                frame_flag = True
                q_obj = Question()

            elif "\\end{frame}" in l:
                frame_flag = False
                self.questions.append(q_obj)

            elif "\\begin{enumerate}" in l:
                enum_flag = True

            elif "\\end{enumerate}" in l:
                enum_flag = False

            else:
                if frame_flag and not enum_flag:
                    q_obj.add_content(l)
                elif frame_flag and enum_flag:
                    if "\\item" in l:
                        q_obj.add_options(l, "% Ans" in l)
                else:
                    continue

    def gen_versions(self, num_versions):
        assignment = self._gen_json()
        self.split_rolls(num_versions)
        for copy_id in range(num_versions):
            frames = []
            random.shuffle(self.questions)
            doc_name = "main-{}-{}.tex".format(self.id_, copy_id)
            q_name = "q-{}-{}.tex".format(self.id_, copy_id)

            for q_num, q in enumerate(self.questions):
                q.randomize()
                frames.append(q.pprint())
                assignment["questions"].append(q.json(self.id_, q_num, copy_id, doc_name, self.start_time, self.end_time))

            self._gen_question_doc(q_name, frames)
            self._gen_main_doc(doc_name, q_name)
        print("Generated {} versions of Assignment {}".format(num_versions, self.id_))
        with open(os.path.join(self.output, "assignment.json"), "w") as f:
            f.write(json.dumps(assignment, indent=4))
        print("Metadata added to %s" % os.path.join(self.output, "assignment.json"))

    def _gen_json(self):
        s = {
            "title": "Test RQ",
            "code": "trq{}".format(self.id_),
            "number": self.id_,
            "description": "Bulk uploaded assignment for class review",
            "questions": []
        }
        return s

    def split_rolls(self, num_versions):
        data = pd.read_csv(self.roll_nums)
        emails = [x for x in data["Email ID"]]
        random.shuffle(emails)

        idx = np.linspace(0, len(emails), num_versions+1)

        for copy_id in range(num_versions):
            fname = "rolls-{}-{}.csv".format(self.id_, copy_id)
            with open(os.path.join(self.output, fname), "w") as f:
                f.write(",\n".join(emails[int(idx[copy_id]): int(idx[copy_id+1])]) + ",")
        print("Split roll numbers into {} groups".format(num_versions))

    def _gen_main_doc(self, doc_name, q_name):
        content = "\\documentclass[aspectratio=43]{beamer}\n" +\
                  "\\usepackage{styles/common}\n" +\
                  "\\usepackage{styles/beamer-section}\n" +\
                  "\\usepackage{enumitem}\n" +\
                  "\\setbeamertemplate{navigation symbols}{}\n" +\
                  "\\begin{document}\n" +\
                  "\\input{%s}\n" +\
                  "\\end{document}"

        with open(os.path.join(self.output, doc_name), "w") as f:
            f.write(content % os.path.join(self.output, q_name))

    def _gen_question_doc(self, q_name, frames):
        content = "\n".join(frames)
        with open(os.path.join(self.output, q_name), "w") as f:
            f.write(content)


class Question(object):
    def __init__(self):
        self.content = ""
        self.options = []

    def add_content(self, c):
        self.content += c + "\n"

    def add_options(self, item, is_true=False):
        self.options.append(Option(item, is_true))

    def randomize(self):
        random.shuffle(self.options)
        return None

    def pprint(self):
        content = "\\begin{frame}\n" +\
                  "\\section{}\n" +\
                  "%s \n" +\
                  "\\begin{enumerate}[label=(\\Alph*)]\n" +\
                  "%s \n" +\
                  "\\end{enumerate}\n" +\
                  "\\end{frame}\n"

        content = content % (self.content, "\n".join([str(x) for x in self.options]))
        return content

    def json(self, assign_id, q_num, copy_id, doc_name, start_time, end_time):
        s = {
            "title": "Review question",
            "number": q_num + 1,
            "code": "q_{}_{}_{}".format(assign_id, copy_id, q_num),
            "description": "Answer the question",
            "start_time": start_time,
            "end_time": end_time,
            "tas": [
                "cvit.office@research.iiit.ac.in"
            ],
            "image": "{}-{}.png".format(doc_name.replace(".tex", ".pdf"), q_num),
            "marks": 1,
            "options": [x.json(i) for i, x in enumerate(self.options)]
        }
        return s


class Option(object):
    def __init__(self, content, is_true):
        self.content = content
        self.is_true = is_true

    def __repr__(self):
        return self.content.strip()

    def __str__(self):
        return self.content.strip()

    def json(self, id_):
        s = {
            "name": "Option {}".format(string.ascii_uppercase[id_]),
            "correct": self.is_true
        }
        return s


def make_assignment(args):
    assignment = Assignment(args.question_file,
                            args.assignment_id,
                            args.output,
                            args.start_time,
                            args.end_time,
                            args.roll_nums)
    assignment.gen_versions(args.num_versions)
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate variations of the questions')
    parser.add_argument('--num_versions', default=3, type=int, help='Number of versions to generate')
    parser.add_argument('--question_file', default="questions/sample.tex", type=str, help='File containing the questions')
    parser.add_argument('--output', default="latex/", help="Path to output folder")
    parser.add_argument('--assignment_id', default=0, type=int, help="Assignment number")
    parser.add_argument('--start_time', type=str, help="Start time")
    parser.add_argument('--end_time', type=str, help="End time")
    parser.add_argument('--roll_nums', default="rolls.csv", type=str, help="CSV containing the roll number and emails of students")
    args = parser.parse_args()

    make_assignment(args)
