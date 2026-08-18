# Secure Learning Portal

Một API quản lý tài nguyên học tập xây dựng bằng Python + FastAPI, đáp ứng bài toán xác thực JWT, phân quyền Admin/User, kiểm tra quyền sở hữu, CORS và giám sát request.

## 1. Mục tiêu sản phẩm

### Nỗi đau khách hàng
Đơn vị đào tạo cần một API mà Frontend có thể gọi an toàn, biết chính xác người dùng hiện tại là ai và ngăn người dùng truy cập hoặc chỉnh sửa dữ liệu ngoài quyền của mình.

### Nhóm người dùng
- **Admin:** quản lý người dùng và tài nguyên học tập.
- **User:** xem và cập nhật tài nguyên thuộc quyền sở hữu của mình.

### Quy tắc nghiệp vụ
1. Chỉ tài khoản đang hoạt động mới được đăng nhập và gọi API bảo vệ.
2. JWT phải hợp lệ, còn hạn và có `sub`.
3. Admin có quyền quản lý người dùng và tài nguyên.
4. User không được gọi API Admin.
5. User chỉ đọc/cập nhật resource nếu `resource.owner_id == current_user.id`.
6. Truy cập resource không tồn tại trả `404`.
7. Sai/thiếu token trả `401`; có token hợp lệ nhưng thiếu quyền trả `403`.
8. Dữ liệu đầu vào sai schema trả `422` và không làm ứng dụng crash.
9. CORS chỉ cho phép các origin đã cấu hình; credentials được bật nhưng không dùng wildcard `*`.
10. Request `OPTIONS` được CORS middleware xử lý trước dependency xác thực.

## 2. Kiến trúc

```text
Frontend
   |
   v
CORS Middleware
   |
   v
RequestContextMiddleware
(request ID + timing + logging)
   |
   v
Router
   |
   v
Authentication Dependency
(get_current_user -> decode JWT -> load user)
   |
   v
Authorization Dependency / Ownership Check
(RoleChecker / require_owner_or_admin)
   |
   v
Service
   |
   v
SQLAlchemy Session
   |
   v
SQLite Data Store
   |
   v
Response + X-Request-ID + X-Process-Time-ms
```

### Trách nhiệm module
- `core/config.py`: đọc cấu hình từ `.env`.
- `core/database.py`: engine, session và SQLAlchemy Base.
- `models/`: mô hình `User`, `Resource`.
- `schemas/`: request/response schema Pydantic.
- `services/`: business logic cho authentication và resource.
- `dependencies/authentication.py`: OAuth2 bearer + current user.
- `dependencies/authorization.py`: role checker và ownership check.
- `middleware/request_middleware.py`: request ID, đo latency, log method/URL/status.
- `routers/`: HTTP endpoints.
- `main.py`: tạo ứng dụng, CORS, middleware, exception handler, startup seed.
- `tests/`: kiểm thử authentication, authorization, ownership, CORS và validation.

## 3. Luồng JWT

```text
POST /api/v1/auth/login
  |
  +--> tìm User theo email
  +--> Argon2 verify(password)
  +--> kiểm tra is_active
  +--> tạo JWT: sub, role, exp
  +--> trả access_token

Request bảo vệ
  |
  +--> Authorization: Bearer <token>
  +--> decode + verify signature + exp
  +--> đọc sub
  +--> lấy User trong DB
  +--> kiểm tra user tồn tại / active
  +--> trả current_user cho endpoint
```

JWT không lưu password; secret key lấy từ environment.

## 4. Luồng phân quyền

```text
current_user
   |
   +--> role == admin ? --> API Admin
   |                         |
   |                         +--> cho phép
   |
   +--> role == user ------> API Admin => 403

Resource request
   |
   +--> resource tồn tại ? --no--> 404
   |
   +--> admin ? ------------yes--> allow
   |
   +--> owner_id == user.id ? --yes--> allow
   |
   +--> no -------------------------> 403
```

## 5. Danh sách API

