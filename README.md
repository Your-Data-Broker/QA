# QA

# Assembling the .so library:
#   nasm -f elf64 backend.s
#   gcc -shared backend.o -o backend

# Usage:
#   python3 root.py

# Changing the test image:
#   Change the source code in root.py (path to image)
#   Move the image you want from testImages to one, where root.py located
