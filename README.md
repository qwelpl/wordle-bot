# Wordle Solver Bot

A Python-based **Wordle solver bot** that suggests optimal guesses based on how many possibilities a word eliminates.  
This solver uses feedback (`g`, `y`, `b`) to aggressively reduce the remaining search space.

## Project Structure
```
├── src/
│   ├── main.py              
│   ├── text_init.py         
│   └── files/
│       ├── requirements.txt
│       ├── words.txt        
│       └── words_frequency.txt
├── LICENSE
└── README.md
```
## Installation
### Required Libraries
1) wordfreq
2) colorama
To install these libraries, run:
```bash
pip install -r src/files/requirements.txt
```



## How to Run
### Add word list
Start off by adding any five letter word list of your choice. If you don't want to, there is already a default list.
### Initialize `words_frequency.txt`
run the python file
```bash
python src/text_init.py
```
### Run `src/main.py`
```bash
python src/main.py
```
Have fun!

