# uploader-batch-copy

The script copies all multimedia files from the given input path (recursively) to the output directory.

Since all files are saved in the same directory, the script prevents overriding the files with the same name - it skips them (the output directory will be cleaned after some time).

To prevent copying the same file twice, the script calculates (and stores in a CSV file) hashes of the previously copied files.

Copying is run in batches.

## Usage:
```
python3 script.py --input_path="/input/path/with/media" --output_path="/output/path"
```
