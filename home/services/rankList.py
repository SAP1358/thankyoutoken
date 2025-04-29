####################################################################
# 2024-12-25 VTI   move business of rankList from views.py
####################################################################

import json
from django.db.models import F, Q
from collections import Counter
from myprofile.models import UserTokens, ManagePosi, UserPraise
from django.db.models import OuterRef, Subquery, Value, ExpressionWrapper, Sum, fields
from django.db.models.functions import Coalesce

def get_active_tokens(model_class, today, order_by='-end_date'):
    """Helper function to get active tokens"""
    tokens = model_class.objects.filter(
        Q(start_date__lte=today) & Q(end_date__gte=today),
        is_active='Y'
    ).first()
    
    if not tokens:
        tokens = model_class.objects.filter(
            is_active='Y'
        ).order_by(order_by).first()
    
    return tokens

def get_user_tokens_base_query(token_ids, company_filters, exclude_ids=None):
    """Generate base query for user tokens"""
    return UserTokens.objects.filter(
        token_id__in=token_ids if isinstance(token_ids, (list, tuple)) else [token_ids],
        is_active='Y',
        **company_filters
    ).annotate(
        employee_id=F('user__employee_id'),
        employee_name=F('user__employee_name'),
        company_id=F('user__company_id'),
        company_name=F('user__company_name'),
        department_name=F('user__department_name'),
        position_id=F('user__position_id'),
        position_name=F('user__position_name'),
        user_image_yn=F('user__image_yn'),
        user_image=F('user__image'),
        recev_point=ExpressionWrapper(F('received_tokens') * 1, output_field=fields.IntegerField()),
        send_point=ExpressionWrapper(F('my_send_tokens') * 1, output_field=fields.IntegerField())
    ).exclude(user_id__in=exclude_ids).values(
        'user_id', 'chg_date', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name','position_id','position_name', 'user_image_yn', 'user_image','recev_point', 'send_point'
    )

def get_user_praise_query(base_query, is_group=True):
    """Generate user praise query with annotations"""
    query = base_query

    if is_group:
        query = base_query.values('user_id', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name', 'position_id', 'position_name', 'user_image_yn', 'user_image')

    query = query.annotate(
        reward_skip_yn=Coalesce(
            Subquery(
                ManagePosi.objects.filter(
                    is_active="Y",
                    company_id=OuterRef('company_id'),
                    posi_id=OuterRef('position_id'),
                    reward_skip_yn__isnull=False
                ).values('reward_skip_yn')[:1]
            ), Value('N')
        ),
        tot_point=Sum(ExpressionWrapper(
            F('recev_point') + F('send_point'), 
            output_field=fields.IntegerField()
        ))
    ).exclude(
        reward_skip_yn='Y'
    ).filter(
        tot_point__gt=0
    )

    if is_group:
        return query.order_by('-tot_point').values(
            'user_id', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name', 'position_id', 'position_name', 'user_image_yn', 'user_image', 'tot_point', 'reward_skip_yn'
        )[:10]
    else:
        return query.order_by('-tot_point', 'chg_date').values(
            'user_id', 'chg_date', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name','position_id','position_name', 'user_image_yn', 'user_image', 'recev_point', 'send_point','tot_point', 'reward_skip_yn'
        )[:10]

def process_praise_tags(token_id, tag_filters):
    """Process and aggregate praise tags"""
    praise_tags = (UserPraise.objects
        .filter(is_active='Y', token_id=token_id, **tag_filters)
        .values('praise_id', 'tag'))
    
    tag_result = {}
    for praise in praise_tags:
        if not praise['tag']:
            continue
            
        try:
            tag_data = json.loads(praise['tag'].replace("'", "\"")) if isinstance(praise['tag'], str) else praise['tag']
            if not isinstance(tag_data.get('tag', []), list):
                continue
                
            praise_id = praise['praise_id']
            if praise_id not in tag_result:
                tag_result[praise_id] = []
            tag_result[praise_id].extend(tag_data['tag'])
        except (json.JSONDecodeError, AttributeError):
            continue
    
    return {
        praise_id: [tag for tag, _ in Counter(tags).most_common(3)]
        for praise_id, tags in tag_result.items()
    }

def get_group_mapping():
    """Return group mappings"""
    return {
        'A': ["20"],  # 우리은행
        'B': ["95", "E5", "B3", "B1"],  # 우리은행 등
        'C': ["D2", "E3", "E1", "C9", "E6"],  # 우리종합금융 등
        'D': ["C7", "E8", "D1", "C1", "E7"]  # 우리펀드서비스 등
    }