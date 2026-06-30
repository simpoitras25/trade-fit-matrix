from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Trade Fit Matrix is running!'

if __name__ == '__main__':
    app.run(debug=True)