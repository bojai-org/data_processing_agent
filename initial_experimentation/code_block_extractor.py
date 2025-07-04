import re

def extract_code_block(reply):
    match = re.search(r"```(?:python)?\s*(.*?)```", reply, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

reply = """
Sure, here is an example implementation of a `get_inputs_outputs` function that does what you described:
```
def get_inputs_outputs(self, data_address):
    # Import any necessary libraries
    import os

    # Get the list of images in the 'images' folder
    images = os.listdir(data_address + '/images')

    # Create a list of tuples, where each tuple contains the image number and the corresponding tag
    tags = []
    with open(data_address + '/tags.txt') as f:
        for line in f:
            image_number, tag = line.split()
            tags.append((image_number, tag))

    # Return the inputs (images) and outputs (image addresses)
    return images, [data_address + '/images/' + img for img in images]
```
Here's how it works:

1. The function takes a `data_address` argument, which is the path to the data folder.
2. We import the `os` module to get the `listdir()` function, which we use to get the list of images in the 'images' folder.
3. We create a list of tuples, where each tuple contains the image number and the corresponding tag. We use the `open()` function to read the `tags.txt` file, and we split the line into two parts using the `split()` method.
4. We return the inputs (images) and outputs (image addresses) as two separate lists.

Note that this implementation assumes that the `tags.txt` file is located in the same directory as the data folder. If the `tags.txt` file is located elsewhere, you'll need to modify the function accordingly.
No JSON found.
"""

code = extract_code_block(reply)
print(code)


def replace_function(file_path, new_function_code):
    with open(file_path, 'r', encoding='utf-8') as f:
        original_code = f.read()

    # Match with leading whitespace and capture it (group 1)
    pattern = r"(^[ \t]*)def get_inputs_outputs\s*\(self,\s*data_dir\):(?:\n(?:\1 {4}.*|\1\t.*)*)?"

    match = re.search(pattern, original_code, re.MULTILINE)
    if not match:
        print("Function not found.")
        return

    indent = match.group(1)  # e.g., '    ' (4 spaces) if inside a class

    old_func_block = match.group(0)

    # Re-indent the new function code with matching indent level
    if new_function_code.strip().startswith("def get_inputs_outputs"):
        # Code already includes its own def
        lines = new_function_code.strip().splitlines()
        new_func_def = '\n'.join(indent + line if line.strip() else '' for line in lines)
    else:
        # Only function body was provided
        body = '\n'.join(indent + '    ' + line if line.strip() else '' for line in new_function_code.strip().splitlines())
        new_func_def = f"{indent}def get_inputs_outputs(self, data_dir):\n{body}"

    # Insert new after old, then remove old
    updated_code = original_code.replace(old_func_block, old_func_block + '\n' + new_func_def)
    updated_code = updated_code.replace(old_func_block, '', 1)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_code)

    print("Function replaced successfully with correct indentation.")


# === Example usage ===
# Replace with actual path to your file
file_path = 'your_script.py'
replace_function(file_path, code)