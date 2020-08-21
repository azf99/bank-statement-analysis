# Bank statement Analysis

By- Azfar Lari

**Files**
1. extract.py: contains functions for extracting data from pdfs of diffetent banks(currently, Yes Bank and Allahabad Bank)

2. analysis.py: contains functions for processing and analizing the data

3. main.py: the driver code that accepts the filename of the PDF

**Setup**
Prequisites:- Python 3 and tesseract need to be installed
for tesseract, see: https://github.com/tesseract-ocr/tesseract/wiki


1. Run 
	pip install -r requirements.txt

2. Run
	python main.py <filename.pdf>

This starts the process and generates the outputs in excelsheets and returns JSON output

