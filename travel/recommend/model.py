import tensorflow as tf
from tensorflow.keras import layers, models


def create_recommend_model(input_dim=100):
    """
    추천 모델 (MLP) 생성 함수
    input_dim: 입력 벡터 크기 (예: user_vec + place_vec + abs_diff + prod = 100)
    """

    model = models.Sequential([
        layers.Input(shape=(input_dim,)),

        # 첫 번째 Dense 레이어
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.2),

        # 두 번째 Dense
        layers.Dense(64, activation='relu'),
        layers.Dropout(0.2),

        # 세 번째 Dense
        layers.Dense(32, activation='relu'),

        # 출력: 0~1 추천 점수
        layers.Dense(1, activation='sigmoid')
    ])

    # 모델 compile
    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',
        metrics=['accuracy']
    )

    return model
