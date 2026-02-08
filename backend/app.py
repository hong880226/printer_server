"""
Flask主应用 - 远程打印服务
"""
import os
import uuid
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_file, render_template, abort
from flask_cors import CORS
from werkzeug.utils import secure_filename

from backend.config import (
    SERVICE_HOST, SERVICE_PORT, DEBUG_MODE, CUPS_SERVER, CUPS_PORT,
    CUPS_PRINTER_NAME, UPLOAD_FOLDER, MAX_CONTENT_LENGTH, ALLOWED_EXTENSIONS,
    PREVIEW_WIDTH, PREVIEW_HEIGHT, DEFAULT_COPIES, LOG_FILE
)
from backend.cups_service import CupsService
from backend.file_handler import FileHandler
from backend.models import PrintJob, PrintJobStatus

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建应用
app = Flask(__name__, static_url_path='/static', static_folder='/app/frontend/static')
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
CORS(app)

# 初始化服务
cups_service = CupsService(server=CUPS_SERVER, port=CUPS_PORT)
file_handler = FileHandler(UPLOAD_FOLDER, os.path.join(UPLOAD_FOLDER, 'previews'))

# 存储打印任务
print_jobs = {}

def get_printer_name() -> str:
    """获取配置的打印机名称"""
    return CUPS_PRINTER_NAME

@app.route('/')
def index():
    """渲染主页面"""
    return render_template('index.html')

@app.route('/api/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'service': 'Remote Print Service',
        'timestamp': datetime.now().isoformat(),
        'printer': get_printer_name()
    })

