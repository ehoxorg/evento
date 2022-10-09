run:requirements.txt
	pip3 install -r requirements.txt
	python3 api.py
clean:
	rm -rf __pycache__