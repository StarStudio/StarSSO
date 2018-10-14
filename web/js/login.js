vue_bind = function() {
    nav_bar = new Vue({
        el: '#containerbox'
        , data: {
            'bar_items': {
                'login': {
                    'name': '登录'
                    , 'class' : 'nav_item item_selected'
                }
                , 'register' : {
                    'name' : '注册'
                    , 'class' : 'nav_item item_normal'
                }
            }
            , 'current_selected' : 'login'
            , 'control' : {
                'show_login_err' : false
                , 'login_err_box_style' : 'error'
                , 'reg_err_box_style' : 'error'
                , 'login_err_msg': ''
                , 'show_reg_err' : false
                , 'reg_err_msg': ''
            }
            , 'login' : {
               'username': ''
                , 'password' : ''
                , 'show_login_err': false
                , 'login_err_msg' : ''
            }
            , 'group_set' : []
            , 'register' : {
                'username': ''
                , 'password': ''
                , 'password_confrim': ''
                , 'sex' : '性别'
                , 'address' : ''
                , 'birthday' : ''
                , 'mail' : ''
                , 'tel' : ''
                , 'gid' : ''
            }
        }
        , mounted: function() {
            $("#datetime1").datetimepicker({
                format: 'YYYY-MM-DD hh:mm:ss'
            }).on('dp.change', function(event) {
                evt = new Event('input', {"bubbles": true})
                this.childNodes[0].dispatchEvent(evt)
            })
            app = this
            // Load groups
            axios.get('/v1/star/group').then(function(response){
                console.log(response)
                if(response.data.code == 0) {
                    app.group_set = response.data.data
                }
            })
        }
        , updated: function() {
            $('#group_select').selectpicker('refresh')
        }
        , methods: {
            select: function(event) {
                new_selected = event.target.attributes['nav_item_id'].value
                this.bar_items[this.current_selected].class = 'nav_item item_normal'
                this.bar_items[new_selected].class = 'nav_item item_selected'
                this.current_selected = new_selected
                this.$emit('nav_select_change')
            }
            , loginSubmit: function (event) {
                vue_app = this
                axios.post('/sso/login',
                        'username=' + this.login.username
                        +'&password=' + this.login.password
                ).then(function(response) {
                    if(response.data.code == 0 && response.status == 200) {
                        href_base = window.location.protocol + '//' + window.location.host + '/'
                        document.location = window.location.protocol + '//'  + window.location.host + '/sso/login?appid=1&redirectURL=' + href_base
                    } else {
                        vue_app.login_err_msg = '认证错误 [' + response.data.code + ']: ' + response.data.msg;
                        vue_app.show_login_err = true
                    }
                }).catch(function(response){
                    if(response.response.data.code == 1201 && response.response.status == 403){
                        vue_app.login_err_msg = '认证失败：' + response.response.data.code;
                        vue_app.show_login_err = true
                    }
                })
            }
            , clearRegister: function(event) {
                for(key in this.register) {
                    if(key != 'sex') {
                        this.register[key] = ''
                    }
                }
            }
            , registerUser: function(event) {
                show_error = function(msg) {
                    app.control.reg_err_box_style = 'error'
                    app.control.show_reg_err = true
                    app.control.reg_err_msg = msg
                }
                app = this

                if(app.register.password != app.register.password_confrim) {
                    show_error('输入密码不匹配')
                    return
                }

                var args = new Array()
                for(key in this.register) {
                    if(key == 'password_confrim') {
                        continue
                    }
                    if(key == 'username') {
                        args.push('name=' + this.register[key])
                    }
                    args.push(key + '=' + this.register[key])
                }
                app.control.reg_err_box_style = 'info'
                app.control.show_reg_err = true

                axios.post('/v1/star/member', args.join('&')).then(function(response) {
                    if(response.data.code == 0 && response.status == 200) {
                        app.control.reg_err_box_style = 'success'
                        app.control.reg_err_msg = '注册成功'
                        app.control.show_reg_err = true
                    } else {
                        msg = '注册失败 [' + response.data.code + ']: ' + response.data.msg
                        show_error(msg)
                    }
                }).catch(function(response){
                    msg = '注册失败 [' + response.response.data.code + ']: ' + response.response.data.msg
                    show_error(msg)
                })
            }
        }
    })

}

document.addEventListener("DOMContentLoaded", vue_bind)
