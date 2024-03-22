from flask import Flask, request, make_response, jsonify
from pymongo import MongoClient
import bcrypt
from flask_cors import CORS

app = Flask(__name__)

CORS(app)


db1Client = MongoClient('mongodb://localhost:27017')
db1 = db1Client.sic_database_1


# ----------------------------Model Classes--------------------------------
class User:
    def __init__(self, account_type, account_name, email, password):
        self.account_type = account_type
        self.account_name = account_name
        self.email = email
        self.password = password

    def save(self):  
        users = db1.users
        hashed_password = bcrypt.hashpw(self.password.encode('utf-8'), bcrypt.gensalt())
        # Check if the email already exists in the database
        existing_user = users.find_one({'email': self.email})
        if existing_user:
            print("User with this email already exists in the database")
            return "existing_user"
        try:
            result = users.insert_one({'accountType': self.account_type, 'accountName' : self.account_name, 'email': self.email, 'password': hashed_password})
            if result.acknowledged:
                return "success"
            else:
                return "failed"
        except Exception as e:
            print(f"Error occurred while saving user: {e}")
            return "exception"

    @staticmethod
    def find_by_email(email):
        users = db1.users
        user_data = users.find_one({'email': email})
        if user_data:
            return User( user_data["accountType"], user_data["accountName"],user_data['email'], user_data['password'])
        return None
    
# -----------------------------User Authentication------------------------
@app.route('/smart_ielts_coach/user/register', methods=['GET', 'POST'])
def register():
    user_data = request.get_json()
    account_type = user_data.get('accountType')
    account_name = user_data.get('accountName')
    email = user_data.get('email')
    password = user_data.get('password')
    
    if account_type and account_name and email and password:
        new_user = User(account_type, account_name, email, password)
        save_result = new_user.save()
        
        if save_result == "success":
            message = {'message': 'Registration was successful!'}
            return make_response(jsonify(message), 201)
        elif save_result == "failed":
            message = {'error': 'Registration was unsuccessful due to unexpected condition.'}
            return make_response(jsonify(message), 409)
        elif save_result == "existing_user":
            message = {'Unprocessable entity': 'User already exists in the database.'}
            return make_response(jsonify(message), 422)
        else:
            message = {'Internal Server error': 'Some unknown error occurred.'}
            return make_response(jsonify(message), 500)
    else:
        message = {'Bad request': 'Missing data'}
        return make_response(jsonify(message), 400)


@app.route('/smart_ielts_coach/user/login', methods=['POST'])
def login():
        if request.method == 'POST':
            try:
                login_data = request.get_json()

                email = login_data.get("email")
                password = login_data.get("password")
                print(email + password)


                # Fetch user from the database using email
                user = User.find_by_email(email)

                if user and bcrypt.checkpw(password.encode('utf-8'), user.password):
                    # Successful login, return response code 200
                    return make_response(jsonify({"message": "Login successful"}), 200)
                else:
                    # Invalid credentials
                    return make_response(jsonify({"message": "Invalid credentials"}), 404)
            except Exception as e:
            # Handle unknown errors
                print(e)
                return make_response(jsonify({"message": "An error occurred: {}".format(str(e))}), 500)
        else:
            return make_response(jsonify({"message": "Method Not Allowed. Please use POST method for login."}), 405)
    
    


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
