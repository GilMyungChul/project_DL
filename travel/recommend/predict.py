import numpy as np
import tensorflow as tf

MODEL_PATH = "travel/recommend/saved_model.h5"

# 1. 서버 시작 시 모델 로딩
model = tf.keras.models.load_model(MODEL_PATH)


def make_feature(user_vec, place_vec):
    u = np.array(user_vec, dtype=np.float32)
    p = np.array(place_vec, dtype=np.float32)

    abs_diff = np.abs(u - p)
    prod = u * p

    return np.concatenate([u, p, abs_diff, prod]).reshape(1, -1)


def predict_score(user_vec, place_vec):
    x = make_feature(user_vec, place_vec)
    pred = model.predict(x)[0][0]   # 0~1 값
    return float(pred)