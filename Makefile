.PHONY: all preprocessor_with_args pp

SRC_DIR = target_files
SRCS = $(wildcard $(SRC_DIR)/*.c)
MY_SRC = $(firstword $(SRCS))

all: preprocessor_with_args

preprocessor_with_args:
	python preprocessor.py $(MY_SRC)

pp:
	python preprocessor.py

