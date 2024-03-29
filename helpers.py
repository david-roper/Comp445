import os

#Code created by David Roper (40131739) and Gianfranco Dumoulin (40097768) 
#from helpers import edit_data, search_data_dir
#helpers to parse the requests sent from the httpc client
#if the request is invalid it can also send messages back for bad request
#such as errors 404 and 400
def search_data_dir(dir: str, target_file: str = ""):

    if '/../' in target_file:
        target_file = target_file.replace('/../', '/')
    elif '../' in target_file:
        target_file = target_file.replace('../', '')

    if not target_file:
        print(os.getcwd())
        fileList = '\n'.join(os.listdir(f'{os.getcwd()}/{dir}/{target_file}'))
        return fileList
    try:
        with open(f"{os.getcwd()}/{dir}{target_file}", 'r') as file_to_read:
            return file_to_read.read()
    except FileNotFoundError:
        return "404 Not Found"

def edit_data(target_file: str, data_to_write, dir: str, overwrite: bool = True):
    if '/../' in target_file:
        target_file = target_file.replace('/../', '/')
    elif '../' in target_file:
        target_file = target_file.replace('../', '')

    append_or_write = "w" if overwrite else "a"
    with open(f"{os.getcwd()}/{dir}/{target_file}", append_or_write) as file_to_write:
        file_to_write.write(data_to_write)