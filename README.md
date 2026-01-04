# Wordle Solver Bot

A Python-based **Wordle solver bot** that suggests optimal guesses based on how many possibilities a word eliminates.  
This solver uses feedback (`g`, `y`, `b`) to aggressively reduce the remaining search space.

## Project Structure
├── main.py # Main solver logic and CLI
├── text_init.py # Word list and preprocessing utilities
├── words.txt # Allowed Wordle guesses (5-letter words)
├── LICENSE
└── README.md

## Installation
### Required Libraries
1) wordfreq
2) colorama
To install these libraries, run:
```bash
pip install -r requirements.txt
```



## How to Run
### Add word list
Start off by adding any five letter word list of your choice. If you don't want to, there is already a default one.
### Initialize `words_frequency.txt`
run the python file
```bash
python text_init.py
```
### Run `main.py`
Have fun!

