from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "This is a simple web server. Try attacking it!"

if __name__ == '__main__':
    app.run(host='192.168.50.10', port=80)  # Runs on port 80, accessible from other machines
