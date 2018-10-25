# Starstudio SSO 接口文档 (Draft)

### 目录

- [API结果返回格式](#API结果返回格式)
  - [状态码含义](#参考下列code状态码意义)
- [认证接口](#认证)
  - [登录](#登录)
  - [退出](#退出)
  - [API 认证](#API认证)
  - [JWT 格式](#JWT格式)
  - [Token 合法性校验](#Token合法性校验)
- [设备绑定接口](#设备绑定)
  - [查看目前的设备信息（Draft）](#查看目前的设备信息（Draft）)
  - [查看当前用户已绑定的设备信息](#查看当前用户已绑定的设备信息)
  - [绑定当前设备](#绑定当前设备)
  - [当前在线设备的列表](#当前在线设备的列表)
  - [取消设备绑定](#取消设备绑定)
- 信息接口
  - 组
    - [获取小组信息](#获取小组信息)
    - [添加小组](#添加小组)
    - [删除小组](#删除小组)
  - 成员
    - [获取成员信息](#获取成员信息)
    - [批量获取成员信息](#批量获取成员信息)
    - [添加成员](#添加成员)
    - [删除成员](#删除成员)
- 应用管理接口
  - 条件查询应用
  - 查询应用
  - 删除应用
  - 修改应用权限

- [安全性](#安全性)
  - 传输安全性
  - 对 Token 的校验
  - 严防 XSS
  - 禁止使用 API 颁发 Token

---

#### API 返回格式

```json
{"code":0 , "data":"succsss", "msg": ""}
```

**data** 为返回的数据，具体内容依据调用的API所不同。**msg** 为对 **code** 的描述。**code** 为状态码。

##### 参考下列code状态码意义

| code |               msg                |                   含义 |
| :--- | :------------------------------: | ---------------------: |
| 0    |             success              |               请求成功 |
| 1201 |      Authorization failure.      |               认证失败 |
| 1202 | Unsupported Authorization method |       不支持的认证方式 |
| 1203 |          Access denied.          | 因用户权限原因拒绝访问 |
| 1301 |         Group not empty          |               小组非空 |
| 1400 |           Bad request            |             请求不正确 |
| 1422 |          Arg %s missing          |            缺少参数 %s |
| 1423 |            视情况而定            |             参数不正确 |
| 1504 |        Unknown Exception         |           出现未知异常 |

---

### 认证

#### 登录

支持一般的登录认证和单点登录。遵守 JSON Web Token 规范。登录的所有过程都需要在HTTPS下完成。

- 只做认证使用

  - 请求路径：http://\(服务器名)/sso/login

  - 请求方法：POST

  - 认证方式：

    使用表单

| 参数     | 类型   | 描述   |
| -------- | ------ | ------ |
| username | string | 用户名 |
| password | string | 密码   |

  - 返回：

    若成功登录，则会返回

    ```json
    {"code":0 , "msg":"succsss", "data": ""}
    ```

    此时返回 HTTP 状态码 200

    若登录失败，会返回错误信息，此时 code 字段非 0。HTTP 状态码 非200。

- 获取应用 Token

  登录时附带appid可获取应用Token。可以作为其他系统的 Token 使用。

  - 请求路径：http://\<服务器名\>/sso/login?appid=<应用ID>

  - 请求方法：GET 或 PUSH

  - 认证方式：表单认证，[见上](#登录)

  - 返回：

    若认证成功，则在data字段返回一个JWT。

    ```json
    {"code":0 , "msg":"succsss", "data": {
        "token": "<JWT Token>"
    }}
    ```

    一个成功登录的返回示例

    ```json
    {
      "code": 0, 
      "data": {
        "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1MzkxMDE5NjQsImlhdCI6MTUzOTAxNTU2NCwianRpIjoiZjgzMjdhNDdjZmY4NDBlODgyNDRiM2ZkNTQ3NjNhYjQiLCJ1c2FnZSI6ImFwcGxpY2F0aW9uIiwidXNlcl9pZCI6MSwidXNlcm5hbWUiOiJBZG1pbiIsInZlcmJzIjpbInJlYWRfaW50ZXJuYWwiLCJyZWFkX2dyb3VwIiwicmVhZF9vdGhlciIsIndyaXRlX2ludGVybmFsIiwid3JpdGVfc2VsZiIsIndyaXRlX2dyb3VwIiwiYWx0ZXJfZ3JvdXAiLCJhdXRoIiwicmVhZF9zZWxmIiwid3JpdGVfb3RoZXIiXX0.kCvschqm1AWwUMjIdrQgzW5Ao15AEt9d4v8Mfkuges1aOkZebQzPSKZpXOjsk7ltEDxVxrO28yBZC-VZyj8-SV8C3TpLYvcFh8ml2n1UjQFHXACwOayCVblVGW9PYe-7b3BY7ECbF57JRhpelwiopV6crFHxdKuJY3fbhn6AqmM"
      }, 
      "msg": "succeed"
    }
    ```

    失败时返回与只作认证使用时相同。

- 单点登录

  前几种情况中都涉及了认证，在成功认证后，服务器会利用 Set-Cookie 在用户端保存一个特殊的 Token，用于登录状态校验。

  - 利用 redirectURL 从 SSO 系统获取 Token

    一个未有登录状态的系统可以通过以下步骤获取Token。

    - 发现未登录，将用户重定向至 

      ```
      http://<服务器名>/sso/login?appid=<应用ID>&redirectURL=<认证完成后的重定向链接>
      ```

    - SSO 服务对登录状态进行校验，并根据结果进行跳转

      SSO 服务会对 redirectURL 的链接进行检查，若与注册的 URL 不符合，则会拒绝进行 Token 颁发和任何的跳转，显示一个错误信息。

      - 已登录

        SSO 会将颁发的 Token 作为参数，将用户重定向到 redirectURL 所指定的链接。

        例如 redirectURL 指定了 http://sign.stuhome.com/redirectsso，则跳转到：

        ```
        http://sign.stuhome.com/redirectsso?token=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1MzkxMDE5NjQsImlhdCI6MTUzOTAxNTU2NCwianRpIjoiZjgzMjdhNDdjZmY4NDBlODgyNDRiM2ZkNTQ3NjNhYjQiLCJ1c2FnZSI6ImFwcGxpY2F0aW9uIiwidXNlcl9pZCI6MSwidXNlcm5hbWUiOiJBZG1pbiIsInZlcmJzIjpbInJlYWRfaW50ZXJuYWwiLCJyZWFkX2dyb3VwIiwicmVhZF9vdGhlciIsIndyaXRlX2ludGVybmFsIiwid3JpdGVfc2VsZiIsIndyaXRlX2dyb3VwIiwiYWx0ZXJfZ3JvdXAiLCJhdXRoIiwicmVhZF9zZWxmIiwid3JpdGVfb3RoZXIiXX0.kCvschqm1AWwUMjIdrQgzW5Ao15AEt9d4v8Mfkuges1aOkZebQzPSKZpXOjsk7ltEDxVxrO28yBZC-VZyj8-SV8C3TpLYvcFh8ml2n1UjQFHXACwOayCVblVGW9PYe-7b3BY7ECbF57JRhpelwiopV6crFHxdKuJY3fbhn6AqmM
        ```

      - 未登录

        SSO 会将用户重定向到 redirectURL 所指定的链接，不附带任何参数。

    - 系统收到跳转，根据设定的策略提示用户进行下一步操作。

#### 退出

- 请求路径：http://\(服务器名)/sso/logout?redirectURL=<重定向URL>

- 请求方法：GET

- 注意：退出仅仅是单点登录系统退出，其他系统的

- 返回：

  若附带了重定向URL。则会发生重定向。

  否则。

  若成功退出，则会返回

  ```json
  Logouted.
  ```

  未登录时，返回

  ```
  You are not logined.
  ```

#### JWT格式

- Header 格式

```json
{
  "alg": "RS256",
  "typ": "JWT"
}
```

- Payload 格式

- 

#### Token合法性校验

---

### API认证

访问大多数API接口需要附带Bearer Token，Token 的类型为 Application，可以通过API [获取](#登录) Application Token。

---

### 设备绑定

#### 查看目前的设备信息（Draft）

- 请求路径：http://(服务器名)/v1/star/device/myself

- 请求方法：GET

- 是否需要附带 Token：否

- 返回：

  - 格式

    ```json
    {"code": 200, "data":"<MAC地址>", "msg":"success"}
    ```

  - 返回示例：

    ```json
    {"code": 200, "data":"88:d5:0c:8f:59:bb", "msg":"success"}
    {"code": 200, "data":null, "msg":"success"} // 没有发现你的设备
    ```

- 额外说明：

  - 如果没有发现设备，data 字段返回为 null. 表示设备尚未被发现。原因可能是这个设备并不在统一个网络，或者需要等候设备被发现。



#### 查看当前用户已绑定的设备信息

- 请求路径：http://(服务器名)/v1/star/device/mine

- 请求方法：GET

- 是否需要附带 Token：是

- 返回：

  - 格式

    ```json
    {"code": 200, "data":[
            {
                "uid": <用户1 uid>
                , "mac": [
                    "XX:XX:XX:XX:XX:XX"
                    , "XX:XX:XX:XX:XX:XX"
                    , ...
                ]
            }
        	, {
                "uid": <用户2 uid>
                , "mac": [
                    "XX:XX:XX:XX:XX:XX"
                    , "XX:XX:XX:XX:XX:XX"
                    , ...
                ]
            }
        	, ...
        ], "msg":"success"}
    ```

  - 返回示例：

    ```json
    {"code": 200, "data":[
            {
                "uid": 1
                , "mac": [
                    "18:19:C0:19:57:1B"
                    , "18:19:C0:C9:DE:1B"
                ]
            }
        ], "msg":"success"}
    ```



#### 绑定当前设备

- 请求路径：http://(服务器名)/v1/star/device/mine

- 请求方法：POST

- 是否需要附带 Token：是

- 返回：

  - 格式

    ```json
    {"code": <状态码>, "data":"", "msg":"success"}
    ```

  - 返回示例：

    ```json
    {"code": 200, "data":"" , "msg":"success"} // 成功
    {"code": 1422, "data":"Device not found." , "msg":"success"} // 未找到设备
    {"code": 1422, "data":"Bind another device is not allowed." , "msg":"success"} // 不允许绑定非请求设备
    {"code": 1422, "data":"Device bound." , "msg":"success"} // 设备已经被绑定
    ```



#### 当前在线设备的列表

- 请求路径：http://(服务器名)/v1/star/device/list

- 请求方法：GET

- 是否需要附带 Token：是

- 返回：

  - 格式

    ```json
    {"code": <状态码>, "data": 
         {
             "MAC1" : {
                 'IPs' : [
                       'x.x.x.x'
                       , ...
                  ]
             , "MAC2" : {
                 ...
             }
             , ...
        }
    }, "msg":"success"}
    ```

  - 返回示例：

    ```json
    {"code": 200, "data":{
        {
            "94:65:2d:85:a5:91": [
                "192.168.1.1"
                , "192.168.1.189"
            ]
            , "94:65:2d:85:a5:92": [
                "192.168.1.2"
                , "192.168.1.39"
            ]
        }
    }, "msg":"success"} // 成功
    ```



#### 取消设备绑定

- 请求路径：http://(服务器名)/v1/star/mine/<设备MAC>

- 请求方法：DELETE

- 是否需要附带 Token：是

- 路径中 设备MAC 格式

  去掉MAC中间的冒号。

  例：AA:BB:CC:DD:EE:FF 的请求路径为 http://\<服务器名\>/v1/star/mine/AABBCCDDEEFF

- 返回：

  - 格式

    ```json
    {"code": <状态码>, "data": "", "msg":"..."}
    ```

  - 返回示例：

    ```json
    {"code": 200, "data": "", "msg":"success"}
    {"code": 1422, "data": "Not bound or cannot unbind", "msg":"success"}
    ```

---

### 信息接口

#### 获取小组信息

- 请求路径：http://(服务器名)/v1/star/group

- 请求方法：GET

- 是否需要附带 Token：一般为否，除非开启了此接口的认证

- 返回：

  - 格式

    ```json
    {"code": <状态码>, "data": [{
             ”name“: “<小组>”
             , "gid": <小组ID>
             , "desp": "<小组介绍>"
        }
        , ...
    ], "msg":"success"}
    ```

  - 返回示例：

    ```json
    {"code": 200, "data": [{
        "name": "Devops"
        , "gid": 2
        , "desp": "Site Reliability Engineering Group."
    ], "msg":"success"}
    
    {"code": 1422, "data": "Too many args", "msg":"success"} // 参数太多
    ...
    ```



#### 添加小组

- 请求路径：http://(服务器名)/v1/star/group

- 请求方法：POST

- 是否需要附带 Token：是

- 表单参数

| 名称 | 类型   | 是否必须 | 描述     |
| ---- | ------ | -------- | -------- |
| name | string | 是       | 小组名称 |
| desp | string | 是       | 小组描述 |

- 返回：

  - 格式

    ```json
    {"code": <状态码>, "data": {
         "gid": <新小组 GID>
    }, "msg":"success"}
    ```

  - 返回示例：

    ```json
    {"code": <状态码>, "data": {
         "gid": 4
    }, "msg":"success"}
    
    {"code": 1422, "data": "Too many args", "msg":"success"} // 参数太多
    {"code": 1422, "data": "Arg name missing.", "msg":"success"} // 缺少参数 name
    ...
    ```



#### 删除小组

- 请求路径：http://(服务器名)/v1/star/group

- 请求方法：DELETE

- 是否需要附带 Token：是

- 表单参数

| 名称 | 类型    | 是否必须 | 描述     |
| ---- | ------- | -------- | -------- |
| gid  | integer | 是       | 小组 GID |

- 返回：

  - 格式

    ```json
    {"code": <状态码>, "data": "", "msg":"..."}
    ```

  - 返回示例：

    ```json
    {"code": 200, "data":"" , "msg":"success"}
    
    {"code": 1422, "data": "", "msg":"Too many args"} // 参数太多
    {"code": 1422, "data": "", "msg":"Arg name missing."} // 缺少参数 gid
    {"code": 1422, "data": "", "msg":"GID 4 invalid. Group not exists."} // 小组不存在
    {"code": 1505, "data": "", "msg":"Server raises a exception with id  XXXXXXX"} // 服务器提了一个 Issue
    ...
    ```



#### 获取成员信息

- 请求路径：http://(服务器名)/v1/star/member/(uid)

- 请求方法：GET

- 是否需要附带 Token：是

- 返回：

  - 格式

    ```json
    {"code": <状态码>, "data": {
          'name': "<名称>"
          , 'birthday' : "<出生时间>"
          , 'sex': "<性别>"
          , 'address': "<联系地址>"
          , 'tel': "<联系电话>"
          , 'mail': "<邮箱>"
          , 'access_verbs': "<拥有的权限>"
          , 'id': <用户ID>
          , 'gid': <组ID>
    }, "msg":"..."}
    ```

  - 返回示例：

    ```json
    {"code": <状态码>, "data": {
          'name': "渣渣辉"
          , 'birthday' : "2018-10-16 21:24:54"
          , 'sex': "男"
          , 'address': "活在梦里"
          , 'tel': "XXXXXXXXXXX"
          , 'mail': "ZZH@starstudio.org"
          , 'access_verbs': "auth read_self read_internal read_other write_self read_group"
          , 'id': 8
          , 'gid': 2
    }, "msg":"succees"}
    
    {"code": 1422, "data": "", "msg":"Too many args"} // 参数太多
    {"code": 1422, "data": "", "msg":"User not exists."} // 成员不存在
    {"code": 1505, "data": "", "msg":"Server raises a exception with id  XXXXXXX"} // 服务器提了一个 Issue
    ...
    ```

#### 批量获取成员信息

- 请求路径：http://(服务器名)/v1/star/member

- 请求方法：GET

- 是否需要附带 Token：是

- 表单参数：

| 名称 | 类型    | 是否必须 | 描述    |
| ---- | ------- | -------- | ------- |
| uid  | integer | 否       | 成员UID |
| gid  | integer | 否       | 小组GID |

- 返回：

  - 格式

    ```json
    {"code": <状态码>, "data": [{
          'name': "<名称>"
          , 'birthday' : "<出生时间>"
          , 'sex': "<性别>"
          , 'address': "<联系地址>"
          , 'tel': "<联系电话>"
          , 'mail': "<邮箱>"
          , 'access_verbs': "<拥有的权限>"
          , 'id': <用户ID>
          , 'gid': <组ID>
        }
        , ...
    ], "msg":"..."}
    ```

  - 返回示例：

    ```json
    {"code": <状态码>, "data": [{
          'name': "渣渣辉"
          , 'birthday' : "2018-10-16 21:24:54"
          , 'sex': "男"
          , 'address': "活在梦里"
          , 'tel': "XXXXXXXXXXX"
          , 'mail': "ZZH@starstudio.org"
          , 'access_verbs': "auth read_self read_internal read_other write_self read_group"
          , 'id': 8
          , 'gid': 2
         }, {
          'name': "彭于晏"
          , 'birthday' : "2018-10-16 21:24:54"
          , 'sex': "女"
          , 'address': "活在现实"
          , 'tel': "XXXXXXXXXXX"
          , 'mail': "300Kilograms@starstudio.org"
          , 'access_verbs': "auth read_self read_internal read_other write_self read_group"
          , 'id': 9
          , 'gid': 2
         } 
    ], "msg":"succees"}
    
    {"code": 1422, "data": "", "msg":"Too many args"} // 参数太多
    {"code": 1505, "data": "", "msg":"Server raises a exception with id XXXXXXX"} // 服务器提了一个 Issue
    ...
    ```


#### 添加成员

- 请求路径：http://(服务器名)/v1/star/member

- 请求方法：POST

- 是否需要附带 Token：是

- 表单参数

| 名称     | 类型    | 是否必须 | 描述                                                         |
| -------- | ------- | -------- | ------------------------------------------------------------ |
| username | string  | 是       | 登录名                                                       |
| password | string  | 是       | 登录密码                                                     |
| birthday | string  | 是       | 出生日期，UTC 时间，格式为 年-月-日 时:分:秒。如 2018-10-16 21:24:54 |
| name     | string  | 是       | 名称                                                         |
| gid      | integer | 是       | 小组 GID                                                     |
| sex      | string  | 是       | 性别                                                         |
| tel      | string  | 是       | 联系电话                                                     |
| mail     | string  | 是       | 电子邮件                                                     |
| address  | string  | 是       | 联系地址                                                     |

- 返回：

  - 格式

    ```json
    {"code": 200, "data": {
        "uid": <新用户UID>
    }, "msg":"..."}
    {"code": <状态码>, "data": "", "msg":"..."}
    ```

  - 返回示例：

    ```json
    {"code": 200, "data":{
        "uid": 8
    } , "msg":"success"}
    
    {"code": 1422, "data": "", "msg":"Password too short"} // 密码太短
    {"code": 1422, "data": "", "msg":"Username already exists."} // 用户名已存在
    {"code": 1422, "data": "", "msg":"Arg name missing."} // 缺少参数 name
    {"code": 1422, "data": "", "msg":"Incorrect time format."} // 时间格式不正确
    {"code": 1422, "data": "", "msg":"Group 4 not exists."} // 小组不存在
    {"code": 1505, "data": "", "msg":"Server raises a exception with id XXXXXXX"} // 服务器提了一个 Issue
    ...
    ```



#### 删除成员

- 请求路径：

  - http://(服务器名)/v1/star/member

    - 表单参数

| 名称 | 类型    | 是否必须 | 描述     |
| ---- | ------- | -------- | -------- |
| uid  | integer | 是       | 成员 UID |

  - http://<服务器名>/v1/star/member/(uid)

- 请求方法：DELETE

- 是否需要附带 Token：是

- 返回：

  - 格式

    ```json
    {"code": <状态码>, "data": "", "msg":"..."}
    ```

  - 返回示例：

    ```json
    {"code": 200, "data":"" , "msg":"success"}
    
    {"code": 1422, "data": "", "msg":"Too many args"} // 参数太多
    {"code": 1422, "data": "", "msg":"Arg uid missing."} // 缺少参数 uid
    {"code": 1505, "data": "", "msg":"Server raises a exception with id  XXXXXXX"} // 服务器提了一个 Issue
    ...
    ```


