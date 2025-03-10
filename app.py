from flask import Flask, render_template
from blueprints.odoo import odoo_bp
from blueprints.procfy import procfy_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Register blueprints
    app.register_blueprint(odoo_bp, url_prefix='/odoo')
    app.register_blueprint(procfy_bp, url_prefix='/procfy')

    # Home route with card-based homepage
    @app.route('/')
    def home():
        return render_template('index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', debug=True)
