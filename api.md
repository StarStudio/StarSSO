API说明文档

> resp

```
{"code":0 , "data":"succsss", "msg": ""}
```

参考下列code状态码意义

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
| 1503 |         database failed          |         数据库操作失败 |
| 1504 |        Unknown Exception         |           出现未知异常 |
| 1507 |                                  |  识别人脸结果为Unknown |





### 权限

请求接口时需要附带 StarStudio-Application 头部，内容为一个 ApplicationKey。ApplicationKey 具体内容请咨询工作室相关人员。



### 人脸识别签到

- URL：http://sign.stuhome.com/v1/star/record
- 请求方法：POST
- 参数：

| 参数   | 类型   | 说明   |
| ---- | ---- | ---- |
| face | file | 人脸文件 |

- 返回：

  ```json
  {"code":0 
    , "data":{
      "check_in" : [ // 变为 Checked in 状态的人员信息
        	{
             "name": "<成员名>"
             , "uid" :"<成员 UID>"
             , "gid" : "<所属组 GID>"
             , "age" : "<年龄>"
             , "sex" : "<性别>"
             , "address" : "<联系地址>"
             , "tel" : "<联系电话>"
             , "mail" : "<电子邮箱>"
         } 
        , ...
      ]
        , "check_out" : [ // 变为 Checked out 状态的人员信息
        {
             "name": "<成员名>"
             , "uid" :"<成员 UID>"
             , "gid" : "<所属组 GID>"
             , "age" : "<年龄>"
             , "sex" : "<性别>"
             , "address" : "<联系地址>"
             , "tel" : "<联系电话>"
             , "mail" : "<电子邮箱>"
         }
        , ...
      ]
    }
    , "msg": "success"
  }// 成功
  {"code":<status_code>, "data":'', "msg": "<error descrption>"} // 失败
  ```

  ​



### 增加组

- URL：http://sign.stuhome.com/v1/star/group

- 请求方法：POST

- 参数：

| 参数   | 类型     | 说明   |
| ---- | ------ | ---- |
| name | string | 小组名称 |
| desp | string | 小组说明 |

- 返回：

  ```json
  {"code":0 , "data":{"gid": "<新小组 GID>"}, "msg": "success"}// 成功
  {"code":<status_code>, "data":'', "msg": "<error descrption>"} // 失败
  ```


#### 

#### 查询所有小组

- API：http://sign.stuhome.com/v1/star/group

- 请求方法：GET

- 请求参数：无

- 返回：

  ```json
  {
      "code":0 
     , "data" :[
         {
             "name": "<小组名称>"
             , "gid" :"<小组 GID>"
             , "desp" : "<小组描述>"
           , "members" [
           	{
           
         		}, ...
           ]
         }
         , ...
       ]
     , "msg": "success"} // 成功

  {"code":<status_code>, "data":'', "msg": "<error descrption>"} // 失败
  ```

  ​

#### 增加成员

- URL：http://sign.stuhome.com/v1/star/member

- 请求方法：POST

- 表单参数：

| 参数       | 类型     | 说明     |
| :------- | :----- | :----- |
| name     | string | 成员姓名   |
| gid      | string | 组 ID   |
| sex      | string | 性别     |
| tel      | string | 电话号码   |
| mail     | string | 邮箱     |
| face_img | file   | 人脸图片数据 |

- 返回：

  ```json
  {"code":0 , "data":{"uid": "<新成员 GID>"}, "msg": "success"} // 成功
  {"code":<status_code>, "data":'', "msg": "<error descrption>"} // 失败
  ```



### 删除成员

- API ：http://sign.stuhome.com/v1/star/member

- 请求方法：DELETE

- 表单参数：

| 参数   | 类型     | 说明     |
| ---- | ------ | ------ |
| name | string | 成员姓名   |
| uid  | string | 成员 UID |

  name 和 uid 指定其一。指定了 uid，name 会被忽略。

- 返回：

  ```json
  {"code":0 , "data":'', "msg": "success"} // 成功
  {"code":<status_code>, "data":'', "msg": "<error descrption>"} // 失败
  ```





### 查询签到记录

- API：http://sign.stuhome.com/v1/star/record

- 请求方法：GET

- 请求参数：

  参数用于过滤特定结果。

| 参数         | 类型     | 说明   |
| ---------- | ------ | ---- |
| name       | string | 成员名称 |
| group      | string | 小组名称 |
| time_start | int    |      |
| time_end   | int    |      |



- 返回：

  ```json
  {
      "code":0 
     , "data" :[
         {
             "name": "<成员名>"
             , "uid" :"<成员 UID>"
             , "choose" : "..."
             , "chktime" : "<签到时间>"
             , "device" : "..."
             , "img_path" : "..."
             , "res" : "..."
         }
         , ...
       ]
     , "msg": "success"} // 成功

  {"code":<status_code>, "data":'', "msg": "<error descrption>"} // 失败
  ```




####签到情况统计

- API：http://sign.stuhome.com/v1/star/counting

- 请求方法：GET

- 请求参数：

  参数用于过滤特定结果。

| 参数名        | 类型   | 说明                                   |
| ---------- | ---- | ------------------------------------ |
| start_time | int  | 开始时间戳  （从 1970-1-1 8:00:00 开始所经过的秒数） |
| end_time   | int  | 结束时间戳 （从 1970-1-1 8:00:00 开始所经过的秒数）  |

- 返回：

  ```json
  {
      "code":0 
     , "data" :[
         {
             "name": "<成员名>"
             , "uid" :"<成员 UID>"
             , "count" : "<完整签到次数>"
         }
         , ...
  	]
     , "msg": "success"} // 成功

  {"code":<status_code>, "data":'', "msg": "<error descrption>"} // 失败
  ```

  ​

  ​

  ​

### 全部人员概览

- API： http://sign.stuhome.com/v1/star/member

- 请求方法：GET

- 参数：无

- 返回：

  ```json
  {
      "code":0 
     , "data" :[
         {
             "name": "<成员名>"
             , "uid" :"<成员 UID>"
             , "gid" : "<所属组 GID>"
             , "age" : "<年龄>"
             , "sex" : "<性别>"
             , "address" : "<联系地址>"
             , "tel" : "<联系电话>"
             , "mail" : "<电子邮箱>"
         }
         , ...
       ]
     , "msg": "success"} // 成功

  {"code":<status_code>, "data":'', "msg": "<error descrption>"} // 失败
  ```

  ​

