# StarStudioSSO

工作室内部的单点登陆（SSO）服务，供工作室内部系统（包括但不限于签到系统、PaaS容器平台）做身份认证使用。预计使用JWT(Json Web Token)规范。



---

### 子项目

- **[StarMember](#StarMember)**
- **[LANDevice](#LANDevice)**



#### 依赖

推荐使用 virtualenv 进行部署，在虚拟环境中安装依赖。

```bash
pip install -r requirements.txt
```



### StarMember

身份管理、认证服务器，提供Restful API。



### LANDevice

设备感知服务，主动感知局域网内在线设备，提供子网内设备信息列表（MAC、IP、设备名等信息），并产生设备活动事件（加入、移除、设备名更新、DHCP重分配等事件），供其他服务使用。所有信息经过 Redis 实现订阅/发布。

#### 配置

在环境变量 LAN_DEV_PROBER_CONFIG 指定配置文件位置。

```bash
export LAN_DEV_PROBER_CONFIG=<配置文件绝对路径>
```

配置文件示例

```python
LAN_DEV_REDIS_HOST = ''                                   # Redis
LAN_DEV_REDIS_PORT = ''
LAN_DEV_REDIS_PROBER_IDENT_PREFIX = 'LANDEV_DEFAULT'      # Redis key前缀，用于区分应用
LAN_DEV_LIVENESS_TRACK_INTERVAL = 5                       # 进行设备存活测试的时间间隔
LAN_DEV_LIVENESS_PROBE_TIMEOUT = 5                        # 进行设备发现超时时间
                                                          # 若设备在此时间内无响应，则判断
                                                          # 设备不存在
LAN_DEV_LIVENESS_PROBE_INTERVAL = 30                      # 进行设备发现的时间间隔
LAN_DEV_INTERFACE = 'wlp3s0'                              # 进行设备感知的接口名称
```

#### 启动服务

```bash
python -m LANDevice
```

会阻塞，生产环境建议使用supervisor。