| Method | Endpoint | Auth | Quyền | Mục đích |
|---|---|---|---|---|
| POST | `/api/v1/auth/login` | Không | Public | Đăng nhập và cấp JWT |
| GET | `/api/v1/auth/me` | JWT | Active user | Current user |
| GET | `/api/v1/health` | Không | Public | Health check |
| GET | `/api/v1/users` | JWT | Admin | Danh sách user |
| POST | `/api/v1/users` | JWT | Admin | Tạo user |
| PATCH | `/api/v1/users/{user_id}/status` | JWT | Admin | Khóa/mở khóa user |
| GET | `/api/v1/resources` | JWT | User/Admin | User xem resource của mình; Admin xem toàn bộ |
| GET | `/api/v1/resources/{resource_id}` | JWT | Owner/Admin | Xem resource có kiểm tra ownership |
| POST | `/api/v1/resources` | JWT | Admin | Tạo resource |
| PATCH | `/api/v1/resources/{resource_id}` | JWT | Owner/Admin | Cập nhật resource |
| DELETE | `/api/v1/resources/{resource_id}` | JWT | Admin | Xóa resource |

## 6. Input/Output chính

### Login
**Input**
```json
{
  "email": "user@example.com",
  "password": "User12345!"
}
```

**Output**
```json
{
  "access_token": "<JWT>",
  "token_type": "bearer"
}
```

### Resource create
**Input**
```json
{
  "title": "FastAPI JWT",
  "description": "Tài liệu xác thực",
  "resource_type": "document",
  "content_url": "https://example.com/file.pdf",
  "owner_id": 2
}
```

### Resource response
```json
{
  "id": 1,
  "title": "FastAPI JWT",
  "description": "Tài liệu xác thực",
  "resource_type": "document",
  "content_url": "https://example.com/file.pdf",
  "owner_id": 2,
  "created_at": "2026-08-18T00:00:00Z",
  "updated_at": "2026-08-18T00:00:00Z"
}
```

## 7. Xử lý ngoại lệ

| Tình huống | Status |
|---|---:|
| Sai email/password | 401 |
| Thiếu token | 401 |
| Token sai chữ ký | 401 |
| Token hết hạn | 401 |
| Token thiếu `sub` | 401 |
| User không tồn tại | 401 |
| User bị khóa | 403 |
| User gọi API Admin | 403 |
| User truy cập resource của người khác | 403 |
| Resource không tồn tại | 404 |
| Business rule không hợp lệ (vd. email trùng) | 400 |
| Input sai kiểu/thiếu field | 422 |
| OPTIONS preflight | Không yêu cầu JWT |

## 8. Chạy chương trình

### Windows PowerShell
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn main:app --reload
```

### Linux/macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

Swagger: `http://127.0.0.1:8000/docs`
ReDoc: `http://127.0.0.1:8000/redoc`
Health: `http://127.0.0.1:8000/api/v1/health`

## 9. Tài khoản mẫu

| Role | Email | Password |
|---|---|---|
| Admin | `admin@example.com` | `Admin123!` |
| User | `user@example.com` | `User12345!` |

Các tài khoản này được seed tự động khi chạy lần đầu. Trong môi trường thật, hãy đổi password và `SECRET_KEY`.

## 10. Test

```bash
pytest -q
```

Test bao phủ:
- health check
- login/current user
- missing token
- sai password
- Admin/User role
- ownership
- invalid input
- CORS preflight OPTIONS
- user chỉ xem resource của mình

## 11. CORS

Mặc định:
- `http://localhost:3000`
- `http://localhost:5173`

`allow_credentials=True` nhưng `allow_origins` không dùng `*`. Có thể đổi danh sách bằng biến `CORS_ORIGINS` trong `.env`.

## 12. Gợi ý bảo mật khi triển khai thật

- Dùng secret ngẫu nhiên dài và quản lý bằng secret manager.
- Bật HTTPS.
- Đưa SQLite sang PostgreSQL khi cần concurrent workload lớn.
- Dùng Alembic cho migration.
- Không dùng password mẫu trong production.
- Có refresh token / token rotation nếu sản phẩm cần phiên đăng nhập dài.
- Thêm rate limiting, audit log và CSRF strategy tùy kiến trúc Frontend.
