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

# Access contaol                            # 权限控制
ALLOW_REGISTER = True                       # 允许外部注册
ALLOW_ANONYMOUS_GROUP_INFO = True           # 允许匿名访问小组信息，以方便注册

USER_INITIAL_ACCESS = frozenset([
    'auth', 'read_self', 'read_internal', 'read_other', 'write_self', 'read_group'
])

APP_INITIAL_ACCESS = frozenset([
    'auth', 'read_self'
])


# Web console
SSO_WEB_REDIRECT_PREFIX = 'http://sso.local.com/'  # 内部 SSO 管理面板登录的Redirect前缀

#
#   LAN Device discover service.
#   CheckBot service.
#
LAN_DEV_REDIS_HOST = ''                                   # Redis
LAN_DEV_REDIS_PORT = ''
LAN_DEV_REDIS_PROBER_IDENT_PREFIX = 'LANDEV_DEFAULT'      # Redis key前缀，用于区分应用
LAN_DEV_LIVENESS_TRACK_INTERVAL = 5                       # 进行设备存活测试的时间间隔
LAN_DEV_LIVENESS_PROBE_TIMEOUT = 5                        # 进行设备发现超时时间
                                                          # 若设备在此时间内无响应，则判断
                                                          # 设备不存在
LAN_DEV_LIVENESS_PROBE_INTERVAL = 30                      # 进行设备发现的时间间隔
LAN_DEV_INTERFACE = 'wlp3s0'                              # 进行设备感知的接口名称
