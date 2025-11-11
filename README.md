# MiniBlog API REST
# Alumnos: Facundo Puig - Gonzalo Riva

API REST con autenticación JWT y sistema de roles (admin, moderador, usuario) para un blog.

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd EFI-Miniblog-Flask
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# Activar entorno virtual:
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar base de datos

Crear la base de datos en MySQL:

```bash
mysql -u root -p
CREATE DATABASE miniblog;
exit
```

Si es necesario, editar la conexión en 'app.py':

```python
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:@localhost/miniblog"
```

Importar el dump

```bash
mysql -u root -p miniblog < database_dump.sql
```

### 5. Ejecutar la app

```bash
flask run --reload
```

La API estará disponible en: `http://localhost:5000`

---

## Credenciales de Prueba

### Administrador
- **Email:** 'admin@admin.com'
- **Password:** `admin`

### Moderador
- **Email:** 'moderador@moderador.com'
- **Password:** `moderador`

### Usuario
- **Email:** 'usuario@usuario.com'
- **Password:** 'usuario'

## Documentación de Endpoints

La API usa `http://localhost:5000/api` como base.

Para los endpoints que necesitan autenticación, tenés que incluir el token en el header:
```
Authorization: Bearer {tu_token}
```

---

### Autenticación

**Registrarse:**
```
POST /api/register

{
  "username": "Juan",
  "email": "juan@example.com",
  "password": "pass123"
}
```

**Login:**
```
POST /api/login

{
  "email": "juan@example.com",
  "password": "pass123"
}

// Te devuelve el token que necesitás para los demás endpoints
```

---

### Posts

**Ver todos los posts** (público):
```
GET /api/posts
```

**Ver un post específico** (público):
```
GET /api/posts/1
```

**Crear un post** (necesita login):
```
POST /api/posts
Authorization: Bearer {token}

{
  "title": "Mi post",
  "content": "El contenido..."
}
```

**Editar un post** (solo si sos el autor o admin):
```
PUT /api/posts/1
Authorization: Bearer {token}

{
  "title": "Título nuevo",
  "content": "Contenido nuevo..."
}
```

**Eliminar un post** (solo si sos el autor o admin):
```
DELETE /api/posts/1
Authorization: Bearer {token}
```

---

### Comentarios

**Ver comentarios de un post** (público):
```
GET /api/posts/1/comments
```

**Comentar en un post** (necesita login):
```
POST /api/posts/1/comments
Authorization: Bearer {token}

{
  "text": "Buen post!"
}
```

**Editar un comentario** (solo si sos el autor):
```
PUT /api/comments/1
Authorization: Bearer {token}

{
  "text": "Comentario editado"
}
```

**Eliminar un comentario** (si sos el autor, moderador o admin):
```
DELETE /api/comments/1
Authorization: Bearer {token}
```

---

### Categorías

**Ver todas las categorías** (público):
```
GET /api/categories
```

**Crear una categoría** (moderador o admin):
```
POST /api/categories
Authorization: Bearer {token}

{
  "name": "Tecnología"
}
```

**Editar una categoría** (moderador o admin):
```
PUT /api/categories/1
Authorization: Bearer {token}

{
  "name": "Tech"
}
```

**Eliminar una categoría** (solo admin):
```
DELETE /api/categories/1
Authorization: Bearer {token}
```

---

### Usuarios (Administración)

**Ver mi perfil:**
```
GET /api/users/me
Authorization: Bearer {token}
```

**Ver todos los usuarios** (solo admin):
```
GET /api/users
Authorization: Bearer {token}
```

**Ver un usuario específico** (el usuario mismo o admin):
```
GET /api/users/1
Authorization: Bearer {token}
```

**Cambiar el rol de un usuario** (solo admin):
```
PATCH /api/users/1/role
Authorization: Bearer {token}

{
  "role": "moderator"  // puede ser: user, moderator o admin
}
```

**Desactivar un usuario** (solo admin):
```
DELETE /api/users/1
Authorization: Bearer {token}
```

---

### Estadísticas

**Ver estadísticas del sistema** (moderador o admin):
```
GET /api/stats
Authorization: Bearer {token}

// Los moderadores ven: total_posts, total_comments, total_users
// Los admin ven eso + posts_last_week
```

---

## Permisos por Rol

**Usuario (user):**
- Puede ver posts y comentarios
- Puede crear sus propios posts
- Puede editar/eliminar solo sus posts y comentarios

**Moderador (moderator):**
- Todo lo del usuario +
- Puede eliminar cualquier comentario
- Puede crear/editar categorías
- Puede ver estadísticas

**Administrador (admin):**
- Todo lo del moderador +
- Puede eliminar cualquier post
- Puede eliminar categorías
- Puede gestionar usuarios (cambiar roles, desactivar)
- Puede ver estadísticas completas

---
