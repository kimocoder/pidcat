import argparse
import sys
import re
import importlib
import subprocess
from subprocess import PIPE


class FileReader():
    def __init__(self, filename):
        self.filename = filename
        self.input = open(filename, 'r')

    def __enter__(self):
        print("FileReader __enter__")
        self.input.__enter__()
        return self

    def __exit__(self, type, value, traceback):
        return self.input.__exit__(type, value, traceback)

    def next(self):
        line = self.input.readline()
        if line == '':
            raise Exception('This is the end.')
        return line.rstrip()
