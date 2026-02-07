"""
应用启动脚本
"""
import os
import sys

# 确保backend模块可以被导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import app

if __name__ == '__main__':
    port = int(os.environ.get('SERVICE_PORT', 5000))
    host = os.environ.get('SERVICE_HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG_MODE', 'false').lower() == 'true'
    
    print(f"""
    ========================================
    🖨️  远程打印服务
    ========================================
    服务地址: http://{host}:{port}
    调试模式: {'开启' if debug else '关闭'}
    ========================================
    """)
    
    app.run(host=host, port=port, debug=debug)
