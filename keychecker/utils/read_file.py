def read_key(file_path):
    try:
        with open(file_path, "r") as file:
            key_string = file.read()
            return(key_string)
    except FileNotFoundError:
        print("❗❗ File Not Found! ❗❗ Exiting.")
        exit()