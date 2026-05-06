.PHONY: all

SRC_DIR = target_files
SRCS = $(wildcard $(SRC_DIR)/*.c)
MY_SRC = $(firstword $(SRCS))

all:
	python preprocessor.py $(MY_SRC)
