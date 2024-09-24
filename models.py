from main import database, app
from datetime import datetime, timezone

def get_utc_now():
    return datetime.now(timezone.utc)

class Usuario(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    username = database.Column(database.String, nullable=False)
    email = database.Column(database.String, nullable=False, unique=True)
    senha = database.Column(database.String, nullable=False)
    foto_perfil = database.Column(database.String, default='default.jpg')
    posts = database.relationship('Post', backref='autor', lazy=True)
    cursos = database.Column(database.String, nullable=False, default='Não informado')
    
class Post(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    titulo = database.Column(database.String, nullable=False)
    corpo = database.Column(database.Text, nullable=False)
    data_criacao = database.Column(database.DateTime, nullable=False, default=get_utc_now)
    id_usuario = database.Column(database.Integer, database.ForeignKey('usuario.id'), nullable=False)

if __name__ == '__main__':
    with app.app_context():
        # database.drop_all()
        database.create_all()
    print('Banco criado!')