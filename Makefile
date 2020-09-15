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

question_file = questions/q11.tex
assignment_id = 12
start_time = 2020-09-16T09:00:15+05:30
end_time = 2020-09-16T09:40:15+05:30
shuffle_question = True
shuffle_list = 0 1 2 3 4

all: create-build clean parse key images package backup

create-build:
	mkdir -p build

beamer:
	for f in latex/main*.tex; do \
		xelatex -output-directory build/ $$f; \
	done

clean: clean-build clean-latex
	rm -rf assignment.zip

clean-build:
	rm -f build/*.pdf build/*.out build/*.aux build/*.log build/*.toc build/*.nav build/*.snm
	rm -rf build/images

clean-latex:
	rm -rf latex/*.tex
	rm -rf latex/assignment.json
	rm -rf latex/*.csv

images: beamer
	rm -rf build/images
	mkdir -p build/images
	for f in build/main*.pdf; do \
  	convert -density 192 build/`basename $$f` -quality 100 build/images/`basename $$f`-%d.png; \
  done

key:
	for f in latex/key*.tex; do \
		xelatex -output-directory build/ $$f; \
	done

package:
	zip -j assignment.zip build/images/*.png latex/assignment.json


backup:
	cp assignment.zip "archive/assignment_$(assignment_id)_$(timestamp).zip"
	for f in build/key*.pdf; do \
		cp $$f "archive/keys/`basename $$f`_$(timestamp).pdf"; \
	done

parse:
	python3 parser.py --num_versions $(num_versions) --question_file $(question_file) --output $(output) \
	--assignment_id $(assignment_id) --start_time $(start_time) --end_time $(end_time) --roll_nums $(roll_nums) \
	--shuffle_question $(shuffle_question) --shuffle_list $(shuffle_list)

sync: clean
	git add .
	git commit -m "Syncing"
	git push origin master
