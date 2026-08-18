# Hồ sơ sản phẩm — Secure Learning Portal

## 1. Tên sản phẩm
**Secure Learning Portal (SLP)** — cổng API bảo mật cho tài nguyên học tập.

## 2. Nỗi đau khách hàng
Đơn vị đào tạo hiện có nhu cầu phân phối tài nguyên và dữ liệu cá nhân qua Frontend nhưng chưa có cơ chế đáng tin cậy để:
- xác định request đang đến từ user nào;
- giới hạn API theo vai trò;
- ngăn user đọc/sửa dữ liệu của người khác;
- tích hợp Frontend qua CORS;
- truy vết request và thời gian xử lý;
- xử lý token lỗi một cách nhất quán.

SLP giải quyết các vấn đề này bằng JWT, Current User Dependency, RoleChecker, ownership check, CORS và custom middleware.

## 3. Nhóm người dùng

### Admin
- Quản lý user.
- Khóa/mở khóa tài khoản.
- Tạo, xem, sửa, xóa tài nguyên.

### User
- Đăng nhập.
- Xem current user.
- Xem tài nguyên thuộc quyền sở hữu.
- Cập nhật tài nguyên của mình.

## 4. Chức năng
1. Authentication: login, JWT, current user, expiry/invalid token, inactive account.
2. Authorization: Admin/User, reusable role checker, ownership.
3. Resource management: CRUD theo quyền.
4. CORS: allowlist origins, credentials, preflight OPTIONS.
5. Monitoring: request ID, latency, method/URL/status logs.
6. Health check.
7. Validation/error handling.

## 5. Quy tắc nghiệp vụ
- Authentication failure => 401.
- Authentication thành công nhưng role không đủ => 403.
- Resource không tồn tại => 404.
- Business rule invalid => 400.
- Schema validation failure => 422.
- User inactive không được tiếp tục dùng protected API.
- User không được sửa/xem resource không thuộc mình.
- Không copy role check vào từng endpoint; dùng `require_admin`.

## 6. Phân tích Input/Output

### POST /api/v1/auth/login
Input: email + password.
Output: bearer access token.

### GET /api/v1/auth/me
Input: Bearer JWT.
Output: id, email, full_name, role, is_active, created_at.

### GET /api/v1/resources
Input: Bearer JWT.
Output: list resource theo quyền.

### GET /api/v1/resources/{resource_id}
Input: JWT + resource_id.
Output: resource nếu admin hoặc owner; 403 nếu user khác owner; 404 nếu không có.

### POST /api/v1/resources
Input: title, description, type, URL, owner_id.
Output: resource vừa tạo; chỉ Admin.

## 7. Kiến trúc module

```text
main.py
 ├── core/config.py
 ├── core/database.py
 ├── middleware/request_middleware.py
 ├── dependencies/authentication.py
 ├── dependencies/authorization.py
 ├── routers/auth_router.py
 ├── routers/user_router.py
 ├── routers/resource_router.py
 ├── services/auth_service.py
 ├── services/resource_service.py
 ├── models/models.py
 └── schemas/schemas.py
```

## 8. Luồng dữ liệu

```text
Frontend
  ↓
CORS
  ↓
RequestContextMiddleware
  ↓
Router
  ↓
get_current_user
  ↓
RoleChecker / ownership
  ↓
Service
  ↓
SQLAlchemy
  ↓
SQLite
  ↓
Response
```

## 9. Luồng xác thực

```text
Login
 ↓
Find user
 ↓
Verify bcrypt password
 ↓
Check active
 ↓
Create JWT(sub, role, exp)
 ↓
Frontend stores token
 ↓
Request Authorization: Bearer
 ↓
Decode + verify signature + expiry
 ↓
Read sub
 ↓
Load User
 ↓
Current User
```

## 10. Luồng phân quyền và ownership

```text
JWT
 ↓
Current User
 ├── role=admin → protected admin endpoint
 └── role=user  → user endpoint
                    ↓
                 Resource
                    ↓
          owner_id == current_user.id ?
             ├── yes → allow
             └── no  → 403
```
