import os
# 并行工作进程数
workers = os.getenv('WORKERS', os.cpu_count())
# 指定每个工作者的线程数
threads = os.getenv('THREADS', os.cpu_count())
# 监听内网端口5000
bind = '0.0.0.0:{}'.format(os.getenv('PORT', 6060))
# 设置守护进程,将进程交给supervisor管理
#daemon = 'True'
# 工作模式协程
worker_class = 'uvicorn.workers.UvicornWorker'
# 设置最大并发量
worker_connections = 2000
# 设置进程文件目录
pidfile = 'gunicorn.pid'
# 设置访问日志和错误信息日志路径
# accesslog = './log/gunicorn_acess.log'
# errorlog = './log/gunicorn_error.log'
log_level='Error'
# 设置日志记录水平
