#
#   Configure SSO API Server
#

# Logging
ACCESS_LOG = 'access.log'                   # 日志文件
ERROR_LOG = 'error.log'
DEBUG_LOG = 'debug.log'

DEBUG = False                               # 调试模式


# Secret
SECRET_KEY_FILE = 'jwt.pri'                 # JWT 私钥
SECRET_KEY_FILE_MODE = 0o600                # 私钥文件权限
PUBLIC_KEY_FILE = 'jwt.pub'                 # JWT 公钥
PUBLIC_KEY_MODE = 0o666                     # 公钥文件权限

SALT_FILE = 'starstudio.salt'               # 密码散列盐
SALT_FILE_MODE = 0o600                      # 文件权限

AUTH_TOKEN_EXPIRE_DEFAULT = 86400           # Auth 类型 Token 的有效时间 (秒)
APP_TOKEN_EXPIRE_DEFAULT = 86400            # Application 类型 Token 的有效时间 (秒)

# Database
MYSQL_DATABASE_HOST = 'localhost'           # 数据库配置
MYSQL_DATABASE_PORT = 3306
MYSQL_DATABASE_USER = 'root'
MYSQL_DATABASE_PASSWORD = None
MYSQL_DATABASE_DB = 'starstudio'
MYSQL_DATABASE_CHARSET = 'utf8'

# Web console
SSO_WEB_REDIRECT_PREFIX = 'http://127.0.0.1:5000/'  # 内部 SSO 管理面板登录的Redirect前缀

#
#   LAN Device discover service.
#
LAN_DEV_REDIS_HOST = ''
LAN_DEV_REDIS_PORT = ''
LAN_DEV_REDIS_PROBER_IDENT_PREFIX = 'LANDEV_DEFAULT'

LAN_DEV_LIVENESS_TRACK_INTERVAL = 5
LAN_DEV_LIVENESS_PROBE_TIMEOUT = 5
LAN_DEV_LIVENESS_PROBE_INTERVAL = 20
LAN_DEV_INTERFACE = 'wlp3s0'
