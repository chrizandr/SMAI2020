import pdb
import argparse
import os
import random
import string
import json
import pandas as pd
import numpy as np
import sys
import re


class Assignment(object):
    def __init__(self, question_file, id_, output, start_time, end_time, roll_nums):
        self.id_ = id_
        self.questions = []
        self.output = output
        self.start_time = start_time
        self.end_time = end_time
        self.roll_nums = roll_nums
        self.question_file = question_file
        if question_file.endswith(".tex"):
            self._parse_doc(question_file)

    def _parse_doc(self, question_file):
        self.content = open(question_file, "r").read()
        self.questions = []
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
                    if "% Desc" in l:
                        q_obj.desc = l.replace("% Desc", "")
                    if "% FIB" in l:
                        q_obj.type = "FIB"
                    else:
                        q_obj.add_content(l)
                elif frame_flag and enum_flag:
                    if "\\item" in l:
                        q_obj.add_options(l, "% Ans" in l, "% None" in l)
                else:
                    continue

    def gen_key(self, quiz=False, part=0):
        doc_name = "quiz-{}-part-{}-key.tex".format(self.id_, part) if quiz else "key-{}.tex".format(self.id_)
        q_name = "q_k-{}.tex".format(self.id_)
        frames = []

        for q_num, q in enumerate(self.questions):
            frames.append(q.pprint(key=True))
            self._gen_question_doc(q_name, frames)
            self._gen_main_doc(doc_name, q_name)
        print("Generated key of Assignment {}".format(self.id_))

    def gen_versions(self, num_versions, shuffle_question=True, shuffle_list=None, shuffle_options=True, quiz=False, part=1, sample=0):
        assignment = self._gen_json(quiz)
        if sample >= 0:
            assigned_students, _ = self.split_rolls(num_versions)

            for copy_id in range(num_versions):
                frames = []
                if shuffle_question:
                    if shuffle_list == [-1]:
                        shuffle_list = list(range(len(self.questions)))
                    self._shuffle_questions(shuffle_list)

                doc_name = "main-{}-{}.tex".format(self.id_, copy_id)
                q_name = "q-{}-{}.tex".format(self.id_, copy_id)

                if sample == 0:
                    # Generate [num_versions] sets with random ordering of question and options
                    for q_num, q in enumerate(self.questions):
                        if shuffle_options:
                            q.randomize()
                        if q.type == "MCQ":
                            frames.append(q.pprint())
                            assignment["questions"].append(q.json(self.id_, q_num, copy_id,
                                                           doc_name, self.start_time, self.end_time,
                                                           assigned_students[copy_id], quiz, part))
                elif sample > 0:
                    # Generate [num_versions] groups with random questions of size [sample] from a large set
                    assert sample * num_versions <= len(self.questions)
                    for q_num, q in enumerate(self.questions[copy_id*sample:(copy_id+1)*sample]):
                        if shuffle_options:
                            q.randomize()
                        frames.append(q.pprint())
                        assignment["questions"].append(q.json(self.id_, q_num, copy_id,
                                                              doc_name, self.start_time, self.end_time,
                                                              assigned_students[copy_id], quiz, part))
                self._gen_question_doc(q_name, frames)
                self._gen_main_doc(doc_name, q_name)

            # No versioning for FIB
            fibs = [q for q in self.questions if q.type == "FIB"]
            non_fib = len(self.questions) - len(fibs)
            frames = [q.pprint() for q in fibs]
            if len(frames) > 0:
                doc_name = "main-{}-{}.tex".format("fib", 0)
                q_name = "q-{}-{}.tex".format("fib", 0)
                self._gen_question_doc(q_name, frames)
                self._gen_main_doc(doc_name, q_name)

            all_students = [student for group in assigned_students for student in group]
            assignment["questions"].extend([q.json(self.id_, non_fib + q_num, 0, doc_name, self.start_time,
                                                   self.end_time, all_students, quiz, part, non_fib)
                                            for q_num, q in enumerate(fibs)])

        if sample < 0:
            # Group students into buckets and assign each version of question to one bucket [number of buckets == number of versions]
            files = os.listdir(self.question_file)
            files = sorted(files, key=lambda s: int(s.strip(".tex")))

            for q_num, f in enumerate(files):
                self._parse_doc(os.path.join(self.question_file, f))
                assigned_students, _ = self.split_rolls(len(self.questions))

                frames = []
                doc_name = "main-{}-{}.tex".format(self.id_, q_num)
                q_name = "q-{}-{}.tex".format(self.id_, q_num)
                for copy_id, q in enumerate(self.questions):
                    frames.append(q.pprint())
                    assignment["questions"].append(q.json(self.id_, q_num, copy_id,
                                                   doc_name, self.start_time, self.end_time,
                                                   assigned_students[copy_id], quiz, part))
                self._gen_question_doc(q_name, frames)
                self._gen_main_doc(doc_name, q_name)


        print("Generated {} versions of Assignment {}".format(num_versions, self.id_))
        with open(os.path.join(self.output, "assignment.json"), "w") as f:
            f.write(json.dumps(assignment, indent=4))
        print("Metadata added to %s" % os.path.join(self.output, "assignment.json"))

    def gen_per_student(self, values, quiz, part):
        assignment = self._gen_json(quiz)
        assigned_students, r_nos = self.split_rolls(1)
        for i, r_no in enumerate(r_nos):
            frames = []
            doc_name = "main-{}-{}.tex".format(self.id_, r_no)
            q_name = "q-{}-{}.tex".format(self.id_, r_no)

            v = self.gen_values(values)
            for q_num, q in enumerate(self.questions):
                frames.append(q.pprint(values=v[q_num]))

                assignment["questions"].append(q.json(self.id_, q_num, r_no,
                                                      doc_name, self.start_time, self.end_time,
                                                      [assigned_students[0][i]], quiz, part))

            self._gen_question_doc(q_name, frames)
            self._gen_main_doc(doc_name, q_name)
        print("Generated {} versions of Assignment {}".format(len(r_nos), self.id_))
        with open(os.path.join(self.output, "assignment.json"), "w") as f:
            f.write(json.dumps(assignment, indent=4))
        print("Metadata added to %s" % os.path.join(self.output, "assignment.json"))

    def gen_values(self, values):
        v = []
        for dic in values:
            m = {}
            used = []
            for k in dic:
                type_ = dic[k][0]
                if type_ is int:
                    x = random.randint(*dic[k][1])
                    while x in used:
                        x = random.randint(*dic[k][1])
                    m[k] = x
                    used.append(x)
                elif type_ is float:
                    x = random.uniform(*dic[k][1])
                    while x in used:
                        x = random.uniform(*dic[k][1])
                    m[k] = x
                    used.append(x)
            v.append(m)

        return v

    def _gen_json(self, quiz):
        s = {
            "title": "Quiz" if quiz else "Test RQ",
            "code": "quiz{}".format(self.id_) if quiz else "trq{}".format(self.id_),
            "number": self.id_,
            "description": "Quiz " if quiz else "Bulk uploaded assignment for class review",
            "questions": []
        }
        return s

    def _shuffle_questions(self, shuffle_list):
        if len(shuffle_list) == 0:
            shuffle_list = list(range(len(self.questions)))

        shuffled_indices = shuffle_list.copy()
        random.shuffle(shuffled_indices)
        map = {o: n for o, n in zip(shuffle_list, shuffled_indices)}
        new_order = [self.questions[i] if i not in shuffle_list else self.questions[map[i]]
                     for i in range(len(self.questions))]

        self.questions = new_order

    def split_rolls(self, num_versions):
        data = pd.read_csv(self.roll_nums)
        emails = [x for x in data["Email ID"]]
        r_nos = [x for x in data["Roll No."]]
        rids = np.random.permutation(len(emails))
        emails = [emails[i] for i in rids]
        r_nos = [r_nos[i] for i in rids]

        idx = np.linspace(0, len(emails), num_versions+1)

        assigned_students = []
        for copy_id in range(num_versions):
            assigned_students.append(emails[int(idx[copy_id]): int(idx[copy_id+1])])
        # pdb.set_trace()
        print("Split roll numbers into {} groups".format(num_versions))
        return assigned_students, r_nos

    def _gen_main_doc(self, doc_name, q_name):
        content = "\\documentclass[aspectratio=43]{beamer}\n" +\
                  "\\usepackage{styles/common}\n" +\
                  "\\usepackage{styles/beamer-section}\n" +\
                  "\\usepackage{enumitem}\n" +\
                  "\\usepackage{graphicx}\n" +\
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
        self.desc = ""
        self.type = "MCQ"

    def add_content(self, c):
        self.content += c + "\n"

    def add_options(self, item, is_true=False, is_none=False):
        self.options.append(Option(item, is_true, is_none))

    def randomize(self):
        non_none_values = [x for x in self.options if not x.is_none]
        none_values = [x for x in self.options if x.is_none]
        random.shuffle(non_none_values)
        self.options = non_none_values + none_values

    def fill_values(self, values):
        ignore = ["[!htbp]"]
        placeholders = set([x for x in re.findall(r"\[.*?\]", self.content) if x not in ignore])
        output = self.content
        for k in placeholders:
            e_string = k.replace("[", "").replace("]", "")
            for v in values:
                e_string = e_string.replace(v, "%0.4f" % (values[v]) if type(values[v]) is float else str(values[v]))
            e_val = eval(e_string)
            output = output.replace(k, "%0.4f" % (e_val) if type(e_val) is float else str(e_val))
        return output

    def pprint(self, key=False, values=None):
        if self.type == "MCQ":
            content = "\\begin{frame}[shrink=20]\n" +\
                      "\\section{}\n" +\
                      "%s \n" +\
                      "\\begin{enumerate}[label=(\\Alph*)]\n" +\
                      "%s \n" +\
                      "\\end{enumerate}\n" +\
                      "\\end{frame}\n"
            options = [x.key_version() if key else str(x) for x in self.options]

            if values:
                output = self.fill_values(values)
                options = [x.numeric_version(values) for x in self.options]
                content = content % (output, "\n".join(options))
            else:
                content = content % (self.content, "\n".join(options))
        else:
            content = "\\begin{frame}[shrink=20]\n" +\
                      "\\section{}\n" +\
                      "%s \n" +\
                      "\\end{frame}\n"
            content = content % (self.content)
        return content

    def json(self, assign_id, q_num, copy_id, doc_name, start_time, end_time, assigned_students, quiz=False, part=0, non_fib=0):
        if part > 0:
            title = "Quiz {}, Part {}, Question".format(assign_id, part) if quiz else "Class review {} Question".format(assign_id)
            description = "Quiz {}, Part {}, Question {}".format(assign_id, part, q_num+1) if quiz else "Class review {} Question {}".format(assign_id, q_num+1)

        else:
            title = "Quiz {}, Question".format(assign_id) if quiz else "Class review {} Question".format(assign_id)
            description = "Quiz {}, Question {}".format(assign_id, q_num+1) if quiz else "Class review {} Question {}".format(assign_id, q_num+1)

        description = description + "\n" + self.desc
        code = "q_{}_{}_{}_{}".format(assign_id, part, copy_id, q_num) if quiz else "q_{}_{}_{}".format(assign_id, copy_id, q_num)
        s = {
            "title": title,
            "number": q_num + 1,
            "code": code,
            "type": self.type,
            "description": description,
            "start_time": start_time,
            "end_time": end_time,
            "tas": [
                "cvit.office@research.iiit.ac.in"
            ],
            "image": "{}-{}.png".format(doc_name.replace(".tex", ".pdf"), copy_id if quiz and not part else q_num-non_fib),
            "marks": 1,

            "students": assigned_students
        }
        if self.type == "MCQ":
            s["options"] = [x.json(i) for i, x in enumerate(self.options)]
        return s


