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
        }
        , methods: {
            select: function(event) {
                new_selected = event.target.attributes['nav_item_id'].value
                this.bar_items[this.current_selected].class = 'nav_item item_normal'
                this.bar_items[new_selected].class = 'nav_item item_selected'
                this.current_selected = new_selected
                this.$emit('nav_select_change')
            }
        }
    })
    $("#datetime1").datetimepicker({
        format: 'YYYY-MM-DD hh:mm:ss'
    });
}

document.addEventListener("DOMContentLoaded", vue_bind)
