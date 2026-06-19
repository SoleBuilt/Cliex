# Hướng dẫn phát hành Cliex (GitLab → GitHub Mirror → PyPI + GitHub Releases)

Tài liệu này hướng dẫn từng bước để user cài Cliex qua **PyPI** hoặc **GitHub Releases**, với GitLab là repo chính và GitHub mirror tự động.

## Tổng quan luồng hoạt động

```
Bạn push tag v0.1.0 lên GitLab
        │
        ├─► GitLab CI: test → build → publish PyPI
        │
        └─► GitLab mirror tag sang GitHub (vài phút)
                    │
                    └─► GitHub Actions: test → build → tạo GitHub Release (kèm .whl)
```

| Kênh                | Ai chạy CI     | User cài                          | User update          |
| ------------------- | -------------- | --------------------------------- | -------------------- |
| **PyPI**            | GitLab CI      | `pipx install cliex`              | `pipx upgrade cliex` |
| **GitHub Releases** | GitHub Actions | tải `.whl` hoặc `pip install` URL | tải release mới      |

---

## Bước 1 — Chuẩn bị tài khoản PyPI (chỉ làm 1 lần)

### 1.1 Tạo tài khoản

1. Vào https://pypi.org/account/register/
2. Xác minh email

### 1.2 Kiểm tra tên package

1. Vào https://pypi.org/project/cliex/
2. Nếu tên `cliex` đã bị chiếm → đổi `name` trong `pyproject.toml` (ví dụ `cliex-quick`) rồi cập nhật README

### 1.3 Tạo API Token

1. PyPI → Account settings → **API tokens** → **Add API token**
2. Scope: **Entire account** (lần đầu) hoặc project cụ thể sau khi đã publish lần 1
3. Copy token (dạng `pypi-AgEIc...`) — **chỉ hiện 1 lần**

### 1.4 (Khuyến nghị) Test trên TestPyPI trước

1. Tạo tài khoản https://test.pypi.org
2. Tạo API token tương tự
3. Lần đầu có thể upload thử:
    ```bash
    pip install flit twine
    python -m flit build
    twine upload --repository testpypi dist/* --username __token__ --password pypi-XXXX
    pip install -i https://test.pypi.org/simple/ cliex
    ```

---

## Bước 2 — Cấu hình GitLab CI (repo chính)

### 2.1 Thêm biến môi trường CI/CD

Trên GitLab project:

1. **Settings** → **CI/CD** → **Variables** → **Add variable**
2. Thêm:

| Key              | Value                     | Flags                                                       |
| ---------------- | ------------------------- | ----------------------------------------------------------- |
| `PYPI_API_TOKEN` | token PyPI (`pypi-Ag...`) | ✅ Masked, ✅ Protected (nếu chỉ tag trên protected branch) |

> **Protected**: nếu bật, tag phải được tạo trên branch được protect (thường là `main`).

### 2.2 Bật GitLab CI

File `.gitlab-ci.yml` đã có sẵn trong repo. Push lên GitLab là pipeline tự chạy.

Kiểm tra: **Build** → **Pipelines** — job `test:branch` chạy khi push code.

### 2.3 Cấu hình mirror sang GitHub (nếu chưa có)

1. GitLab → **Settings** → **Repository** → **Mirroring repositories**
2. **Git repository URL**: `https://github.com/DucHuynhTrung/cliex-quick.git`
3. **Mirror direction**: Push (GitLab → GitHub)
4. **Authentication**: Personal Access Token GitHub
    - GitHub → Settings → Developer settings → **Personal access tokens** → **Fine-grained** hoặc **Classic**
    - Quyền cần: `repo` (full control hoặc contents write)
5. Bật **Only mirror protected branches** nếu muốn (tùy chọn)
6. **Keep divergent refs** — thường nên bật

Mirror sẽ đồng bộ:

- ✅ commits, branches, **tags**
- ❌ GitHub Releases (tạo riêng bằng GitHub Actions)
- ❌ GitLab CI artifacts

---

## Bước 3 — Cấu hình GitHub (mirror repo)

### 3.1 Bật GitHub Actions

1. GitHub repo → **Settings** → **Actions** → **General**
2. **Actions permissions**: Allow all actions
3. **Workflow permissions**: Read and write

File `.github/workflows/release.yml` sẽ được mirror từ GitLab sang GitHub.

### 3.2 Kiểm tra mirror đã hoạt động

