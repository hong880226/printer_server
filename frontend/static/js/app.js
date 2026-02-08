/**
 * 远程打印服务 - 前端应用
 */

class PrintService {
    constructor() {
        this.apiBase = '/api';
        this.files = [];
        this.selectedFile = null;
        this.currentPreviewFile = null;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadPrinterStatus();
        this.loadPrinters();
        this.loadFiles();
        this.loadJobs();
        
        // 定时刷新状态
        setInterval(() => this.loadPrinterStatus(), 10000);
        setInterval(() => this.loadJobs(), 5000);
    }

    bindEvents() {
        // 文件上传
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        
        uploadArea.addEventListener('click', () => fileInput.click());
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            this.uploadFiles(files);
        });
        
        fileInput.addEventListener('change', (e) => {
            this.uploadFiles(e.target.files);
            e.target.value = '';
        });

        // 刷新按钮
        document.getElementById('refreshFilesBtn').addEventListener('click', () => {
            this.loadFiles();
        });
        
        document.getElementById('refreshJobsBtn').addEventListener('click', () => {
            this.loadJobs();
        });

        // 预览模态框
        document.getElementById('closePreview').addEventListener('click', () => {
            this.closePreview();
        });
        
        document.getElementById('previewModal').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                this.closePreview();
            }
        });
        
        document.getElementById('printFromPreview').addEventListener('click', () => {
            if (this.currentPreviewFile) {
                this.printFile(this.currentPreviewFile.filename);
            }
        });
        
        document.getElementById('deleteFromPreview').addEventListener('click', () => {
            if (this.currentPreviewFile) {
                this.deleteFile(this.currentPreviewFile.filename);
                this.closePreview();
            }
        });
    }

    async uploadFiles(files) {
        if (!files || files.length === 0) return;
        
        const uploadProgress = document.getElementById('uploadProgress');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        uploadProgress.style.display = 'flex';
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch(`${this.apiBase}/upload`, {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    this.showNotification(`文件 "${file.name}" 上传成功`, 'success');
                    this.loadFiles();
                } else {
                    this.showNotification(`文件 "${file.name}" 上传失败: ${result.error}`, 'error');
                }
                
                // 更新进度
                const progress = ((i + 1) / files.length) * 100;
                progressFill.style.width = `${progress}%`;
                progressText.textContent = `${Math.round(progress)}%`;
                
            } catch (error) {
                this.showNotification(`文件 "${file.name}" 上传失败: ${error.message}`, 'error');
            }
        }
        
        // 重置进度条
        setTimeout(() => {
            uploadProgress.style.display = 'none';
            progressFill.style.width = '0%';
            progressText.textContent = '0%';
        }, 1000);
    }

    async loadPrinters() {
        try {
            const response = await fetch(`${this.apiBase}/printers`);
            const result = await response.json();
            
            const select = document.getElementById('printerSelect');
            select.innerHTML = '';
            
            if (result.success && result.printers.length > 0) {
                result.printers.forEach(printer => {
                    const option = document.createElement('option');
                    option.value = printer.name;
                    option.textContent = `${printer.name} (${printer.info || '本地打印机'})`;
                    select.appendChild(option);
                });
            } else {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = '未找到打印机';
                select.appendChild(option);
            }
            
        } catch (error) {
            console.error('加载打印机列表失败:', error);
        }
    }

    async loadPrinterStatus() {
        try {
            const response = await fetch(`${this.apiBase}/printer/status`);
            const result = await response.json();
            
            const statusDot = document.getElementById('statusDot');
            const statusText = document.getElementById('statusText');
            
            if (result.success) {
                statusDot.className = 'status-dot';
                
                switch (result.status) {
                    case 'idle':
                        statusDot.classList.add('online');
                        statusText.textContent = '就绪';
                        break;
                    case 'processing':
                        statusDot.classList.add('busy');
                        statusText.textContent = '工作中';
                        break;
                    case 'stopped':
                        statusDot.classList.add('offline');
                        statusText.textContent = '已停止';
                        break;
                    default:
                        statusDot.classList.add('offline');
                        statusText.textContent = '未知状态';
                }
            } else {
                statusDot.classList.add('offline');
                statusText.textContent = '连接失败';
            }
            
        } catch (error) {
            const statusDot = document.getElementById('statusDot');
            const statusText = document.getElementById('statusText');
            statusDot.classList.add('offline');
            statusText.textContent = '连接失败';
        }
    }

    async loadFiles() {
        try {
            const response = await fetch(`${this.apiBase}/files`);
            const result = await response.json();
            
            if (result.success) {
                this.files = result.files;
                this.renderFiles(result.files);
            }
            
        } catch (error) {
            this.showNotification('加载文件列表失败', 'error');
        }
    }

    renderFiles(files) {
        const grid = document.getElementById('filesGrid');
        const emptyState = document.getElementById('emptyState');
        
        if (!files || files.length === 0) {
            grid.innerHTML = '';
            grid.appendChild(emptyState);
            emptyState.style.display = 'block';
            return;
        }
        
        emptyState.style.display = 'none';
        grid.innerHTML = '';
        
        files.forEach(file => {
            const card = this.createFileCard(file);
            grid.appendChild(card);
        });
    }

    createFileCard(file) {
        const card = document.createElement('div');
        card.className = 'file-card';
        card.dataset.filename = file.filename;
        
        const extension = file.filename.split('.').pop().toLowerCase();
        const iconClass = this.getIconClass(extension);
        
        let previewHtml;
        if (file.preview_path) {
            previewHtml = `<img class="file-preview" src="${file.preview_path}" alt="${file.filename}">`;
        } else {
            previewHtml = `<div class="file-preview-placeholder">
                <span class="file-icon ${iconClass}">${this.getFileIcon(extension)}</span>
            </div>`;
        }
        
        card.innerHTML = `
            ${previewHtml}
            <div class="file-info">
                <div class="file-name" title="${file.filename}">${file.filename}</div>
                <div class="file-size">${file.size}</div>
            </div>
            <div class="file-actions">
                <button class="btn btn-primary btn-sm preview-btn" data-filename="${file.filename}">预览</button>
                <button class="btn btn-secondary btn-sm print-btn" data-filename="${file.filename}">打印</button>
                <button class="btn btn-danger btn-sm delete-btn" data-filename="${file.filename}">删除</button>
            </div>
        `;
        
        // 绑定事件
        card.querySelector('.preview-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            this.openPreview(file);
        });
        
        card.querySelector('.print-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            this.printFile(file.filename);
        });
        
        card.querySelector('.delete-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            this.deleteFile(file.filename);
        });
        
        card.addEventListener('click', () => {
            this.openPreview(file);
        });
        
        return card;
    }

    getFileIcon(extension) {
        const icons = {
            'pdf': '📄',
            'doc': '📝', 'docx': '📝',
            'xls': '📊', 'xlsx': '📊',
            'ppt': '📑', 'pptx': '📑',
            'txt': '📃',
            'png': '🖼️', 'jpg': '🖼️', 'jpeg': '🖼️', 'gif': '🖼️', 'bmp': '🖼️',
            'html': '🌐', 'htm': '🌐',
            'csv': '📈'
        };
        return icons[extension] || '📎';
    }

    getIconClass(extension) {
        const classes = {
            'pdf': 'pdf',
            'doc': 'doc', 'docx': 'docx',
            'xls': 'xls', 'xlsx': 'xlsx',
            'ppt': 'ppt', 'pptx': 'pptx',
            'txt': 'txt',
            'png': 'image', 'jpg': 'image', 'jpeg': 'image', 'gif': 'image', 'bmp': 'image',
            'html': 'html', 'htm': 'html'
        };
        return classes[extension] || '';
    }

    openPreview(file) {
        this.currentPreviewFile = file;
        
        const modal = document.getElementById('previewModal');
        const title = document.getElementById('previewTitle');
        const image = document.getElementById('previewImage');
        const placeholder = document.getElementById('previewPlaceholder');
        
        title.textContent = file.filename;
        
        if (file.preview_path) {
            image.src = file.preview_path;
            image.style.display = 'block';
            placeholder.style.display = 'none';
        } else {
            image.style.display = 'none';
            placeholder.style.display = 'block';
            placeholder.innerHTML = `<span style="font-size: 4rem;">${this.getFileIcon(file.filename.split('.').pop())}</span><p>暂无预览</p>`;
        }
        
        modal.classList.add('show');
    }

    closePreview() {
        const modal = document.getElementById('previewModal');
        modal.classList.remove('show');
        this.currentPreviewFile = null;
    }

    async printFile(filename) {
        const printer = document.getElementById('printerSelect').value;
        const copies = document.getElementById('copiesInput').value;
        const pageRange = document.getElementById('pageRangeInput').value;
        
        if (!printer) {
            this.showNotification('请选择打印机', 'warning');
            return;
        }
        
        if (!filename) {
            this.showNotification('请选择要打印的文件', 'warning');
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBase}/print`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filename: filename,
                    printer: printer,
                    copies: parseInt(copies) || 1,
                    page_range: pageRange || null
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification(`打印任务已提交: ${result.job.job_id}`, 'success');
                this.loadJobs();
                
                // 清空页码范围输入
                document.getElementById('pageRangeInput').value = '';
            } else {
                this.showNotification(`打印失败: ${result.error}`, 'error');
            }
            
        } catch (error) {
            this.showNotification(`打印失败: ${error.message}`, 'error');
        }
    }

    async deleteFile(filename) {
        if (!confirm(`确定要删除文件 "${filename}" 吗？`)) {
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBase}/files/${encodeURIComponent(filename)}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification(`文件已删除`, 'success');
                this.loadFiles();
            } else {
                this.showNotification(`删除失败: ${result.error}`, 'error');
            }
            
        } catch (error) {
            this.showNotification(`删除失败: ${error.message}`, 'error');
        }
    }

    async loadJobs() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);
            
            const response = await fetch(`${this.apiBase}/jobs`, {
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            
            const result = await response.json();
            
            if (result.success) {
                this.renderJobs(result.cups_jobs);
            }
            
        } catch (error) {
            if (error.name === 'AbortError') {
                console.warn('加载打印任务超时');
            } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
                console.warn('无法连接到CUPS服务，检查CUPS状态');
            } else {
                console.error('加载打印任务失败:', error);
            }
        }
    }

    renderJobs(jobs) {
        const list = document.getElementById('jobsList');
        
        if (!jobs || jobs.length === 0) {
            list.innerHTML = '<div class="empty-state"><p>暂无打印任务</p></div>';
            return;
        }
        
        list.innerHTML = '';
        
        jobs.forEach(job => {
            const item = document.createElement('div');
            item.className = 'job-item';
            
            const statusClass = this.getJobStatusClass(job.state);
            
            item.innerHTML = `
                <div class="job-info">
                    <div class="job-name">
                        ${job.name || '未知任务'}
                        <span class="job-status ${statusClass}">${this.getJobStatusText(job.state)}</span>
                    </div>
                    <div class="job-meta">
                        打印机: ${job.printer || '未知'} | 
                        用户: ${job.user || '未知'} | 
                        大小: ${this.formatSize(job.size)}
                    </div>
                </div>
                ${job.state === 3 ? `<button class="btn btn-danger btn-sm cancel-job-btn" data-job-id="${job.job_id}">取消</button>` : ''}
            `;
            
            // 取消任务按钮
            const cancelBtn = item.querySelector('.cancel-job-btn');
            if (cancelBtn) {
                cancelBtn.addEventListener('click', () => {
                    this.cancelJob(job.job_id);
                });
            }
            
            list.appendChild(item);
        });
    }

    getJobStatusClass(state) {
        const stateMap = {
            1: 'pending',
            2: 'pending',
            3: 'completed',
            4: 'pending',
            5: 'cancelled',
            6: 'cancelled',
            7: 'cancelled',
            8: 'failed',
            9: 'failed'
        };
        return stateMap[state] || 'pending';
    }

    getJobStatusText(state) {
        const stateMap = {
            1: '等待中',
            2: '排队中',
            3: '完成',
            4: '处理中',
            5: '已停止',
            6: '已取消',
            7: '已中止',
            8: '失败',
            9: '失败'
        };
        return stateMap[state] || '未知';
    }

    async cancelJob(jobId) {
        if (!confirm('确定要取消这个打印任务吗？')) {
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBase}/jobs/${jobId}/cancel`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('任务已取消', 'success');
                this.loadJobs();
            } else {
                this.showNotification(`取消失败: ${result.error}`, 'error');
            }
            
        } catch (error) {
            this.showNotification(`取消失败: ${error.message}`, 'error');
        }
    }

    formatSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notifications');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        container.appendChild(notification);
        
        // 3秒后移除
        setTimeout(() => {
            notification.style.animation = 'fadeOut 0.3s ease forwards';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.printService = new PrintService();
});
