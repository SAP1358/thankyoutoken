from django.contrib import admin  
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin  
from django.contrib.auth import get_user_model
# from django.contrib.auth.models import User


from .models import UserTokens, UserPraise, UserNotices, UserComment, UserLike

User = get_user_model()

class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('추가 정보', {'fields': ('ty','birth_date','gender',),},),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('추가 정보', {
            'fields': ('ty','birth_date','gender',),
        },),
    )
    

# Register your models here.

# class ProfileInline(admin.StackedInline):  
#     model = Profile
#     can_delete = False
#     verbose_name_plural = 'profile'


# class UserAdmin(BaseUserAdmin):  
#     inlines = (ProfileInline, )


admin.site.register(User, UserAdmin)

admin.site.register(UserTokens)
admin.site.register(UserPraise)
admin.site.register(UserNotices)
admin.site.register(UserComment)
admin.site.register(UserLike)

