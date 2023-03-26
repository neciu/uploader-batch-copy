import argparse
import os
import csv
import hashlib
from datetime import datetime
import shutil
import sys


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

batch_size = 1000
supported_extensions = (
    ".jpg",
    ".jpeg",
    ".png",
    ".avi",
    ".cr2",
    ".mov",
    ".mp4",
    ".mpg",
    ".mts",
)
all_medias = []
name_collisions = []
hash_collisions_count = 0
copied_medias_count = 0
hash_to_media_map = {}
csv_file_path = os.path.join(args.input_path, "_uploader_batch_copy.csv")
fieldnames = ["relative_root", "media_name", "sha256", "copy_timestamp"]

update_progress(0)

file_exists = os.path.isfile(csv_file_path)
if file_exists:
    # Load current csv into a dict
    with open(csv_file_path, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            hash_to_media_map[row["sha256"]] = row
else:
    # Create the csv file
    with open(csv_file_path, "a") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()


with open(csv_file_path, "a") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    # Find all media files
    for root, dirs, files in os.walk(args.input_path):
        # Skip Windows recycle bin path
        if "$recycle.bin" in root.lower():
            continue

        medias = [f for f in files if f.lower().endswith(supported_extensions)]
        for media in medias:
            all_medias.append({"name": media, "root": root})

    # Process media files
    for media in all_medias:
        # Stop processing if batch size is reached
        if copied_medias_count >= batch_size:
            break

        root = media["root"]
        relative_root = os.path.relpath(root, args.input_path)
        name = media["name"]
        media_path = os.path.join(root, name)

        # Skip name collisions
        if name in os.listdir(args.output_path):
            name_collisions.append(os.path.join(relative_root, name))
            continue

        with open(media_path, "rb") as media_file:
            contents = media_file.read()
            hash_str = hashlib.sha256(contents).hexdigest()

            # Skip hash collisions
            if hash_str in hash_to_media_map:
                hash_collisions_count += 1
                continue

            # Copy file and save it's hash to the csv and memory
            shutil.copy2(media_path, args.output_path)
            new_row = {
                "relative_root": relative_root,
                "media_name": name,
                "sha256": hash_str,
                "copy_timestamp": datetime.now().astimezone().isoformat(),
            }
            writer.writerow(new_row)
            hash_to_media_map["hash_str"] = new_row

        copied_medias_count += 1
        update_progress(copied_medias_count / batch_size)

# Displays 100% progress in case when batch finishes before it's max size
if copied_medias_count / batch_size < 1:
    update_progress(1)

print("")
print(f"All medias count: {len(all_medias)}.")
print(f"Name collisions count: {len(name_collisions)}.")
print(f"Hash collisions count: {hash_collisions_count}.")
print(f"Copied medias count: {copied_medias_count}.")

if len(name_collisions) > 0:
    print("")
    print("Name collisions:")
    for c in name_collisions:
        print(f"\t{c}")
