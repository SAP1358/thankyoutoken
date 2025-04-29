####################################################################
# 업무제목 : 땡큐토큰 models
# 프로그램 : models.py
# ------------------------------------------------------------------
# 2023-12-11 김대영 최초개발
# 2023-12-28 김대영 user 테이블에 org_username 컬럼추가 MigrationUser
# 2024-01-23 김대영 MigrationUser 테이블 추가
# 2024       윤준영 추가 및 개선
####################################################################
from django.db import models  
from django.contrib.auth.models import AbstractUser, UserManager as BaseUserManager
from django.db.models.signals import post_save  
from django.dispatch import receiver


class UserManager(BaseUserManager):
    def create_superuser(self, *args, **kwargs):
        return super().create_superuser(ty = '0', *args, **kwargs)
    
    # def create_user(self, *args, **kwargs):
    #     return super().create_user(type = '0', *args, **kwargs)


class ManageDept(models.Model):
    id = models.AutoField(primary_key=True)
    company_id = models.CharField(max_length=10)
    company_name = models.CharField(max_length=255, null=True)
    dept_id = models.CharField(max_length=10)
    dept_name = models.CharField(max_length=255, null=True)
    dept_level = models.CharField(max_length=2)
    parent_dept_id = models.CharField(max_length=10, null=True)
    peer_no = models.CharField(max_length=10, null=True)
    is_active = models.CharField(max_length=1, null=True)
    chg_date = models.DateTimeField(null=True)
    reg_date = models.DateTimeField(null=True)

    class Meta:
        db_table = 'account_manage_dept'
        
class ManagePosi(models.Model):
    id = models.AutoField(primary_key=True)
    company_id = models.CharField(max_length=10)
    company_name = models.CharField(max_length=255, null=True)
    posi_id = models.CharField(max_length=10)
    posi_name = models.CharField(max_length=255, null=True)
    reward_skip_yn = models.CharField(max_length=1, null=True)
    is_active = models.CharField(max_length=1, null=True)
    chg_date = models.DateTimeField(null=True)
    reg_date = models.DateTimeField(null=True)

    class Meta:
        db_table = 'account_manage_posi'
    
class User(AbstractUser):
    ty = models.IntegerField(null = True)
    birth_date = models.CharField(max_length=8)
    kor_name = models.CharField(max_length=150, null=True, blank=True)
    
    employee_id = models.CharField(max_length=18, null=True, blank=True)
    employee_name = models.CharField(max_length=50, null=True, blank=True)
    
    position_id = models.CharField(max_length=18, null=True, blank=True)
    position_name = models.CharField(max_length=50, null=True, blank=True)
    
    department_id = models.CharField(max_length=10, null=True, blank=True)
    department_name = models.CharField(max_length=50, null=True, blank=True)
    
    company_id = models.CharField(max_length=10, null=True, blank=True)
    company_name = models.CharField(max_length=50, null=True, blank=True)
    
    gender = models.CharField(max_length=1)
    image_yn = models.CharField(max_length=1, null=True, blank=True)
    image = models.CharField(max_length=255, null=True, blank=True)
    
    org_username = models.CharField(max_length=150, null=True, blank=True)
    
    chg_date = models.DateTimeField(blank=True, null=True)
    reg_date = models.DateTimeField(blank=True, null=True)
    addtoken_date = models.DateTimeField(blank=True, null=True)
    
    objects = UserManager()

    def __str__(self):
        return self.username
    
    class Meta:
        db_table = 'account_user_user'
    

######################################################################
# DB INSERT 2023-05-02
######################################################################

class UserImages(models.Model):
    id = models.AutoField(primary_key=True)
    card_code = models.CharField(max_length=10)
    card_name = models.CharField(max_length=50)
    card_message = models.CharField(max_length=255)
    image_path = models.TextField()
    is_open   = models.CharField(max_length=1, null=True, blank=True)
    is_active = models.CharField(max_length=1, null=True)
    chg_date  = models.DateTimeField(null=True)
    reg_date  = models.DateTimeField(null=True)

    class Meta:
        db_table = 'account_user_images'


