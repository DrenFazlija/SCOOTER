import sys
import subprocess

def substitute_data_path(sql_file_path, data_path):
    # Read the SQL file
    with open(sql_file_path, 'r') as file:
        sql_content = file.read()

    sql_content = sql_content.split("\n")

    sql_content[0] = "\\set data_path '" + data_path + "'"

    # Write the modified SQL to a temporary file
    temp_sql_file_path = sql_file_path + ".tmp"
    with open(temp_sql_file_path, 'w') as temp_file:
        # Write the modified SQL content
        temp_file.write("\n".join(sql_content))

    return temp_sql_file_path

def execute_psql(temp_sql_file_path):
    # Construct the psql command
    command = ["psql", "-h", "localhost", "-U", "postgres", "-d", "scooter", "-f", temp_sql_file_path]

    # Execute the psql command
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Print the output and errors
    print(result.stdout.decode())
    print(result.stderr.decode())

    # Check for errors
    if result.returncode != 0:
        sys.exit(result.returncode)

def main():
    if len(sys.argv) != 2:
        print("Usage: python init_database.py <data_path>")
        print("E.g.: python init_database.py /home/user/scooter_data/")
        sys.exit(1)

    data_path = sys.argv[1]

    print("Changing the data path...")

    # Substitute the data_path and get the path of the temporary SQL file
    temp_sql_file_path = substitute_data_path("schema.sql", data_path)

    print("Done!")

    # Get the first line of the SQL file
    with open(temp_sql_file_path, 'r') as file:
        first_line = file.readline()

    # Get everything after "\set data_path "
    first_line = first_line[15:]

    correct_data_path = input("Is this the correct data path (y/n): " + first_line + " ")
    if correct_data_path != "y":
        print("Please run the script again with the correct data path.")
        import os
        os.remove(temp_sql_file_path)
        sys.exit(1)

    print("Setting up the database... (this can take a few minutes)")
    print("Important: After providing your password, please wait until the script finishes! (even if it looks like it's stuck!)")

    # Execute the psql command with the temporary SQL file
    execute_psql(temp_sql_file_path)

    # Remove the temporary file
    import os
    os.remove(temp_sql_file_path)

    print("The database setup is finished!")

if __name__ == "__main__":
    main()
