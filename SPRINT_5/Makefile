PY ?= python

install:        ## install dependencies
	$(PY) -m pip install -r requirements.txt
sample:         ## generate synthetic input data (demo only)
	$(PY) scripts/generate_sample_data.py
run:            ## run Day 29-35 end to end
	$(PY) run_sprint5.py --day all
test:           ## unit tests
	$(PY) -m pytest -q
verify:         ## check Sprint 5 exit criteria
	$(PY) scripts/verify_exit_criteria.py
preview:        ## render PNG previews of the 5 test tearsheets
	$(PY) scripts/render_previews.py
clean:          ## delete generated outputs (keeps folders)
	find output reports logs -type f ! -name .gitkeep -delete