class User3(models.Model):
    user_id = models.IntegerField(primary_key=True)
    # 다른 필드들

class Comment(models.Model):
    comment_id = models.IntegerField(primary_key=True)
    # 다른 필드들

class UserComment(models.Model):
    compliment = models.ForeignKey(User3, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    comment_content = models.TextField(blank=True, null=True)
    #user_id = models.IntegerField(unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_user_comm')
    employee_id = models.CharField(max_length=8, null=True, blank=True)
    is_active = models.CharField(max_length=1, blank=True, null=True)
    chg_date = models.DateTimeField(blank=True, null=True)
    reg_date = models.DateTimeField(blank=True, null=True)
    


    class Meta:
        db_table = 'account_user_comments'
        managed = False

class UserLike(models.Model):
    id = models.AutoField(primary_key=True)
    compliment_id = models.IntegerField(default=0)
    user_id = models.IntegerField(default=0)
    is_active = models.CharField(max_length=1, blank=True, null=True)
    chg_date = models.DateTimeField(blank=True, null=True)
    reg_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'account_user_likes'
#        unique_together = ('compliment_id', 'user_id')
        

class UserNotices(models.Model):
    notice_id = models.AutoField(primary_key=True)
    user_id = models.IntegerField(unique=True)    
    send = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='send_user_set', 
        db_column='send_id', 
        to_field='id', 
        verbose_name='발신자' 
    )  
    notice_type = models.CharField(max_length=1)
    compliment_id = models.IntegerField(blank=True, null=True)
    comment_id = models.IntegerField(blank=True, null=True)
    push_yn = models.CharField(max_length=1, blank=True, null=True)
    push_status = models.CharField(max_length=10, blank=True, null=True)
    check_yn = models.CharField(max_length=1, blank=True, null=True)
    is_active = models.CharField(max_length=1, blank=True, null=True)
    chg_date = models.DateTimeField(blank=True, null=True)
    reg_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'account_user_notices'


class ManageTokens(models.Model):
    id = models.AutoField(primary_key=True)
    year = models.CharField(max_length=4)
    quarter = models.CharField(max_length=2)
    tokens = models.IntegerField(default=0)
    high_tokens = models.IntegerField(default=0)
    start_date = models.CharField(max_length=8, null=True)
    end_date = models.CharField(max_length=8, null=True)
    is_active = models.CharField(max_length=1, null=True)
    chg_date = models.DateTimeField(null=True)
    reg_date = models.DateTimeField(null=True)
    director_tokens = models.IntegerField(default=0) # 본부장 100개

    class Meta:
        db_table = 'account_manage_tokens'
        
class ManageTokensGroup(models.Model):
    id = models.AutoField(primary_key=True)
    start_date = models.CharField(max_length=8, null=True, default=None)
    end_date = models.CharField(max_length=8, null=True, default=None)
    is_active = models.CharField(max_length=1, null=True, default=None)
    chg_date = models.DateTimeField(null=True, default=None)
    reg_date = models.DateTimeField(null=True, default=None)

    class Meta:
        db_table = 'account_manage_tokens_group'
        