Sau khi push lên GitLab, vào GitHub repo — code và file workflow phải xuất hiện.

---

## Bước 4 — Phát hành phiên bản mới

Mỗi lần release, làm **theo thứ tự** sau:

### 4.1 Cập nhật version (2 chỗ)

```toml
# pyproject.toml
version = "0.2.0"
```

```python
# cliex/__init__.py
__version__ = "0.2.0"
```

Hai giá trị **phải giống nhau**.

### 4.2 Commit và push

```bash
git add pyproject.toml cliex/__init__.py
git commit -m "chore: release v0.2.0"
git push origin main
```

(Thay `main` bằng tên default branch trên GitLab nếu khác.)

### 4.3 Tạo tag và push tag

```bash
git tag v0.2.0
git push origin v0.2.0
```

**Quy tắc tag**: `v` + semver, ví dụ `v0.1.0`, `v1.0.0` — khớp regex trong CI.

### 4.4 Theo dõi pipeline

**GitLab** (chạy ngay sau khi push tag):

1. **CI/CD** → **Pipelines** — pipeline tag `v0.2.0`
2. Các job: `test:tag` → `build` → `publish:pypi`
3. Nếu `publish:pypi` xanh → package đã lên https://pypi.org/project/cliex/

**GitHub** (sau khi mirror tag, thường 1–5 phút):

1. **Actions** → workflow **Release**
2. Job tạo GitHub Release tại https://github.com/DucHuynhTrung/cliex-quick/releases
3. Release kèm file `.whl` và `.tar.gz`

---

## Bước 5 — Hướng dẫn user cài đặt

Copy vào README hoặc gửi cho user:

### Cách 1 — PyPI (khuyến nghị)

```bash
# Cài (dùng pipx để tách môi trường)
pipx install cliex

# Kiểm tra
cliex list

# Cập nhật khi có bản mới
pipx upgrade cliex
```

Hoặc:

```bash
pip install cliex
pip install -U cliex   # update
```

### Cách 2 — GitHub Releases

```bash
# Thay VERSION bằng tag, ví dụ 0.2.0
pip install https://github.com/DucHuynhTrung/cliex-quick/releases/download/v0.2.0/cliex-0.2.0-py3-none-any.whl
```

Hoặc tải file `.whl` từ trang Releases → cài local:

```bash
pip install path/to/cliex-0.2.0-py3-none-any.whl
```

---

## Xử lý sự cố

### GitLab CI: `publish:pypi` failed — invalid credentials

- Kiểm tra `PYPI_API_TOKEN` trong GitLab CI Variables
- Token hết hạn → tạo token mới
- Username luôn là `__token__`, password là token

### GitLab CI: package version already exists

- PyPI **không cho upload lại** cùng version
- Tăng version trong `pyproject.toml` + `__init__.py`, tag mới (`v0.2.1`)

### GitHub Actions không chạy

- Tag đã mirror sang GitHub chưa? (`git ls-remote --tags https://github.com/...`)
- Actions đã bật chưa?
- File `.github/workflows/release.yml` có trên GitHub không?

### Mirror GitLab → GitHub không sync tag

- Kiểm tra mirror status trên GitLab (Settings → Repository → Mirroring)
- Token GitHub còn hạn không
- Thử **Trigger immediate pull/push** trên trang mirror

### User `pip install cliex` không thấy bản mới

- PyPI cache vài phút — đợi hoặc `pip install -U cliex`
- Xác nhận version trên https://pypi.org/project/cliex/

---

## Checklist nhanh mỗi lần release

- [ ] Tăng `version` trong `pyproject.toml`
- [ ] Tăng `__version__` trong `cliex/__init__.py`
- [ ] Commit + push lên GitLab `main`
- [ ] `git tag vX.Y.Z` + `git push origin vX.Y.Z`
- [ ] GitLab pipeline xanh (đặc biệt `publish:pypi`)
- [ ] GitHub Actions xanh (Release có file đính kèm)
- [ ] Test: `pipx install cliex` hoặc `pip install -U cliex`

---

## Phát hành thủ công (không qua CI)

Khi cần upload PyPI từ máy local:

```bash
pip install flit twine
python -m flit build
twine check dist/*
twine upload dist/* --username __token__ --password pypi-YOUR_TOKEN
```

GitHub Release vẫn nên tạo bằng push tag (Actions) hoặc tạo thủ công trên GitHub UI và upload `dist/*`.