class Option(object):
    def __init__(self, content, is_true, is_none):
        self.content = content
        self.is_true = is_true
        self.is_none = is_none

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

    def key_version(self):
        if self.is_true:
            text = self.content.replace("% Ans", "")
            text = text.replace("% None", "")
            text = text.replace("\\item", "")
            content = "\\item \\textbf{[Ans]} %s" % text
            return content
        else:
            return str(self)

    def numeric_version(self, values):
        ignore = ["[!htbp]"]
        placeholders = set([x for x in re.findall(r"\[.*?\]", self.content) if x not in ignore])
        output = self.content
        for k in placeholders:
            e_string = k.replace("[", "").replace("]", "")
            for v in values:
                e_string = e_string.replace(v, "%0.4f" % (values[v]) if type(values[v]) is float else str(values[v]))
            e_val = eval(e_string)
            output = output.replace(k, "%0.4f" % (e_val) if type(e_val) is float else str(e_val))
        return output


def make_assignment(args):
    if args.shuffle_question not in ["True", "False"] or args.quiz not in ["True", "False"] or args.shuffle_options not in ["True", "False"]:
        parser.print_help()
        sys.exit(1)

    shuffle_question = args.shuffle_question == "True"
    shuffle_options = args.shuffle_options == "True"
    quiz = args.quiz == "True"

    assignment = Assignment(args.question_file,
                            args.assignment_id,
                            args.output,
                            args.start_time,
                            args.end_time,
                            args.roll_nums,
                            )

    assignment.gen_key(quiz=quiz, part=args.part)
    assignment.gen_versions(args.num_versions, shuffle_question, args.shuffle_list, shuffle_options, quiz=quiz, part=args.part, sample=args.sample)
    # values = [
    #     {
    #         "m": (int, [2, 6]),
    #         "p": (float, [0.1, 0.9]),
    #     },
    #     {
    #         "w_1": (int, [1, 10]),
    #         "w_2": (int, [1, 10]),
    #         "b_1": (int, [1, 10]),
    #         "b_2": (int, [1, 10]),
    #     },
    #     {
    #         "K": (int, [0, 10])
    #     },
    #     {
    #         "A": (int, [0, 10]),
    #         "B": (int, [0, 10]),
    #         "C": (int, [0, 10]),
    #         "D": (int, [0, 10]),
    #     },
    #     {
    #         "N": (int, [3, 10])
    #     }
    # ]
    # assignment.gen_per_student(values, quiz, args.part)
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate variations of the questions')
    parser.add_argument('--num_versions', default=1, type=int, help='Number of versions to generate')
    parser.add_argument('--question_file', default="questions/sample.tex", type=str, help='File containing the questions')
    parser.add_argument('--output', default="latex/", help="Path to output folder")
    parser.add_argument('--assignment_id', default=0, type=int, help="Assignment number")
    parser.add_argument('--sample', default=0, type=int, help="Questions to sample per set")
    parser.add_argument('--part', default=0, type=int, help="Part number of quiz")
    parser.add_argument('--start_time', type=str, help="Start time")
    parser.add_argument('--end_time', type=str, help="End time")
    parser.add_argument('--roll_nums', default="rolls.csv", type=str, help="CSV containing the roll number and emails of students")
    parser.add_argument('--shuffle_question', default="True", type=str, help="Shuffle question order, [True or False]")
    parser.add_argument('--shuffle_options', default="True", type=str, help="Shuffle options order, [True or False]")
    parser.add_argument('--quiz', default="False", type=str, help="If the assignment is a quiz, [True or False]")
    parser.add_argument('--shuffle_list', default=[], nargs='+', type=int,
                        help='List of questions that can be shuffled, if not given and --shuffle_question is True all will be shuffled')
    args = parser.parse_args()
    make_assignment(args)
