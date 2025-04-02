#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  1 09:42:41 2025

@author: jlu8

test script to read and process json files
"""

import re
import os
import glob
from functools import reduce
import argparse
from collections import OrderedDict, Counter
import sys
import numpy as np
import pandas as pd
import requests
import time
from io import StringIO
import csv
import random
import subprocess
import yaml
import warnings
from pathlib import Path
import json
from io import StringIO

working_dir = "/Users/jlu8/MGnify/GitHub/dataharmonizer-support/"


json_file = os.path.join(working_dir, "metadata_files", "example_export.js")


with open(json_file) as f:
    data = json.load(f)