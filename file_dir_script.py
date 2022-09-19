import os
import sys
#print(os.getenv("HOSTNAME", default=None))
#path="/etc/hosts"
#if os.path.exists(path):
#    print(f"{path} is valid path")
#else:
#    print(f"{path} is Invalid Path")
#path= input("Enter the Path of Directory to list files :")
#print(os.path.is_dir())
#print(os.listdir(path))
#print(os.getcwd())
#print(os.listdir())

#print("hello World")

trace_path=input("Enter the path:")

if os.path.exists(trace_path):
    print(f"{trace_path} is a valid path")
else:
    print(f"{trace_path} is not a valid path \n Enter a valid path")
    sys.exit()

print(f"choosen path {trace_path} ")
f_d=os.listdir(trace_path)
print(f"{f_d}")


for paths in f_d:
  full_path=os.path.join(trace_path,paths)
  if os.path.isfile(full_path):
      print(f"{full_path} is a file")
  else:
      print(f"{full_path} is a directory")
