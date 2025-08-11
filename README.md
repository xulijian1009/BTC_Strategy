## 1) 创建本地数据库（MySQL 8+）
mysql -uroot -p -e "CREATE DATABASE quant DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

## 2) 导入建表脚本（确保 quant.sql 在仓库根目录）
mysql -uroot -p quant < quant.sql

## 3) 复制并编辑 .env（将示例变量替换为你的本地配置）
cp .env.example .env

## 4) 创建并激活虚拟环境 + 安装依赖
python -m venv .venv
### macOS/Linux
source .venv/bin/activate
### Windows PowerShell
### .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

## 5) 启动应用
python app.py
### 或（若使用 Flask 内置运行器）
## flask run --host=0.0.0.0 --port=5000
