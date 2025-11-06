from marshmallow import Schema, fields, validate


#### AUTENTICACION ####

class RegisterSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=64))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)


#### USUARIO ####

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    email = fields.Email(required=True)
    role = fields.Str(dump_only=True)
    is_active = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


#### POST ####

class PostSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    content = fields.Str(required=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    is_published = fields.Bool(dump_only=True)
    user_id = fields.Int(dump_only=True)
    author = fields.Nested('UserSchema', only=['id', 'name'], dump_only=True)


#### COMENTARIO ####

class CommentSchema(Schema):
    id = fields.Int(dump_only=True)
    text = fields.Str(required=True, validate=validate.Length(min=1))
    created_at = fields.DateTime(dump_only=True)
    is_visible = fields.Bool(dump_only=True)
    user_id = fields.Int(dump_only=True)
    post_id = fields.Int(dump_only=True)
    author = fields.Nested('UserSchema', only=['id', 'name'], dump_only=True)


#### CATEGORIA ####

class CategorySchema(Schema):
    """Schema para Categoria"""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=50))