from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_migrate import Migrate
from models import db, Usuario, Post, Comentario, Categoria

app = Flask(__name__)
app.secret_key = "clave_secreta"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:@localhost/miniblog"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)

# Context processors
@app.context_processor
def inject_data():
    current_user = Usuario.query.get(session.get('user_id')) if 'user_id' in session else None
    return dict(current_user=current_user, categorias=Categoria.query.all())

def require_login():
    if 'user_id' not in session:
        flash('Debes iniciar sesión', 'error')
        return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html', posts=Post.query.order_by(Post.fecha_creacion.desc()).all())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Usuario.query.filter_by(nombre_usuario=request.form['username']).first()
        if user and user.contraseña == request.form['password']:
            session.update({'user_id': user.id, 'username': user.nombre_usuario})
            flash('Login exitoso!', 'success')
            return redirect(url_for('index'))
        flash('Usuario o contraseña incorrectos', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username, email, password = request.form['username'], request.form['email'], request.form['password']
        
        if Usuario.query.filter_by(nombre_usuario=username).first():
            flash('El nombre de usuario ya existe', 'error')
        elif Usuario.query.filter_by(correo=email).first():
            flash('El email ya está registrado', 'error')
        else:
            db.session.add(Usuario(nombre_usuario=username, correo=email, contraseña=password))
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
            titulo=request.form['titulo'],
            contenido=request.form['contenido'],
            usuario_id=session['user_id']
        )
        
        for cat_id in request.form.getlist('categorias[]'):
            cat = Categoria.query.get(int(cat_id))
            if cat:
                post.categorias.append(cat)
        
        db.session.add(post)
        db.session.commit()
        flash("Post creado con éxito", "success")
        return redirect(url_for('index'))
    
    return render_template('nuevo_post.html', categorias=Categoria.query.all())

@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def ver_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if request.method == 'POST':
        if 'user_id' not in session:
            return require_login()
        
        db.session.add(Comentario(
            texto=request.form['comentario'],
            usuario_id=session['user_id'],
            post_id=post_id
        ))
        db.session.commit()
        flash("Comentario agregado", "success")
        return redirect(url_for('ver_post', post_id=post_id))
    
    return render_template('ver_post.html', post=post)

if __name__ == '__main__':
    app.run(debug=True)