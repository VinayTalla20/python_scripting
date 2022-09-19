import os
import sys


trace_path=input("Enter the path:")

print(f"choosen path {trace_path} ")
f_d=os.listdir(trace_path)
print(f"{f_d}")


for paths in f_d:
  full_path=os.path.join(trace_path,paths)
  if os.path.isfile(full_path):
      print(f"{full_path} is a file")
  else:
      print(f"{full_path} is a directory")
