# Starstudio SSO 接口文档 (Draft)

### 目录

- [API结果返回格式](#API结果返回格式)
  - [状态码含义](#参考下列code状态码意义)
- [认证](认证)
  - [登录](#登录)
  - [退出](#退出)
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

登录

支持一般的登录认证和单点登录。遵守 JSON Web Token 规范。登录的所有过程都需要在HTTPS下完成。

- 只做认证使用

  - 请求路径：http://\<服务器名\>/sso/login

  - 请求方法：GET

  - 认证方式：

    使用 HTTP Basic Authentication，即附带 Basic Authorization 头部。

  - 返回：

    若成功登录，则会返回

    ```json
    {"code":0 , "msg":"succsss", "data": ""}
    ```

    此时返回 HTTP 状态码 200

    若登录失败，会返回错误信息，此时 code 字段非 0。HTTP 状态码 非200。

- 获取应用 Token

  读取用户信息需要 HTTP Bearer Authentication。获取的Token可以作为其他系统的 Token 使用。

  - 请求路径：http://\<服务器名\>/sso/login?appid=<应用ID>

  - 请求方法、认证方式与只作认证使用时相同

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

    一个未有登录状态的系统可以通过以下步骤获取已登录的用户状态。

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

##### 退出

- 请求路径：http://\<服务器名\>/sso/logout

- 请求方法：GET

- 返回：

  若成功退出，则会返回

  ```json
  Logouted.
  ```

  未登录时，返回

  ```
  You are not logined.
  ```

---

