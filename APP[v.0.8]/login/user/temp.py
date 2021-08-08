####[RECIPE]####
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}
params = (
    ('app_id', 'b173452a'),
    ('app_key', '470fb694269e42dc1e038ce448a6a345'),
)
data = '{ "ingr": ["2 apples"] }'
r = requests.post('https://api.edamam.com/api/nutrition-details', headers=headers, params=params, data=data).json()




####[DETAILS]####
headers = {
    'Accept': 'application/json',
}
params = (
    ('app_id', 'b173452a'),
    ('app_key', '470fb694269e42dc1e038ce448a6a345'),
    ('nutrition-type', 'cooking'),
    ('ingr', '1 big apple'),
)
response = requests.get('https://api.edamam.com/api/nutrition-data', headers=headers, params=params)