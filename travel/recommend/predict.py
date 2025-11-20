import numpy as np
import tensorflow as tf

# 서버 시작 시 모델 로딩
model = tf.keras.models.load_model("myapp/recommend/saved_model.h5")

def make_feature(user_vec, place_vec):
    user_vec = np.array(user_vec, dtype=np.float32)
    place_vec = np.array(place_vec, dtype=np.float32)

    abs_diff = np.abs(user_vec - place_vec)
    prod = user_vec * place_vec

    x = np.concatenate([
        user_vec, place_vec, abs_diff, prod
    ])

    return x.reshape(1, -1)   # shape: (1, 100)

def predict_score(user_vec, place_vec):
    x = make_feature(user_vec, place_vec)
    score = model.predict(x)[0][0]
    return float(score)  # Python float