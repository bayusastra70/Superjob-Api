# 🚀 FastAPI Project Setup Guide

Dokumentasi ini menjelaskan cara menjalankan project FastAPI mulai dari persiapan virtual environment, instalasi
dependencies, hingga menjalankan server — mendukung **Windows** dan **Linux/MacOS**.

---

## 📦 1. Persyaratan Sistem

Pastikan sudah terpasang:

* Python **3.9+**
* Git

Cek versi Python:

```bash
python --version
# atau
python3 --version
```

---

## 🧰 2. Setup Virtual Environment (.venv)

### 🔹 Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 🔹 Linux / MacOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Jika berhasil, terminal akan menampilkan prefix:

```
(.venv) user@computer:~/project$
```

---

## 📥 3. Install Dependencies

Pastikan `requirements.txt` berisi:

```
fastapi
uvicorn[standard]
dan dependncies lainnya....
```

Lalu jalankan:

### Windows

```bash
pip install -r requirements.txt
```

### Linux / MacOS

```bash
pip3 install -r requirements.txt
```

### Jalankan migrasi database dan seed user dummy

```bash
alembic upgrade head

python -m app.db.seeds.user_seed
```

---

## 🛠️ 4. Menjalankan Server FastAPI

### Windows

```bash
uvicorn app.main:app --reload
```

### Linux / MacOS

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Akses dokumentasi otomatis:

* Swagger UI → [http://localhost:8000/docs](http://localhost:8000/docs)
* ReDoc → [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📄 5. Contoh File `main.py`

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def home():
    return {"message": "FastAPI is running!"}
```

---

## 🔑 6. Environment Variables (Opsional)

Buat file `.env` untuk menyimpan konfigurasi:

```
PROJECT_NAME=My FastAPI App
SECRET_KEY=your-secret-key
```

---

## 🧹 7. Menonaktifkan Virtual Environment

Cukup jalankan:

```bash
deactivate
```

Berlaku untuk Windows, Linux, dan MacOS.

---

## 🐳 8. (Opsional) Menjalankan Menggunakan Docker

Jika ingin menjalankan lewat Docker:

```bash
docker build -t fastapi-app .
docker run -p 8000:8000 fastapi-app
```

---

## 🔖 9. Release & Versioning

Di projek ini ada helper script untuk melakukan *bumping* versi dan menjalankan `bumpver` secara interaktif. Berikut ringkasan cara kerja dan cara pakai:

### 📁 File yang relevan

* `release.py` (script interaktif — contoh isi ada di repo): menangani pilihan `patch`, `minor`, `major`, `custom`, `as-is`, dan `cancel`, lalu menjalankan `bumpver`.
* `pyproject.toml` — memiliki konfigurasi `tool.bumpver` yang mengatur pola versi, commit/tag/push, dan file yang akan diupdate.
* `app/__init__.py` — menyimpan `__version__ = "MAJOR.MINOR.PATCH"` (harus ada agar `bumpver` dapat menemukan versi saat ini).

> Pastikan `app/__init__.py` berisi line seperti:
>
> ```python
> __version__ = "0.1.0"
> ```

### 📦 Persyaratan untuk release

Install tools yang dibutuhkan (jika belum):

```bash
pip install bumpver questionary
```

`bumpver` akan mengubah versi di file yang dikonfigurasi di `pyproject.toml`, membuat commit, men-tag commit tersebut, dan (opsional) mendorong ke remote.

### ⚙️ Contoh konfigurasi `pyproject.toml`

Contoh konfigurasi yang dipakai di repo ini:

```toml
[tool.bumpver]
current_version = "0.1.0"
version_pattern = "MAJOR.MINOR.PATCH"
commit_message = "chore(release): v{new_version}"
commit = true
tag = true
push = true

[tool.bumpver.file_patterns]
"pyproject.toml" = ['version = "{version}"']
"app/__init__.py" = ['__version__ = "{version}"']
```

### ▶️ Cara menjalankan skrip release (interaktif)

Di root project, jalankan:

```bash
python release.py
```

Lalu pilih salah satu opsi:

* `patch` — menaikkan patch (x.y.(z+1))
* `minor` — menaikkan minor (x.(y+1).0)
* `major` — menaikkan major ((x+1).0.0)
* `custom` — masukkan versi kustom (mis. `1.2.3`)
* `as-is` — tidak mengubah versi
* `cancel` — batal

Script juga menampilkan versi saat ini dan preview versi yang akan dibuat. Setelah konfirmasi, script menjalankan `bumpver update --patch|--minor|--major` atau `bumpver update --set-version X.Y.Z`.

> Catatan: bila ingin mengizinkan file yang belum dicommit (`dirty`), Anda dapat menambahkan opsi `--allow-dirty` pada baris `subprocess.run(cmd, check=True)` di `release.py` (script sudah menyertakan komentar tempat menambahkannya).

### ✅ Setelah release selesai

* `bumpver` akan:

  * Mengupdate versi di file yang terkenda konfigurasi (mis. `pyproject.toml`, `app/__init__.py`)
  * Membuat commit dengan pesan seperti di `commit_message`
  * Membuat git tag
  * Mendorong perubahan ke remote (jika `push = true`)

### 🔁 Mengecek versi saat ini dari Python

Untuk melihat versi yang terpasang di runtime:

```bash
python -c "import app; print(app.__version__)"
```

### 📝 Menambahkan catatan rilis

Script ini tidak otomatis menulis CHANGELOG. Disarankan menambahkan/menyunting `CHANGELOG.md` secara manual sebelum/atau setelah melakukan release untuk menjelaskan perubahan-perubahan.

### 🔧 Troubleshooting singkat

* Jika `bumpver` gagal: jalankan `bumpver update --patch` (atau opsi yang sesuai) secara manual untuk melihat pesan error lengkap.
* Pastikan file `app/__init__.py` sesuai pola `__version__ = "X.Y.Z"` agar regex di script dapat menemukan versi.
* Jika commit/push gagal: periksa credential git dan remote branch.

---

## 🎉 Selesai