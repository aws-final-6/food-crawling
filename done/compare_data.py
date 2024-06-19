import pandas as pd

# 데이터 파일 로드 (cp949 인코딩 사용)
recent_ingredient_df = pd.read_csv('./recent9737_division_ingredient.csv', encoding='cp949')
recipe_cat_ids_df = pd.read_csv('./recipe_cat_ids.csv', encoding='cp949')

# 'recipe_id' 열 이름을 'RecipeID'로 변경
recent_ingredient_df = recent_ingredient_df.rename(columns={'recipe_id': 'RecipeID'})

# RecipeID 열을 기준으로 inner join을 수행하여 공통으로 존재하는 데이터만 남기고, recipe_cat_ids 데이터 병합
merged_df = pd.merge(recent_ingredient_df, recipe_cat_ids_df, on='RecipeID', how='inner')

# 병합된 데이터를 CSV 파일로 저장 (utf-8-sig 인코딩 지정)
merged_df.to_csv('Recipe_data.csv', index=False, encoding='utf-8-sig')

print("병합된 데이터가 'Recipe_data.csv' 파일로 저장되었습니다.")