#!/usr/bin/env python3
"""Placeholder — see GEMSDOE32/scripts/build_features.py for full 35-channel stack."""
import pathlib
if pathlib.Path("data/training_features.tif").exists():
    print("Would build 35-channel feature stack to /tmp/gems32/work/feature_stack.npy (see GEMSDOE32)")
else:
    print("No data/training_features.tif — download first")
