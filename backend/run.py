"""
Flask 应用启动入口
"""
import os
from app import create_app

# 获取配置名称
config_name = os.environ.get("FLASK_ENV", "dev")

# 创建应用实例
app = create_app(config_name)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
