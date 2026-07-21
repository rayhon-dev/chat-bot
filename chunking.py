# def chunk_text(text, chunk_size=500, overlap=50):
#     chunks = []
#     start = 0
#
#     while start < len(text):
#         end = start + chunk_size
#
#         if end < len(text):
#             while end > start and text[end] not in [" ", "\n"]:
#                 end -= 1
#
#         chunk = text[start:end]
#         chunks.append(chunk.strip())
#         start += chunk_size - overlap
#
#     return chunks
#
