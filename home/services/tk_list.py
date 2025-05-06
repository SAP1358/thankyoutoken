####################################################################
# 2024-12-25 VTI   move business of tk_list from views.py
# 2025-04-23 VTI   add limit, offset in api get data tk_list
####################################################################

from datetime import datetime
from functools import lru_cache
from django.db import connection
from django.db.models import F, Q, OuterRef, Subquery, Count, When, Case
from myprofile.models import BefInsUcmsg, User, UserPraise, UserNotices, UserTokens, UserImages, ManagePosi, ManageTokens


def get_unprocessed_messages(username, one_month_ago):
    """Get unprocessed messages from the last month"""
    return BefInsUcmsg.objects.filter(
        Q(send_username=username) | Q(recv_username=username),
        insert_yn='N',
        send_time__gte=one_month_ago
    )

def get_users_from_message(message):
    """Get sender and receiver user objects and validate their existence"""
    receiver = User.objects.filter(username=message.recv_username).first()
    sender = User.objects.filter(username=message.send_username).first()
    
    if not (receiver and sender):
        raise ValueError("Sender or receiver not found")
        
    return sender, receiver

def get_user_reward_skip_status(user):
    """Check if user is eligible for reward skip"""
    user_reward = ManagePosi.objects.filter(
        is_active='Y',
        company_id=user.company_id,
        posi_id=user.position_id
    ).first()
    
    return "Y" if user_reward and user_reward.reward_skip_yn == "Y" else "N"

def create_user_praise(message, send_user, recv_user, token_info):
    """Create UserPraise record from UC message"""
    praise = UserPraise()
    praise.praise_id = recv_user.id  # 칭찬 받는 직원
    praise.user_id = send_user.id    # 칭찬한 직원
    praise.compliment_type = '1'
    
    # Handle images_id
    if message.images_id and message.images_id not in ['', 'null']:
        praise.images_id = message.images_id
    else:
        praise.images_id = '428'
    
    # Handle content
    if message.send_content and message.send_content not in ['', 'null', None]:
        content = message.send_content
    else:
        content = '감사합니다.'
    
    praise.content = content
    praise.org_content = content
    praise.short_content = content[:100]
    
    praise.tag = {'tag': ['감사','칭찬','UC']}
    praise.emotion_ratio = ''
    praise.view_count = 0
    praise.comment_count = 0
    praise.likes_count = 0
    praise.is_senduc = 'Y'
    praise.token_id = token_info.id
    praise.is_active = 'Y'
    praise.reg_date = message.send_time
    
    praise.save()
    return praise

def create_user_notice(praise_obj, send_user, recv_user):
    """Create notification for praise"""
    notice = UserNotices(
        user_id=recv_user.id,
        send_id=send_user.id,
        notice_type='1',
        compliment_id=praise_obj.compliment_id,
        comment_id=0,
        check_yn='N',
        push_yn='N',
        push_status='',
        is_active='Y',
        reg_date=datetime.now()
    )
    notice.save()
    return notice

def check_high_position_user(user_id):
    """Check if user is in high position (본부장 or 부행장)"""
    return User.objects.filter(
        Q(position_name__contains='본부장') | Q(position_name__contains='부행장'),
        ~Q(id=5256),
        id=user_id,
        company_id=20    
    ).exists()

def get_token_allocation(user, token_info, user_reward_skip_yn):
    """Determine token allocation based on user position and status"""
    if user.id == 15893:  # 회장님
        return 100
        
    if check_high_position_user(user.id):
        return 100
        
    if user_reward_skip_yn == "Y":
        return token_info.high_tokens
        
    return token_info.tokens

def process_user_tokens(user, token_info, is_sender, same_total_count=0):
    """Process token updates for user"""
    user_tokens = UserTokens.objects.filter(
        user_id=user.id,
        token_id=token_info.id,
        is_active='Y'
    ).first()
    
    user_reward_skip_yn = get_user_reward_skip_status(user)
    
    if user_tokens:
        if same_total_count == 1:
            if is_sender:
                user_tokens.my_send_tokens += 1
            else:
                user_tokens.received_tokens += 1
        user_tokens.chg_date = datetime.now()
        user_tokens.save()
    else:
        new_tokens = UserTokens(
            user_id=user.id,
            token_id=token_info.id,
            year=token_info.year,
            quarter=token_info.quarter
        )
        
        # Calculate my_tot_tokens based on user status
        my_tot_tokens = get_token_allocation(user, token_info, user_reward_skip_yn)
        new_tokens.my_tot_tokens = my_tot_tokens
        new_tokens.my_current_tokens = my_tot_tokens
        
        # Set tokens based on role and same_total_count
        if is_sender:
            new_tokens.my_send_tokens = 1 if same_total_count == 1 else 0
            new_tokens.received_tokens = 0
        else:
            new_tokens.my_send_tokens = 0
            new_tokens.received_tokens = 1 if same_total_count == 1 else 0
            
        new_tokens.is_active = 'Y'
        new_tokens.reg_date = datetime.now()
        new_tokens.save()

