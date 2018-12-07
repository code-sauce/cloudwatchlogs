def create_file_if_does_not_exist(file_name):
    try:
        file = open(file_name, 'r')
    except IOError:
        file = open(file_name, 'w')
    file.close()
