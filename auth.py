import json
import bcrypt

# Function to load users from the JSON file
def load_users():
    with open('users.json', 'r') as file:
        return json.load(file)['users']

# Function to authenticate a user
def authenticate(username, password):
    users = load_users()
    for user in users:
        if user['username'] == username and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return True
    return False

# Example usage
if __name__ == "__main__":
    username = input("Enter username: ")
    password = input("Enter password: ")
    if authenticate(username, password):
        print("Authentication successful")
    else:
        print("Authentication failed")
