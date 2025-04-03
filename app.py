from flask import Flask, render_template
from blueprints.odoo import odoo_bp
from blueprints.procfy.views import procfy

app = Flask(__name__)
app.register_blueprint(odoo_bp, url_prefix='/odoo')
print(app.url_map)
app.register_blueprint(procfy, url_prefix='/procfy')

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)