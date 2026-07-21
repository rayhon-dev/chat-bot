def calculate_chunk_params(text_length):
    if text_length <= 20_000:          # kichik hujjat (~5-10 sahifa)
        return {"chunk_size": 800, "overlap": 100, "top_k": 4}
    elif text_length <= 150_000:       # o'rta hujjat (~30-50 sahifa)
        return {"chunk_size": 1200, "overlap": 200, "top_k": 8}
    elif text_length <= 600_000:       # katta hujjat (~150-200 sahifa)
        return {"chunk_size": 1500, "overlap": 250, "top_k": 15}
    else:                               # juda katta (kitob darajasida)
        return {"chunk_size": 1800, "overlap": 300, "top_k": 25}