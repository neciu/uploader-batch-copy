#!/usr/bin/python

import argparse
import os
import csv
import hashlib
from datetime import datetime
import shutil
import sys
import time


# Source https://stackoverflow.com/a/15860757/1035552
# update_progress() : Displays or updates a console progress bar
# Accepts a float between 0 and 1. Any int will be converted to a float.
# A value under 0 represents a 'halt'.
# A value at 1 or bigger represents 100%
def update_progress(progress):
    barLength = 10  # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "Done...\r\n"
    block = int(round(barLength * progress))
    text = "\rPercent: [{0}] {1}% {2}".format(
        "#" * block + "-" * (barLength - block), progress * 100, status
    )
    sys.stdout.write(text)
    sys.stdout.flush()


parser = argparse.ArgumentParser()
parser.add_argument("--input_path")
parser.add_argument("--output_path")

args = parser.parse_args()

batch_size = 2
supported_extensions = (".jpg", ".jpeg", ".png")
all_images = []
name_collisions = []
hash_collisions_count = 0
copied_images_count = 0
csv_file_path = os.path.join(args.input_path, "_uploader_batch_copy.csv")
file_exists = os.path.isfile(csv_file_path)

update_progress(0)

with open(csv_file_path, "a+") as csvfile:
    # Write headers to csv if needed
    fieldnames = ["relative_root", "image_name", "sha256", "copy_timestamp"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    if not file_exists:
        writer.writeheader()

    # Load current csv into a dict
    reader = csv.DictReader(csvfile)
    hash_to_image_map = {}
    for row in reader:
        hash_to_image_map[row["sha256"]] = row

    # Find all media files
    for root, dirs, files in os.walk(args.input_path):
        images = [f for f in files if f.lower().endswith(supported_extensions)]
        for image in images:
            all_images.append({"name": image, "root": root})

    # Process media files
    for image in all_images:
        # Stop processing if batch size is reached
        if copied_images_count >= batch_size:
            break

        root = image["root"]
        relative_root = os.path.relpath(root, args.input_path)
        name = image["name"]
        image_path = os.path.join(root, name)

        # Skip name collisions
        if name in os.listdir(args.output_path):
            name_collisions.append(os.path.join(relative_root, name))
            continue

        with open(image_path, "rb") as image_file:
            contents = image_file.read()
            hash_str = hashlib.sha256(contents).hexdigest()

            # Skip hash collisions
            if hash_str in hash_to_image_map:
                hash_collisions_count += 1
                continue

            # Copy file and save it's hash to the csv and memory
            shutil.copy2(image_path, args.output_path)
            new_row = {
                "relative_root": relative_root,
                "image_name": name,
                "sha256": hash_str,
                "copy_timestamp": datetime.now().astimezone().isoformat(),
            }
            writer.writerow(new_row)
            hash_to_image_map["hash_str"] = new_row

        copied_images_count += 1
        update_progress(copied_images_count / batch_size)
        time.sleep(0.001)

update_progress(1+copied_images_count / batch_size)
print("")
print(f"All images count: {len(all_images)}.")
print(f"Name collisions count: {len(name_collisions)}.")
print(f"Hash collisions count: {hash_collisions_count}.")
print(f"Copied images count: {copied_images_count}.")

if len(name_collisions) > 0:
    print("")
    print("Name collisions:")
    for c in name_collisions:
        print(f"\t{c}")
