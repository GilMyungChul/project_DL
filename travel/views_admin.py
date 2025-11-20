from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required

from .recommend.train import train_recommend_model


@staff_member_required   # 관리자만 접근 가능
def train_recommend_model_view(request):
    success = train_recommend_model(request)

    if success:
        return HttpResponse("추천 모델 학습 완료! saved_model.h5 업데이트됨")
    else:
        return HttpResponse("학습 실패. 로그를 확인하세요.")
