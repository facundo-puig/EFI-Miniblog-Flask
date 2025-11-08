from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from passlib.hash import bcrypt
from datetime import timedelta
from models import db, User, UserCredential, Post, Comment, Category

from views import (
    UserRegisterAPI, LoginAPI,
    PostListAPI, PostDetailAPI,
    CommentListAPI, CommentDetailAPI,
    CategoryListAPI, CategoryDetailAPI,
    UserListAPI, UserDetailAPI, UserRoleAPI,
    StatsAPI
)

app = Flask(__name__)
app.secret_key = "clave_secreta"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:@localhost/miniblog"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

#jwt
app.config['JWT_SECRET_KEY'] = 'jwt_clave_secreta'  
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# Context processors
@app.context_processor
def inject_data():
    current_user = User.query.get(session.get('user_id')) if 'user_id' in session else None
    return dict(current_user=current_user, categories=Category.query.all())

def require_login():
    if 'user_id' not in session:
        flash('Debes iniciar sesión', 'error')
        return redirect(url_for('login'))

@app.route('/')
def index():
    posts = Post.query.filter_by(is_published=True).order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        
        # Verificar que el usuario existe y tiene credenciales
        if user and user.credential:
            # Verificar la contraseña con bcrypt
            if bcrypt.verify(request.form['password'], user.credential.password_hash):
                # Verificar que el usuario esté activo
                if not user.is_active:
                    flash('Usuario desactivado', 'error')
                    return render_template('login.html')
                
                session.update({'user_id': user.id, 'username': user.name})
                flash('Login exitoso!', 'success')
                return redirect(url_for('index'))
        
        flash('Email o contraseña incorrectos', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Verificar si el usuario ya existe
        if User.query.filter_by(name=username).first():
            flash('El nombre de usuario ya existe', 'error')
        elif User.query.filter_by(email=email).first():
            flash('El email ya está registrado', 'error')
        else:
            # Crear el usuario
            new_user = User(name=username, email=email)
            db.session.add(new_user)
            db.session.flush()  # Para obtener el ID del usuario
            
            # Crear las credenciales con la contraseña hasheada
            password_hash = bcrypt.hash(password)
            credentials = UserCredential(
                user_id=new_user.id,
                password_hash=password_hash
            )
            db.session.add(credentials)
            db.session.commit()
            
            flash('Registro exitoso! Ya puedes iniciar sesión', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('index'))

@app.route('/post/nuevo', methods=['GET', 'POST'])
def nuevo_post():
    if 'user_id' not in session:
        return require_login()
    
    if request.method == 'POST':
        post = Post(
            title=request.form['title'],
            content=request.form['content'],
            user_id=session['user_id']
        )
        
        # Agregar categorías si se seleccionaron
        for cat_id in request.form.getlist('categories[]'):
            cat = Category.query.get(int(cat_id))
            if cat:
                post.categories.append(cat)
        
        db.session.add(post)
        db.session.commit()
        flash("Post creado con éxito", "success")
        return redirect(url_for('index'))
    
    return render_template('nuevo_post.html', categories=Category.query.all())

@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def ver_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if request.method == 'POST':
        if 'user_id' not in session:
            return require_login()
        
        new_comment = Comment(
            text=request.form['comment'],
            user_id=session['user_id'],
            post_id=post_id
        )
        db.session.add(new_comment)
        db.session.commit()
        flash("Comentario agregado", "success")
        return redirect(url_for('ver_post', post_id=post_id))
    
    return render_template('ver_post.html', post=post)

#registro de rutas


#autenticacion
app.add_url_rule('/api/register', view_func=UserRegisterAPI.as_view('api_register'))
app.add_url_rule('/api/login', view_func=LoginAPI.as_view('api_login'))

#post
app.add_url_rule('/api/posts', view_func=PostListAPI.as_view('api_posts'))
app.add_url_rule('/api/posts/<int:post_id>', view_func=PostDetailAPI.as_view('api_post_detail'))

#comentarios
app.add_url_rule('/api/posts/<int:post_id>/comments', view_func=CommentListAPI.as_view('api_post_comments'))
app.add_url_rule('/api/comments/<int:comment_id>', view_func=CommentDetailAPI.as_view('api_comment_detail'))

#categorias
app.add_url_rule('/api/categories', view_func=CategoryListAPI.as_view('api_categories'))
app.add_url_rule('/api/categories/<int:category_id>', view_func=CategoryDetailAPI.as_view('api_category_detail'))

#usuariosAdmin
app.add_url_rule('/api/users', view_func=UserListAPI.as_view('api_users'))
app.add_url_rule('/api/users/<int:user_id>', view_func=UserDetailAPI.as_view('api_user_detail'))
app.add_url_rule('/api/users/<int:user_id>/role', view_func=UserRoleAPI.as_view('api_user_role'))


#estadisticas
app.add_url_rule('/api/stats', view_func=StatsAPI.as_view('api_stats'))


if __name__ == '__main__':
    app.run(debug=True)
