# Python Docker Template

A minimal, reusable template for containerized Python 3.10 projects using Docker. Designed for fast setup, isolated environments, and cross-platform compatibility (Windows, Linux, WSL, Git Bash).

---

## 🚀 Features

- Python 3.10 runtime (Dockerized)
- Cross-platform run scripts (`.bat` for Windows, `.sh` for Unix/WSL)
- Auto-installs dependencies from `requirements.txt`
- Isolated from host system — no virtualenvs or pip clutter
- Clean one-command execution of any Python script

---

## 📁 Project Structure

```
.
├── Dockerfile             # Python 3.10 container setup
├── requirements.txt       # Python dependencies
├── run.sh                 # Run helper for Unix/WSL
├── run.bat                # Run helper for Windows
└── src/
    └── main.py            # Example Python script
```

---

## 🧪 Getting Started

### 🐧 Unix / WSL / Git Bash
```bash
./run.sh main.py
./run.sh main.py YourName  # with arguments
```

### 🪟 Windows (CMD or PowerShell)
```cmd
run.bat main.py
run.bat main.py YourName  # with arguments
```

---

## 🛠️ Modify for Your Project

- Add your source files inside the `src/` folder
- Update `requirements.txt` with any Python packages you need
- Rebuild the Docker image only if `requirements.txt` changes:
  ```bash
  docker build -t py310-base .
  ```

---

## ♻️ Clean Rebuild (Optional)
To force a full rebuild:
```bash
docker rmi py310-base
docker build -t py310-base .
```

---

## 🔒 Why Docker?

- No virtualenvs or global Python conflicts
- Reproducible builds across machines
- Great for training, experiments, APIs, and CLI tools

---

## 📦 Dependencies

- Docker Desktop (Windows/Linux/macOS)
- Python dependencies managed via `requirements.txt`

---

## 📝 License

MIT License. Use freely.