def process_single_message(message):
    """Process a single UC message"""
    send_user, recv_user = get_users_from_message(message)
    
    # Get token information
    msg_date = message.send_time.strftime('%Y%m%d')
    token_info = ManageTokens.objects.filter(
        Q(start_date__lte=msg_date) & Q(end_date__gte=msg_date)
    ).first()
    
    if not token_info:
        raise ValueError("Token information not found for the given date")
    
    # Create praise record
    praise = create_user_praise(message, send_user, recv_user, token_info)
    
    # Create notification
    create_user_notice(praise, send_user, recv_user)
    
    # Check total count for same user pair
    same_total_count = UserPraise.objects.filter(
        is_active='Y',
        token_id=token_info.id,
        user_id=send_user.id,
        praise_id=recv_user.id
    ).count()
    
    # Process tokens for both users
    process_user_tokens(send_user, token_info, True, same_total_count)
    process_user_tokens(recv_user, token_info, False, same_total_count)
    
    # Update UC message status
    message.insert_yn = 'Y'
    message.insert_time = datetime.now()
    message.insertfail_reason = ''
    message.save()


@lru_cache(maxsize=128)
def get_notice_count_subquery(user_id):
    """
    Returns a subquery for counting unread notices for a user.
    Uses caching to improve performance for repeated calls.
    """
    return UserNotices.objects.filter(
        user_id=user_id,
        send_id=OuterRef('user_id'),
        check_yn='N'
    ).values('user_id').annotate(
        notice_count=Count('notice_id')
    ).values('notice_count')[:1]


def select_my_list(user_id):
    """
    Retrieves compliment IDs for a given user based on their interactions.
    Different query logic for:
    - user_id 15893: Gets data from last 2 months using MAX(compliment_id)
    - other users: Gets most recent compliment_id using ROW_NUMBER()
    """
    if user_id == 15893:
        # Special case for user 15893: Get data from last 2 months
        # CREATE INDEX idx_praise_date ON wbntt.account_user_praise (reg_date, user_id, praise_id, compliment_id);
        query = """
            SELECT t1.list_id, MAX(t1.compliment_id) AS compliment_id
            FROM (
                SELECT compliment_id, user_id AS list_id, reg_date
                FROM wbntt.account_user_praise
                WHERE praise_id = %s AND is_active = 'Y' 
                    AND reg_date >= DATE_SUB(NOW(), INTERVAL 2 MONTH)
                UNION ALL
                SELECT compliment_id, praise_id AS list_id, reg_date
                FROM wbntt.account_user_praise
                WHERE user_id = %s AND is_active = 'Y'
                    AND reg_date >= DATE_SUB(NOW(), INTERVAL 2 MONTH)
            ) AS t1
            GROUP BY t1.list_id
        """
    else:
        # Normal case: Get most recent compliment for each list_id
        # CREATE INDEX idx_praise_composite ON wbntt.account_user_praise (is_active, praise_id, reg_date, compliment_id, user_id);
        query = """
            SELECT list_id, compliment_id
            FROM (
                SELECT list_id,
                    compliment_id,
                    ROW_NUMBER() OVER(PARTITION BY list_id ORDER BY reg_date DESC) AS rn
                FROM (
                    SELECT user_id AS list_id, 
                        compliment_id, 
                        reg_date
                    FROM wbntt.account_user_praise
                    WHERE praise_id = %s AND is_active = 'Y' 
                    UNION ALL
                    SELECT praise_id AS list_id, 
                        compliment_id, 
                        reg_date
                    FROM wbntt.account_user_praise
                    WHERE user_id = %s AND is_active = 'Y' 
                ) AS t1
            ) AS t2
            WHERE rn = 1
        """

    with connection.cursor() as cursor:
        cursor.execute(query, [user_id, user_id])
        return [row[1] for row in cursor.fetchall()]


def get_user_praise_queryset(compliment_ids, user_id, limit, offset):
    # ===================
    # 2025-01-05 add limit, offset in api get data tk_list
    # ===================

    """
    Returns an optimized queryset for user praise data with conditional field swapping.
    """
    if not compliment_ids:
        return UserPraise.objects.none()
    
    # Define fields to swap
    swap_fields = {
        'employee_name': ('praise__employee_name', 'user__employee_name'),
        'employee_id': ('praise__employee_id', 'user__employee_id'),
        'department_name': ('praise__department_name', 'user__department_name'),
        'position_name': ('praise__position_name', 'user__position_name'),
        'company_name': ('praise__company_name', 'user__company_name'),
        'image_yn': ('praise__image_yn', 'user__image_yn'),
        'image': ('praise__image', 'user__image'),
    }

    # Build annotations dictionary
    annotations = {}
    for field, (praise_field, user_field) in swap_fields.items():
        # For praise fields
        annotations[f'praise_{field}'] = Case(
            When(user_id=user_id, then=F(user_field)),
            default=F(praise_field)
        )
        # For user fields
        annotations[f'user_{field}'] = Case(
            When(user_id=user_id, then=F(praise_field)),
            default=F(user_field)
        )

    # Add other annotations
    annotations['temp_praise_id'] = Case(
        When(user_id=user_id, then=F('user_id')),
        default=F('praise_id')
    )

    annotations['temp_user_id'] = Case(
        When(user_id=user_id, then=F('praise_id')),
        default=F('user_id')
    )

    annotations.update({
        'image_path': F('images__image_path'),
        'notice_count': Subquery(get_notice_count_subquery(user_id))
    })

    return (UserPraise.objects
        .filter(compliment_id__in=compliment_ids)
        .select_related('praise', 'user')
        .prefetch_related('images')
        .annotate(**annotations)
        .order_by('-reg_date')[offset:offset+limit]
    )


def get_user_images():
    """
    Returns queryset for user images.
    """
    return (UserImages.objects
        .filter(is_open='Y', is_active='Y')
        .order_by('-reg_date')
    )