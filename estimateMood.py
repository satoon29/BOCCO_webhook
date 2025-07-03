def estimateMAX(emoji_list: list) -> int:
    """
    受け取った絵文字リストから、ユーザの感情状態を推定する
    最も感情価値が高い絵文字を選ぶ
    """
    if not emoji_list:
        return -1  # 絵文字リストが空の場合は-1を返す

    # 各絵文字の感情値と覚醒度を計算
    valence_scores = [valence_emoji(emoji) for emoji in emoji_list]
    arousal_scores = [arousal_emoji(emoji) for emoji in emoji_list]

    # Valenceの絶対値が最も大きいデータを選択
    max_valence = max(valence_scores, key=abs)

    # メッセージを選択
    if max_valence < -0.3:
        return 0 # ネガティブな感情
    elif max_valence > 0.3:
        return 1 # ポジティブな感情
    else:
        return 2 # ニュートラルな感情

def estimateAVG(emoji_list: list) -> int:
    """
    受け取った絵文字リストから、ユーザの感情状態を推定する
    感情価値の平均値を計算する
    """
    if not emoji_list:
        return -1  # 絵文字リストが空の場合は-1を返す

    # 各絵文字の感情値と覚醒度を計算
    valence_scores = [valence_emoji(emoji) for emoji in emoji_list]

    # Valenceの平均値を計算
    avg_valence = sum(valence_scores) / len(valence_scores)

    # メッセージを選択
    if avg_valence < -0.3:
        return 0 # ネガティブな感情
    elif avg_valence > 0.3:
        return 1 # ポジティブな感情
    else:
        return 2 # ニュートラルな感情



def valence_emoji(emoji: str) -> float:
    # 元の値の範囲: 3.01〜7.75 を -1〜1 に正規化
    min_val, max_val = 3.01, 7.75
    if emoji == "😫":
        val = 3.01
    elif emoji == "😤":
        val = 3.02
    elif emoji == "😢":
        val = 3.56
    elif emoji == "😥":
        val = 3.48
    elif emoji == "😅":
        val = 4.26
    elif emoji == "🙄":
        val = 4.36
    elif emoji == "🧐":
        val = 5.20
    elif emoji == "😎":
        val = 5.62
    elif emoji == "😉":
        val = 6.54
    elif emoji == "😙":
        val = 6.58
    elif emoji == "😊":
        val = 7.75
    elif emoji == "😍":
        val = 7.69
    else:
        return 0.0
    # -1〜1に正規化
    return 2 * ((val - min_val) / (max_val - min_val)) - 1

def arousal_emoji(emoji: str) -> float:
    # 元の値の範囲: 5.04〜7.37 を -1〜1 に正規化
    min_val, max_val = 5.04, 7.37
    if emoji == "😫":
        val = 6.70
    elif emoji == "😤":
        val = 6.69
    elif emoji == "😢":
        val = 5.58
    elif emoji == "😥":
        val = 5.68
    elif emoji == "😅":
        val = 5.04
    elif emoji == "🙄":
        val = 5.13
    elif emoji == "🧐":
        val = 5.14
    elif emoji == "😎":
        val = 5.06
    elif emoji == "😉":
        val = 5.68
    elif emoji == "😙":
        val = 6.00
    elif emoji == "😊":
        val = 7.03
    elif emoji == "😍":
        val = 7.37
    else:
        return 0.0
    # -1〜1に正規化
    return 2 * ((val - min_val) / (max_val - min_val)) - 1