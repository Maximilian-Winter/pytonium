# Function to generate .pyi stub file from given Cython code and save it to a file
import re


def generate_pyi_from_cython(cython_code, pyi_filename):
    # Initialize an empty string to hold the contents of the pyi file, corrected for 'self'
    pyi_content = ''

    # Extract class name and methods
    class_match = re.search(r'cdef class (\w+):', cython_code)
    if class_match:
        class_name = class_match.group(1)
        pyi_content += f'class {class_name}:\n'

        # Extract methods again, this time keeping 'self' or 'cls' for instance and class methods
        method_matches = re.findall(r'def ([\w_]+)\(([^)]*)\):', cython_code)
        for method_name, params in method_matches:
            # Keep parameters as is, including 'self' and 'cls'
            pyi_content += f'    def {method_name}({params}) -> None: ...\n'

    # Save to a .pyi file
    with open(pyi_filename, 'w') as f:
        f.write(pyi_content)