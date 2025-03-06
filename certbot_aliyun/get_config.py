import sys
import yaml

key = sys.argv[1]

with open("config.yaml") as f:
    data = yaml.safe_load(f)
    n = key.count('.')
    parts = key.split('.')
    res = None
    i = 0
    while i <= n:
        try:
            if not res:
                res = data[parts[i]]
            else:
                res = res[parts[i]]
        except (yaml.YAMLError, KeyError) as exc:
            print ("Error: key not found in YAML")
            res = None
        i = i + 1
    if res:
        print(res)