@app.route('/api/printers', methods=['GET'])
def get_printers():
    """获取可用打印机列表"""
    try:
        printers = cups_service.get_printers()
        return jsonify({
            'success': True,
            'printers': [p.to_dict() for p in printers]
        })
    except Exception as e:
        logger.error(f"获取打印机列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/printer/status', methods=['GET'])
def get_printer_status():
    """获取打印机状态"""
    try:
        printer_name = request.args.get('printer', get_printer_name())
        status = cups_service.get_printer_status(printer_name)
        return jsonify({
            'success': True,
            'printer': printer_name,
            'status': status
        })
    except Exception as e:
        logger.error(f"获取打印机状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有文件'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': '没有选择文件'}), 400
        
        if file and file_handler.allowed_file(file.filename, ALLOWED_EXTENSIONS):
            # 生成唯一文件名
            original_filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(file_path)
            
            logger.info(f"文件已上传: {file_path}")
            
            # 获取文件信息
            file_info = {
                'filename': original_filename,
                'saved_path': file_path,
                'file_type': file_handler.get_file_type(file_path),
                'size': os.path.getsize(file_path)
            }
            
            # 尝试生成预览
            preview_name = os.path.splitext(unique_filename)[0]
            preview_path = file_handler.generate_preview(
                file_path,
                preview_name,
                PREVIEW_WIDTH,
                PREVIEW_HEIGHT
            )
            
            if preview_path:
                logger.info(f"预览已生成: {preview_path}")
                file_info['preview_path'] = preview_path
            else:
                logger.warning(f"预览生成失败或不支持: {original_filename}")
            
            return jsonify({
                'success': True,
                'file': file_info
            })
        
        return jsonify({'success': False, 'error': '不支持的文件类型'}), 400
    
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files', methods=['GET'])
def list_files():
    """列出已上传的文件"""
    try:
        files = file_handler.list_files(UPLOAD_FOLDER)
        logger.info(f"列出文件: 共 {len(files)} 个文件")
        file_list = []
        
        for f in files:
            preview_name = os.path.splitext(f['filename'])[0]
            preview_file = os.path.join(UPLOAD_FOLDER, 'previews', f'{preview_name}.png')
            has_preview = os.path.exists(preview_file)
            preview_path = f"/previews/{preview_name}.png" if has_preview else None
            
            if has_preview:
                logger.debug(f"  - {f['filename']}: 有预览")
            else:
                logger.debug(f"  - {f['filename']}: 无预览")
            
            file_list.append({
                'filename': f['filename'],
                'path': f['path'],
                'size': file_handler.format_file_size(f['size']),
                'size_bytes': f['size'],
                'created': f['created'].isoformat(),
                'preview_path': preview_path
            })
        
        return jsonify({
            'success': True,
            'files': file_list
        })
    
    except Exception as e:
        logger.error(f"列出文件失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    """删除文件"""
    try:
        # 查找文件
        files = file_handler.list_files(UPLOAD_FOLDER)
        target_file = None
        
        for f in files:
            if f['filename'] == filename:
                target_file = f
                break
        
        if not target_file:
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        # 删除文件
        if file_handler.delete_file(target_file['path']):
            return jsonify({'success': True})
        
        return jsonify({'success': False, 'error': '删除失败'}), 500
    
    except Exception as e:
        logger.error(f"删除文件失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/previews/<path:filename>')
def serve_preview(filename):
    """提供预览图片访问"""
    try:
        preview_path = os.path.join(UPLOAD_FOLDER, 'previews', filename)
        if os.path.exists(preview_path):
            return send_file(preview_path, mimetype='image/png')
        return jsonify({'error': '预览不存在'}), 404
    except Exception as e:
        logger.error(f"提供预览失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/preview/<filename>')
def get_preview(filename):
    """获取文件预览"""
    try:
        preview_path = os.path.join(UPLOAD_FOLDER, 'previews', f"{filename}.png")
        
        if os.path.exists(preview_path):
            return send_file(preview_path, mimetype='image/png')
        
        return jsonify({'error': '预览不存在'}), 404
    
    except Exception as e:
        logger.error(f"获取预览失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/print', methods=['POST'])
def print_file():
    """打印文件"""
    try:
        data = request.json
        
        filename = data.get('filename')
        printer_name = data.get('printer', get_printer_name())
        copies = int(data.get('copies', DEFAULT_COPIES))
        page_range = data.get('page_range')
        
        if not filename:
            return jsonify({'success': False, 'error': '缺少文件名'}), 400
        
        # 查找文件
        files = file_handler.list_files(UPLOAD_FOLDER)
        target_file = None
        
        for f in files:
            if f['filename'] == filename:
                target_file = f
                break
        
        if not target_file:
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        file_path = target_file['path']
        file_type = file_handler.get_file_type(file_path)
        extension = file_handler.get_file_extension(filename).lower()
        
        # Office 文档需要转换为 PDF
        print_file_path = file_path
        if extension in ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']:
            logger.info(f"Office文档需转换为PDF: {filename}")
            pdf_path = file_handler.convert_to_pdf(file_path)
            if pdf_path and pdf_path != file_path:
                print_file_path = pdf_path
                logger.info(f"已转换为PDF: {pdf_path}")
            else:
                return jsonify({'success': False, 'error': '文档转换PDF失败'}), 500
        
        # 创建打印任务
        job_id = str(uuid.uuid4())[:8]
        job = PrintJob(
            job_id=job_id,
            filename=filename,
            file_path=print_file_path,
            file_type=file_type,
            copies=copies,
            page_range=page_range,
            printer_name=printer_name,
            status=PrintJobStatus.PENDING
        )
        
        print_jobs[job_id] = job
        
        logger.info(f"创建打印任务: {job_id}, 文件: {filename}")
        
        # 执行打印
        try:
            cups_job_id = cups_service.print_file(
                printer_name=printer_name,
                file_path=print_file_path,
                job_name=f"RemotePrint-{job_id}",
                copies=copies,
                page_range=page_range
            )
            
            job.status = PrintJobStatus.PRINTING
            job.cups_job_id = cups_job_id
            
            return jsonify({
                'success': True,
                'job': job.to_dict(),
                'cups_job_id': cups_job_id
            })
        
        except Exception as print_error:
            job.status = PrintJobStatus.FAILED
            job.error_message = str(print_error)
            
            return jsonify({
                'success': False,
                'error': str(print_error),
                'job': job.to_dict()
            }), 500
    
    except Exception as e:
        logger.error(f"打印失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """获取打印任务列表"""
    try:
        # 获取本地任务
        local_jobs = [job.to_dict() for job in print_jobs.values()]
        
        # 获取CUPS任务
        cups_jobs = cups_service.get_jobs()
        
        return jsonify({
            'success': True,
            'local_jobs': local_jobs,
            'cups_jobs': cups_jobs
        })
    
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/jobs/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    """取消打印任务"""
    try:
        if job_id in print_jobs:
            job = print_jobs[job_id]
            
            if hasattr(job, 'cups_job_id') and job.cups_job_id:
                cups_service.cancel_job(job.cups_job_id)
            
            job.status = PrintJobStatus.CANCELLED
            return jsonify({'success': True, 'job': job.to_dict()})
        
        return jsonify({'success': False, 'error': '任务不存在'}), 404
    
    except Exception as e:
        logger.error(f"取消任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/convert', methods=['POST'])
def convert_file():
    """转换文件为PDF"""
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'success': False, 'error': '缺少文件名'}), 400
        
        # 查找文件
        files = file_handler.list_files(UPLOAD_FOLDER)
        target_file = None
        
        for f in files:
            if f['filename'] == filename:
                target_file = f
                break
        
        if not target_file:
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        # 转换文件
        pdf_path = file_handler.convert_to_pdf(target_file['path'])
        
        if pdf_path and pdf_path != target_file['path']:
            pdf_filename = os.path.basename(pdf_path)
            
            return jsonify({
                'success': True,
                'original_file': filename,
                'pdf_file': pdf_filename,
                'download_url': f"/uploads/{pdf_filename}"
            })
        
        return jsonify({
            'success': False,
            'error': '文件无法转换或已经是PDF格式'
        }), 400
    
    except Exception as e:
        logger.error(f"文件转换失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/uploads/<path:filename>')
def serve_uploaded_file(filename):
    """提供上传文件的访问"""
    try:
        return send_file(os.path.join(UPLOAD_FOLDER, filename))
    except Exception as e:
        logger.error(f"提供文件失败: {e}")
        abort(404)

if __name__ == '__main__':
    logger.info(f"启动远程打印服务: {SERVICE_HOST}:{SERVICE_PORT}")
    logger.info(f"使用打印机: {get_printer_name()}")
    
    app.run(
        host=SERVICE_HOST,
        port=SERVICE_PORT,
        debug=DEBUG_MODE
    )
