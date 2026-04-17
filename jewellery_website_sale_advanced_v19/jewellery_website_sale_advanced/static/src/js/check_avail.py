from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/process-data', methods=['POST'])
def process_data():
    data = request.json
    token = data.get('token')
    pin_code = data.get('pin_code')
    
    # Process the data as needed (e.g., making a POST request or some other logic)
    response = {
        "status": "success",
        "token_received": token,
        "pin_code_received": pin_code
    }
    
    return jsonify(response)


