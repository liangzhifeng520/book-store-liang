"""通用功能的文件（就是所有应用都拥有的功能）"""
from django.contrib.auth.decorators import login_required


class LoginRequiredMixin(object):
    @classmethod  #自己定义的类方法
    def as_view(cls, **initkwargs):
        #调用父类的as_view，判断是否登录了
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)  #继承原来的as_view()方法
        return login_required(view)