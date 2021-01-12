from flask import Flask

from .main.routes import main
from .extensions import mongo 

def create_app():
    app = Flask(__name__)
    
    app.config['MONGO_URI'] = 'mongodb://admin:tddD4Q43iMQnLpQ@cluster0-shard-00-00.e8xgs.mongodb.net:27017,cluster0-shard-00-01.e8xgs.mongodb.net:27017,cluster0-shard-00-02.e8xgs.mongodb.net:27017/<mydb>?ssl=true&replicaSet=atlas-ouhmh7-shard-0&authSource=admin&retryWrites=true&w=majority'

    mongo.init_app(app)
    
    app.register_blueprint(main)
    
    return app
    
