import pandas as pd
import ast
import json
import re

def safe_literal_eval(val):
    try:
        return ast.literal_eval(val)
    except (ValueError, SyntaxError):
        return val

def safe_json_loads(val):
    try:
        return json.loads(val.replace("'", "\""))
    except (ValueError, SyntaxError):
        return val

def process_instructions(val):
    if pd.notna(val):
        steps = safe_json_loads(val)
        if isinstance(steps, list):
            return [(step.get("text", ""), step.get("image", "")) for step in steps if isinstance(step, dict)]
    return []

def split_ingredient(ingredient):
    match = re.match(r"(.+?)\s+(\d+.*)", ingredient)
    if match:
        return match.groups()
    return ingredient, ""

def preprocess_chunk(chunk):
    # 필요한 데이터만 남기기
    required_columns = ["recipe_id", "name", "image", "author", "datePublished", "description", "recipeIngredient", "recipeInstructions", "tags"]
    chunk = chunk[required_columns]

    # author 필드에서 이름만 추출
    chunk.loc[:, "author"] = chunk["author"].apply(lambda x: safe_json_loads(x)["name"] if pd.notna(x) else "")

    # image 필드를 리스트 형식으로 변환
    chunk.loc[:, "image"] = chunk["image"].apply(lambda x: safe_literal_eval(x) if pd.notna(x) else [])

    # recipeIngredient 필드를 리스트 형식으로 변환 및 재료 이름과 계량으로 분리
    chunk.loc[:, "recipeIngredient"] = chunk["recipeIngredient"].apply(lambda x: [split_ingredient(i) for i in safe_literal_eval(x)] if pd.notna(x) else [])

    # recipeInstructions 필드를 리스트 형식으로 변환
    chunk.loc[:, "recipeInstructions"] = chunk["recipeInstructions"].apply(process_instructions)

    # tags 필드를 리스트 형식으로 변환
    chunk.loc[:, "tags"] = chunk["tags"].apply(lambda x: safe_literal_eval(x) if pd.notna(x) else [])

    return chunk

def preprocess_recipe_data(input_file, output_file, rows_to_process=None):
    # 데이터 읽기
    df = pd.read_csv(input_file, nrows=rows_to_process)

    # 데이터 전처리
    processed_df = preprocess_chunk(df)

    # 결과를 CSV 파일로 저장
    processed_df.to_csv(output_file, index=False, encoding='utf-8-sig')

# 함수 호출 예제
input_file = "./recipes.csv"  # 업로드한 파일 경로
output_file = "./example_prepro.csv"
preprocess_recipe_data(input_file, output_file, rows_to_process=9738)

# 결과를 확인하기 위해 저장된 파일을 다시 읽어옵니다.
processed_df = pd.read_csv(output_file)
processed_df.head()