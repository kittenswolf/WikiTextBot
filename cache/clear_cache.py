files = ["com_cache.txt", "msg_cache.txt"]
limit = 500

for file in files:
    raw_file = open(file, "r").read()
    current_ids = [id for id in raw_file.split("\n") if not id == '']

    print("File: " + file)
    print("Original length: " + str(len(current_ids)))

    last_part = current_ids[-limit:]

    print("New length: " + str(len(last_part)))

    with open(file, "w") as f:
        for id in last_part:
            f.write(id + "\n")
