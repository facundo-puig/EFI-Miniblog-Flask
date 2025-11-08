from datetime import timedelta
from flask import request, jsonify
from marshmallow import ValidationError
from flask.views import MethodView
from passlib.hash import bcrypt_sha256
from flask_jwt_extended import (
    jwt_required,
    create_access_token,
    get_jwt,
    get_jwt_identity
)

from functools import wraps
from models import db, User, UserCredential, Post, Category, Comment
from schemas import (
    UserSchema, RegisterSchema, LoginSchema,
    PostSchema, CommentSchema, CategorySchema
)

def role_required(*allowed_roles: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            role = claims.get('role')
            if not role or role not in allowed_roles:
                return {"error": "Acceso denegado para este rol"}, 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

class UserRegisterAPI(MethodView):
    def post(self):
        try:
            data = RegisterSchema().load(request.json)
        except ValidationError as err:
            return {"error": err.messages}, 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({"error": "Email ya está en uso"}), 400
        
        new_user = User(name=data['username'], email=data['email'])
        db.session.add(new_user)
        db.session.flush()
        
        password_hash = bcrypt_sha256.hash(data['password'])

        credentials = UserCredential(
            user_id=new_user.id, 
            password_hash=password_hash
        )  
        db.session.add(credentials)
        db.session.commit()
        return UserSchema().dump(new_user), 201
    
class LoginAPI(MethodView):
    def post(self):
        try:
            data = LoginSchema().load(request.json)
        except ValidationError as err:
            return {"error": err.messages}, 400
        
        user = User.query.filter_by(email=data["email"]).first()

        if not user or not user.credential:
            return {"error": "Credenciales inválidas"}, 401
        
        if not bcrypt_sha256.verify(data["password"], user.credential.password_hash):
            return {"error": "Credenciales inválidas"}, 401
        
        if not user.is_active:
            return {"error": "Usuario desactivado"}, 401

        additional_claims = {
            "email": user.email,
            "role": user.role,
            "name": user.name
        }
        identity = str(user.id)
        token = create_access_token(
            identity=identity, 
            additional_claims=additional_claims, 
            expires_delta=timedelta(hours=24)
        )

        return jsonify(access_token=token), 200
    
####  POSTS  ####
class PostListAPI(MethodView):
    
    def get(self):
        posts = Post.query.filter_by(is_published=True).order_by(Post.created_at.desc()).all()
        return PostSchema(many=True).dump(posts), 200
    
    @jwt_required()
    def post(self):
        try:
            data = PostSchema().load(request.json)
        except ValidationError as err:
            return {"error": err.messages}, 400
        
        user_id = int(get_jwt_identity())
        
        new_post = Post(
            title=data['title'],
            content=data['content'],
            user_id=user_id
        )
        db.session.add(new_post)
        db.session.commit()
        
        return {"message": "Post creado", "post_id": new_post.id}, 201
    
class PostDetailAPI(MethodView):
    
    def get(self, post_id):
        post = Post.query.get_or_404(post_id)
        return PostSchema().dump(post), 200
    
    @jwt_required()
    def put(self, post_id):
        post = Post.query.get_or_404(post_id)
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        role = claims.get('role')
        

        if post.user_id != user_id and role != 'admin':
            return {"error": "No autorizado"}, 403
        
        try:
            data = PostSchema(partial=True).load(request.json)
            if 'title' in data:
                post.title = data['title']
            if 'content' in data:
                post.content = data['content']
            
            db.session.commit()
            return {"message": "Post actualizado"}, 200
        except ValidationError as err:
            return {"error": err.messages}, 400
    
    @jwt_required()
    @role_required("admin", "user")
    def delete(self, post_id):
        post = Post.query.get_or_404(post_id)
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        role = claims.get('role')
        
        if post.user_id != user_id and role != 'admin':
            return {"error": "No autorizado"}, 403
        
        db.session.delete(post)
        db.session.commit()
        return {"message": "Post eliminado"}, 200
    

####  COMENTARIOS  ####

class CommentListAPI(MethodView):
    
    def get(self, post_id):
        Post.query.get_or_404(post_id)
        comments = Comment.query.filter_by(post_id=post_id, is_visible=True).all()
        return CommentSchema(many=True).dump(comments), 200
    
    @jwt_required()
    def post(self, post_id):
        Post.query.get_or_404(post_id)
        
        try:
            data = CommentSchema().load(request.json)
        except ValidationError as err:
            return {"error": err.messages}, 400
        
        user_id = int(get_jwt_identity())
        
        new_comment = Comment(
            text=data['text'],
            user_id=user_id,
            post_id=post_id
        )
        db.session.add(new_comment)
        db.session.commit()
        
        return {"message": "Comentario creado", "comment_id": new_comment.id}, 201


class CommentDetailAPI(MethodView):
    
    #Eliminar
    @jwt_required()
    @role_required("admin", "moderator", "user")
    def delete(self, comment_id):
        comment = Comment.query.get_or_404(comment_id)
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        role = claims.get('role')
        
        if comment.user_id != user_id and role not in ['moderator', 'admin']:
            return {"error": "No autorizado"}, 403
        
        db.session.delete(comment)
        db.session.commit()
        return {"message": "Comentario eliminado"}, 200
    
    # Editar
    @jwt_required()
    def put(self, comment_id):
        # Editar solo comentarios propios
        comment = Comment.query.get_or_404(comment_id)
        user_id = int(get_jwt_identity())
        
        # Solo el autor puede editar su comentario
        if comment.user_id != user_id:
            return {"error": "No autorizado"}, 403
        
        try:
            data = CommentSchema(partial=True).load(request.json)
            if 'text' in data:
                comment.text = data['text']
            
            db.session.commit()
            return {"message": "Comentario actualizado"}, 200
        except ValidationError as err:
            return {"error": err.messages}, 400
    

####  CATEGORÍAS  ####

class CategoryListAPI(MethodView):
    
    def get(self):
        categories = Category.query.all()
        return CategorySchema(many=True).dump(categories), 200
    
    @jwt_required()
    @role_required("admin", "moderator")
    def post(self):
        try:
            data = CategorySchema().load(request.json)
        except ValidationError as err:
            return {"error": err.messages}, 400
        
        if Category.query.filter_by(name=data['name']).first():
            return {"error": "La categoría ya existe"}, 400
        
        new_category = Category(name=data['name'])
        db.session.add(new_category)
        db.session.commit()
        
        return {"message": "Categoría creada", "category_id": new_category.id}, 201


class CategoryDetailAPI(MethodView):
    
    @jwt_required()
    @role_required("admin", "moderator")
    def put(self, category_id):
        
        category = Category.query.get_or_404(category_id)
        
        try:
            data = CategorySchema().load(request.json)
            category.name = data['name']
            db.session.commit()
            return {"message": "Categoría actualizada"}, 200
        except ValidationError as err:
            return {"error": err.messages}, 400
    
    @jwt_required()
    @role_required("admin")
    def delete(self, category_id):
        
        category = Category.query.get_or_404(category_id)
        
        try:
            db.session.delete(category)
            db.session.commit()
            return {"message": "Categoría eliminada"}, 200
        except:
            return {"error": "No es posible borrar la categoría"}, 400
        

####  USUARIOS (ADMIN) ####
class UserListAPI(MethodView):
    
    @jwt_required()
    @role_required("admin")
    def get(self):
        users = User.query.all()
        return UserSchema(many=True).dump(users), 200


class UserDetailAPI(MethodView):
    
    @jwt_required()
    @role_required("admin", "user", "moderator")
    def get(self, user_id):

        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        role = claims.get('role')
        

        if current_user_id != user_id and role != 'admin':
            return {"error": "No autorizado"}, 403
        
        user = User.query.get_or_404(user_id)
        return UserSchema().dump(user), 200

    @jwt_required()
    @role_required("admin")
    def delete(self, user_id):
        """Solo admin (desactivar usuario)"""
        user = User.query.get_or_404(user_id)
        user.is_active = False
        db.session.commit()

        return {"message": "Usuario desactivado"}, 200

class UserRoleAPI(MethodView):

    
    @jwt_required()
    @role_required("admin")
    def patch(self, user_id):
        user = User.query.get_or_404(user_id)
        
        data = request.json
        if not data or 'role' not in data:
            return {"error": "Falta el rol"}, 400
        
        if data['role'] not in ['user', 'moderator', 'admin']:
            return {"error": "Rol inválido"}, 400
        
        user.role = data['role']
        db.session.commit()
        
        return {"message": "Rol actualizado"}, 200



####  ESTADÍSTICAS  ####

class StatsAPI(MethodView):
    
    @jwt_required()
    @role_required("admin", "moderator")
    def get(self):
        claims = get_jwt()
        role = claims.get('role')
        
        stats = {
            'total_posts': Post.query.count(),
            'total_comments': Comment.query.count(),
            'total_users': User.query.count()
        }
        
        if role == 'admin':
            from datetime import datetime, timedelta
            last_week = datetime.utcnow() - timedelta(days=7)
            stats['posts_last_week'] = Post.query.filter(Post.created_at >= last_week).count()
        
        return jsonify(stats), 200