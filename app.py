from flask import Flask, request, jsonify

app = Flask(__name__)

mirage_data = {}
prehistoric_data = {}

@app.route('/')
def home():
    return "API Working!"

# Mirage
@app.route('/mirage', methods=['GET', 'POST'])
def mirage():
    global mirage_data
    if request.method == 'POST':
        mirage_data = request.json or {}
        print("[INFO] Get Data /mirage:", mirage_data)
        return jsonify({"status": "ok", "received": mirage_data})
    else:  # GET
        return jsonify(mirage_data)

# Prehistoric
@app.route('/prehistoric', methods=['GET', 'POST'])
def prehistoric():
    global prehistoric_data
    if request.method == 'POST':
        prehistoric_data = request.json or {}
        print("[INFO] Get Data /prehistoric:", prehistoric_data)
        return jsonify({"status": "ok", "received": prehistoric_data})
    else:
        return jsonify(prehistoric_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