class UserTokens(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    year = models.CharField(max_length=4)
    quarter = models.CharField(max_length=2)
    token_id = models.IntegerField(null=True, blank=True)
    
    my_tot_tokens = models.IntegerField(null=True, blank=True)
    my_current_tokens = models.IntegerField(null=True, blank=True)
    my_send_tokens = models.IntegerField(null=True, blank=True)
    received_tokens = models.IntegerField(null=True, blank=True)
    
    my_story_stcd = models.CharField(max_length=2)
    my_story_book = models.TextField()   
    my_story_date = models.DateTimeField(null=True)
    
    image_yn = models.CharField(max_length=1, null=True, blank=True)
    image = models.CharField(max_length=255, null=True, blank=True)
    
    is_active = models.CharField(max_length=1, null=True, blank=True)
    chg_date = models.DateTimeField(null=True, blank=True)
    reg_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'account_user_tokens'
        
        
class UserPraise(models.Model):
    compliment_id = models.AutoField(primary_key=True)
    praise = models.ForeignKey(User, on_delete=models.CASCADE, related_name='praise_user_set')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_user_set')
    compliment_type = models.CharField(max_length=1)
    content = models.TextField()
    images = models.ForeignKey(UserImages, on_delete=models.CASCADE, related_name='images_UserImages_set')

    short_content = models.TextField()     # open ai 응답
    org_content = models.TextField()       # open ai 응답
    tag = models.TextField()               # open ai 응답
    emotion_ratio = models.TextField()     # open ai 응답

    view_count  = models.IntegerField(null=True, blank=True)
    comment_count = models.IntegerField(null=True, blank=True)
    likes_count = models.IntegerField(null=True, blank=True)
    token       = models.ForeignKey(ManageTokens, on_delete=models.CASCADE, related_name='token_set')
    
    is_open     = models.CharField(max_length=1, null=True, blank=True)
    is_active   = models.CharField(max_length=1, null=True, blank=True)
    chg_date    = models.DateTimeField(null=True, blank=True)
    reg_date    = models.DateTimeField(null=True, blank=True)

    todaythanks_date = models.DateTimeField(null=True, blank=True)
    todaythanks_showyn = models.CharField(max_length=1, null=True, blank=True)
    is_senduc = models.CharField(max_length=1, null=True, blank=True)

    class Meta:
        db_table = 'account_user_praise'
        


class AccessLog(models.Model):
    access_id = models.AutoField(primary_key=True)
    user_id = models.IntegerField(null=True, default=None)
    user_name = models.CharField(max_length=150, null=True, default=None)
    user_ip = models.CharField(max_length=50, null=True, default=None)
    user_agent = models.TextField(null=True, default=None)
    user_access_time = models.DateTimeField(null=True, default=None)
    requested_url = models.URLField(max_length=2000, null=True, default=None)

    class Meta:
        db_table = 'account_accesslog'


class MigrationUser(models.Model):
    id = models.AutoField(primary_key=True)
    srno = models.CharField(max_length=10, default=None, null=True)
    org_employee = models.CharField(max_length=10, default=None, null=True)
    new_employee = models.CharField(max_length=10, default=None, null=True)
    employee_name = models.CharField(max_length=100, default=None, null=True)
    company_name = models.CharField(max_length=100, default=None, null=True)
    is_active = models.CharField(max_length=1, default=None, null=True)
    chg_date = models.DateTimeField(null=True)
    reg_date = models.DateTimeField(null=True)

    class Meta:
        db_table = 'account_migration_user'

class ManageThankyouWeeks(models.Model):
    id = models.AutoField(primary_key=True)
    weeks_ym = models.CharField(max_length=6)
    start_date = models.CharField(max_length=8, null=True, default=None)
    end_date = models.CharField(max_length=8, null=True, default=None)
    is_active = models.CharField(max_length=1, null=True, default=None)
    chg_date = models.DateTimeField(null=True, default=None)
    reg_date = models.DateTimeField(null=True, default=None)

    class Meta:
        db_table = 'account_manage_thankyou_weeks'


class BefInsUcmsg(models.Model):
    id = models.AutoField(primary_key=True)
    send_company = models.CharField(max_length=50)
    send_department = models.CharField(max_length=50)
    send_username = models.CharField(max_length=20)
    send_empname = models.CharField(max_length=50)
    recv_company = models.CharField(max_length=50)
    recv_department = models.CharField(max_length=50)
    recv_username = models.CharField(max_length=20)
    recv_empname = models.CharField(max_length=50)
    send_time = models.DateTimeField()
    send_content = models.TextField()
    insert_yn = models.CharField(max_length=1, default=None, null=True)
    insert_time = models.DateTimeField()
    insertfail_reason = models.CharField(max_length=100)
    reg_date = models.DateTimeField()
    images_id = models.CharField(max_length=11)

    class Meta:
        db_table = 'account_user_befinsucmsg'