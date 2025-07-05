import re

def parse_and_count_interventions(file_path):
    interventions = {
        'watermarks': 0,
        'frames': 0,
        'modifications': 0,
        'artificial backgrounds': 0,
        'low quality': 0,
        'greyscale': 0,
        'collage': 0,
        'additional images needed': 0,
    }
    
    # Regex to identify grouped interventions
    group_pattern = re.compile(r"ILSVRC\d{4,}_val_\d{8}(?:, ILSVRC\d{4,}_val_\d{8})*")

    with open(file_path, 'r') as file:
        for line in file:
            found_groups = group_pattern.findall(line)
            if found_groups:
                # Calculate interventions based on multiple items listed
                for group in found_groups:
                    items = group.split(', ')
                    count_items = len(items)  # Count how many items in the group
                    if "watermark" in line:
                        interventions['watermarks'] += count_items
                    if "frame" in line or "border" in line:
                        interventions['frames'] += count_items
                    if "apparent modification" in line:
                        interventions['modifications'] += count_items
                    if "artificial background" in line:
                        interventions['artificial backgrounds'] += count_items
                    if "low resolution" in line or "poor quality" in line:
                        interventions['low quality'] += count_items
                    if "greyscale" in line or "monochrome" in line:
                        interventions['greyscale'] += count_items
                    if "collage" in line:
                        interventions['collage'] += count_items
            else:
                # For single mentions, add one if the keyword is present
                if "watermark" in line:
                    interventions['watermarks'] += 1
                if "frame" in line or "border" in line:
                    interventions['frames'] += 1
                if "apparent modification" in line:
                    interventions['modifications'] += 1
                if "artificial background" in line:
                    interventions['artificial backgrounds'] += 1
                if "low resolution" in line or "poor quality" in line:
                    interventions['low quality'] += 1
                if "greyscale" in line or "monochrome" in line:
                    interventions['greyscale'] += 1
                if "collage" in line:
                    interventions['collage'] += 1

    return interventions

# Call the function with the path to your text file
intervention_counts = parse_and_count_interventions('notes.txt')
for key, value in intervention_counts.items():
    print(f"{key}: {value}")

def count_double_new_lines(file_path):
    with open(file_path, 'r') as file:
        content = file.read()  # Read the entire file content into a single string
        double_new_lines_count = content.count('\n\n')  # Count occurrences of double new lines
    return double_new_lines_count

# Call the function with the path to your text file
double_new_lines = count_double_new_lines('notes.txt')
print(f"Number of intervened classes: {double_new_lines}")
print(f"Number of clean classes: {1000 - double_new_lines}")
