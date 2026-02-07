"""
配置文件
"""
import os

# 服务配置
SERVICE_HOST = os.getenv('SERVICE_HOST', '0.0.0.0')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 5000))
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'

# CUPS配置
CUPS_SERVER = os.getenv('CUPS_SERVER', 'localhost')
CUPS_PORT = int(os.getenv('CUPS_PORT', 631))
CUPS_PRINTER_NAME = os.getenv('CUPS_PRINTER_NAME', 'HP_DeskJet_4900')

# 文件配置
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/app/uploads')
MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 50 * 1024 * 1024))  # 50MB
ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'txt', 'png', 'jpg', 'jpeg', 'gif', 'bmp',
    'html', 'htm', 'csv'
}

# 预览配置
PREVIEW_WIDTH = int(os.getenv('PREVIEW_WIDTH', 800))
PREVIEW_HEIGHT = int(os.getenv('PREVIEW_HEIGHT', 1000))

# 打印配置
DEFAULT_COPIES = int(os.getenv('DEFAULT_COPIES', 1))
DEFAULT_PAGE_RANGE = os.getenv('DEFAULT_PAGE_RANGE', None)

# 日志配置
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', '/app/logs/app.log')

# 安全配置
API_KEY = os.getenv('API_KEY', '')
REQUIRE_AUTH = os.getenv('REQUIRE_AUTH', 'false').lower() == 'true'
