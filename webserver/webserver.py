from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "This is a simple web server. Try attacking it!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)  # Runs on port 80, accessible from other machines
