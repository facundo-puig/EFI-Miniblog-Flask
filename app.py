from flask import Flask
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from datetime import timedelta
from models import db

from views import (
    UserRegisterAPI, LoginAPI,
    PostListAPI, PostDetailAPI,
    CommentListAPI, CommentDetailAPI,
    CategoryListAPI, CategoryDetailAPI,
    UserListAPI, UserDetailAPI, UserRoleAPI, UserProfileAPI,
    StatsAPI
)

# DB config
app = Flask(__name__)
app.secret_key = "clave_secreta"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:@localhost/miniblog"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# JWT config
app.config['JWT_SECRET_KEY'] = 'jwt_clave_secreta'  
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Inicialización
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)


#### Registro de rutas ####

# Auth
app.add_url_rule('/api/register', view_func=UserRegisterAPI.as_view('api_register'))
app.add_url_rule('/api/login', view_func=LoginAPI.as_view('api_login'))

# Posts
app.add_url_rule('/api/posts', view_func=PostListAPI.as_view('api_posts'))
app.add_url_rule('/api/posts/<int:post_id>', view_func=PostDetailAPI.as_view('api_post_detail'))

# Comentarios
app.add_url_rule('/api/posts/<int:post_id>/comments', view_func=CommentListAPI.as_view('api_post_comments'))
app.add_url_rule('/api/comments/<int:comment_id>', view_func=CommentDetailAPI.as_view('api_comment_detail'))

# Categorias
app.add_url_rule('/api/categories', view_func=CategoryListAPI.as_view('api_categories'))
app.add_url_rule('/api/categories/<int:category_id>', view_func=CategoryDetailAPI.as_view('api_category_detail'))

# Usuarios (Admin)
app.add_url_rule('/api/users/me', view_func=UserProfileAPI.as_view('api_user_profile')) # ruta adicional para ver el perfil de uno mismo sin indicar el id
app.add_url_rule('/api/users', view_func=UserListAPI.as_view('api_users'))
app.add_url_rule('/api/users/<int:user_id>', view_func=UserDetailAPI.as_view('api_user_detail'))
app.add_url_rule('/api/users/<int:user_id>/role', view_func=UserRoleAPI.as_view('api_user_role'))

# Estadísticas
app.add_url_rule('/api/stats', view_func=StatsAPI.as_view('api_stats'))


if __name__ == '__main__':
    app.run(debug=True)
