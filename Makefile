ifeq (question,$(firstword $(MAKECMDGOALS)))
  # use the rest as arguments for "run"
  Q_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(Q_ARGS):;@:)
endif

num_versions = 4
output = latex/
roll_nums = smai_students2.csv
timestamp = $$(date --iso-8601=seconds)

quiz = True
part = 4
# assignment = assignment
assignment = quiz

sample = 0

question_file = quiz/2/p4.tex
assignment_id = 1
start_time = 2020-09-30T19:15:15+05:30
end_time = 2020-09-30T19:30:15+05:30

shuffle_question = True
shuffle_options = True
# shuffle_list = 0 1 2 3 4
shuffle_list = -1

all: create-build clean parse key images package backup

create-build:
	mkdir -p build

beamer:
	for f in latex/main*.tex; do \
		xelatex -output-directory build/ $$f; \
	done

clean: clean-build clean-latex
	rm -rf assignment.zip quiz.zip

clean-build:
	rm -f build/*.pdf build/*.out build/*.aux build/*.log build/*.toc build/*.nav build/*.snm
	rm -rf build/images

clean-latex:
	rm -rf latex/*.tex
	rm -rf latex/*.json
	rm -rf latex/*.csv

images: beamer
	rm -rf build/images
	mkdir -p build/images
	for f in build/main*.pdf; do \
  	convert -density 192 build/`basename $$f` -quality 100 build/images/`basename $$f`-%d.png; \
  done

key:
	for f in latex/*key*.tex; do \
		xelatex -output-directory build/ $$f; \
	done

package:
	zip -j "$(assignment).zip" build/images/*.png latex/assignment.json


backup:
	cp "$(assignment).zip" "archive/$(assignment)_$(assignment_id)_$(timestamp).zip"
	for f in build/*key*.pdf; do \
		cp $$f "archive/keys/`basename $$f`_$(timestamp).pdf"; \
	done

parse:
	python3 parser.py --num_versions $(num_versions) --question_file $(question_file) --output $(output) \
	--assignment_id $(assignment_id) --start_time $(start_time) --end_time $(end_time) --roll_nums $(roll_nums) \
	--shuffle_question $(shuffle_question) --shuffle_list $(shuffle_list) --quiz $(quiz) --part $(part) --sample $(sample) \
	--shuffle_options $(shuffle_options)

sync: clean
	git add .
	git commit -m "Syncing"
	git push origin master

# 1 - 6:30- 6:45
# 2 - 6:45 - 7:00
# 3 - 7:00 - 7:15
# 4 - 7:15 - 7:30
