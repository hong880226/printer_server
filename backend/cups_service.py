"""
CUPS服务封装
"""
import cups
import logging
import os
from typing import List, Optional
from backend.models import Printer, PrintJobStatus

logger = logging.getLogger(__name__)

class CupsService:
    def __init__(self, server: str = 'localhost', port: int = 631):
        self.server = server
        self.port = port
        self._connection = None
    
    def _create_connection(self):
        """创建新的CUPS连接"""
        try:
            # 优先使用本地socket
            if os.path.exists('/run/cups/cups.sock'):
                logger.debug("通过本地 socket 连接到 CUPS")
                return cups.Connection()
            else:
                logger.debug(f"通过 TCP 连接到 CUPS: {self.server}:{self.port}")
                return cups.Connection(host=self.server, port=self.port)
        except Exception as e:
            logger.error(f"创建CUPS连接失败: {e}")
            raise
    
    def connect(self) -> bool:
        """显式建立连接"""
        try:
            self._connection = self._create_connection()
            logger.info("CUPS连接已建立")
            return True
        except Exception as e:
            logger.error(f"CUPS连接失败: {e}")
            return False
    
    def _ensure_connection(self):
        """确保有有效连接，如果连接失效则重新创建"""
        try:
            # 尝试使用现有连接
            if self._connection is not None:
                # 通过调用一个轻量级操作来测试连接是否有效
                self._connection.getPrinters()
                return self._connection
        except Exception as e:
            logger.warning(f"CUPS连接已失效，重新连接: {e}")
        
        # 重新创建连接
        self._connection = self._create_connection()
        return self._connection
    
    def get_printers(self) -> List[Printer]:
        """获取所有可用打印机"""
        try:
            conn = self._ensure_connection()
            printers = conn.getPrinters()
            printer_list = []
            
            for name, attrs in printers.items():
                printer = Printer(
                    name=name,
                    uri=attrs.get('device-uri', ''),
                    device_id=attrs.get('device-id', ''),
                    state=attrs.get('printer-state', 'unknown'),
                    is_shared=attrs.get('printer-is-shared', False),
                    info=attrs.get('printer-info', '')
                )
                printer_list.append(printer)
            
            logger.info(f"找到 {len(printer_list)} 个打印机")
            return printer_list
        
        except Exception as e:
            logger.error(f"获取打印机列表失败: {e}")
            return []
    
    def get_printer(self, printer_name: str) -> Optional[Printer]:
        """获取指定打印机信息"""
        try:
            conn = self._ensure_connection()
            attrs = conn.getPrinterAttributes(printer_name)
            return Printer(
                name=printer_name,
                uri=attrs.get('device-uri', ''),
                state=attrs.get('printer-state', 'unknown'),
                is_shared=attrs.get('printer-is-shared', False),
                info=attrs.get('printer-info', '')
            )
        
        except Exception as e:
            logger.error(f"获取打印机 {printer_name} 信息失败: {e}")
            return None
    
    def get_printer_status(self, printer_name: str) -> str:
        """获取打印机状态"""
        try:
            conn = self._ensure_connection()
            state_map = {
                3: "idle",
                4: "processing",
                5: "stopped"
            }
            
            attrs = conn.getPrinterAttributes(printer_name)
            state = attrs.get('printer-state', 0)
            return state_map.get(state, "unknown")
        
        except Exception as e:
            logger.error(f"获取打印机状态失败: {e}")
            return "error"
    
    def print_file(
        self,
        printer_name: str,
        file_path: str,
        job_name: str = "Print Job",
        copies: int = 1,
        page_range: Optional[str] = None
    ) -> int:
        """
        打印文件
        
        Args:
            printer_name: 打印机名称
            file_path: 文件路径
            job_name: 作业名称
            copies: 打印份数
            page_range: 页码范围，例如 "1-5,8,11-13"
        
        Returns:
            作业ID
        """
        try:
            conn = self._ensure_connection()
            
            options = {}
            if copies > 1:
                options['copies'] = str(copies)
            if page_range:
                options['page-range'] = page_range
            
            # 添加作业
            job_id = conn.printFile(
                printer_name,
                file_path,
                job_name,
                options
            )
            
            logger.info(f"打印作业已提交: 作业ID={job_id}, 打印机={printer_name}, 文件={os.path.basename(file_path)}")
            return job_id
        
        except Exception as e:
            logger.error(f"打印文件失败: {e}")
            raise Exception(f"打印失败: {e}")
    
    def get_jobs(self, printer_name: str = None) -> List[dict]:
        """获取打印作业列表"""
        try:
            conn = self._ensure_connection()
            jobs = conn.getJobs(printer_name)
            job_list = []
            
            for job_id, attrs in jobs.items():
                job_info = {
                    'job_id': job_id,
                    'name': attrs.get('job-name', 'Unknown'),
                    'printer': attrs.get('printer-uri', '').split('/')[-1] if attrs.get('printer-uri') else '',
                    'state': attrs.get('job-state', 0),
                    'user': attrs.get('job-originating-user-name', 'Unknown'),
                    'size': attrs.get('job-k-octets', 0) * 1024
                }
                job_list.append(job_info)
            
            return job_list
        
        except Exception as e:
            logger.error(f"获取作业列表失败: {e}")
            return []
    
    def cancel_job(self, job_id: int) -> bool:
        """取消打印作业"""
        try:
            conn = self._ensure_connection()
            conn.cancelJob(job_id, purge_job=False)
            logger.info(f"已取消作业: {job_id}")
            return True
        
        except Exception as e:
            logger.error(f"取消作业失败: {e}")
            return False
    
    def get_job_status(self, job_id: int) -> dict:
        """获取作业状态"""
        try:
            conn = self._ensure_connection()
            jobs = conn.getJobs()
            if job_id in jobs:
                attrs = jobs[job_id]
                return {
                    'job_id': job_id,
                    'name': attrs.get('job-name', 'Unknown'),
                    'state': attrs.get('job-state', 0),
                    'user': attrs.get('job-originating-user-name', 'Unknown')
                }
            return None
        
        except Exception as e:
            logger.error(f"获取作业状态失败: {e}")
            return None
    
    def add_printer(
        self,
        name: str,
        uri: str,
        info: str = "",
        is_shared: bool = False
    ) -> bool:
        """添加打印机"""
        try:
            conn = self._ensure_connection()
            conn.addPrinter(
                name,
                device=uri,
                info=info,
                sharing=is_shared
            )
            logger.info(f"已添加打印机: {name}")
            return True
        
        except Exception as e:
            logger.error(f"添加打印机失败: {e}")
            return False
