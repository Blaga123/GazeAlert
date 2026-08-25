# 🤝 Contributing to GazeAlert AI Suite

Thank you for your interest in contributing to **GazeAlert AI**! We welcome contributions from computer vision researchers, Python engineers, UI/UX designers, and students worldwide.

---

## 🛠️ Development Setup

1. **Fork and Clone the Repository**:
   ```bash
   git clone https://github.com/Blaga123/GazeAlert.git
   cd GazeAlert
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   ```

3. **Install Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Run Verification Test Suite**:
   ```bash
   python test_system.py
   ```

---

## 📐 Code Style & Architecture Guidelines
- **Python Standard**: Adhere to PEP 8 and use type annotations (`typing.Tuple`, `typing.Optional`, etc.).
- **Zero-Copy Performance**: All frame manipulation loops should use vectorized NumPy operations or OpenCV C++ bindings. Avoid per-pixel Python iterations.
- **Atomic Commits**: Write clear, descriptive commit messages (e.g., `feat: Add adaptive blink filter`, `fix: Resolve canvas aspect-ratio resize`).

---

## 📜 Pull Request Process
1. Create a feature branch: `git checkout -b feature/amazing-feature`
2. Run test suite: `python test_system.py`
3. Commit your changes: `git commit -m "feat: Add amazing feature"`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request on GitHub.
